"""QLoRA fine-tuning on a Hone conviction export.

    python training/train_qlora.py --data hone-training.jsonl --out ./adapter

Before you run this, read the number the export gave you.  If it said
``few_shot``, this script will happily train and hand you a model that is
worse than the one you started with — it will have memorized your thirty
examples and will apply them, confidently and in your own voice, to the
thirty-first.  The few-shot path in the app needs no GPU, works from about
five resolved predictions, and improves every time one resolves.  Come
back here when you have a few hundred.

What this is
------------
QLoRA (Dettmers et al., 2023): load the base model in 4-bit NF4, freeze
it, and train small low-rank adapters on top.  A 7-8B model fine-tunes on
a single 16GB GPU because the frozen weights are quantized and only the
adapters — a fraction of a percent of the parameters — carry gradients.

This trains a **local open-weights model**, not Claude.  Claude is not
fine-tunable through the public API, so the personalization that reaches
Claude is the in-context path in ``hone/llm/personalize.py``.  What you
get from this script is a small local compiler that has learned your
conventions and can run offline — a different, complementary thing.

Requirements (not installed by Hone; this is a GPU-only path):

    pip install torch transformers peft bitsandbytes trl datasets accelerate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: Small enough to train on one consumer GPU, capable enough for a
#: structured-extraction task. Anything larger stops being a thing a user
#: can actually run at home, which defeats the purpose.
DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

#: LoRA rank. Low on purpose: the task is narrow (learn one person's
#: phrasing conventions), and a high rank on a small dataset is just a
#: faster route to memorizing it.
DEFAULT_RANK = 8


def load_examples(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{i}: not valid JSON ({exc})")
        if "messages" not in row:
            raise SystemExit(f"{path}:{i}: expected a 'messages' key")
        rows.append(row)
    return rows


def chronological_split(rows: list[dict], holdout: float) -> tuple[list, list]:
    """Hold out the *last* slice, never a random one.

    A journal is a time series. A random split puts the same market
    regime on both sides, so validation loss flatters the model and tells
    you nothing about the only question that matters: does this help on
    the next thesis, which has not happened yet.
    """
    n_hold = max(1, int(len(rows) * holdout))
    return rows[: len(rows) - n_hold], rows[len(rows) - n_hold :]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, type=Path, help="JSONL from Hone")
    ap.add_argument("--out", default=Path("./hone-adapter"), type=Path)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--rank", type=int, default=DEFAULT_RANK)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--holdout", type=float, default=0.2)
    ap.add_argument("--max-seq-length", type=int, default=1024)
    ap.add_argument(
        "--force",
        action="store_true",
        help="train even when there is too little data to help",
    )
    args = ap.parse_args()

    rows = load_examples(args.data)
    print(f"{len(rows)} examples from {args.data}")

    if len(rows) < 200 and not args.force:
        print(
            f"\n{len(rows)} examples is well below the ~200 where fine-tuning\n"
            "starts to help. A LoRA trained on this will memorize these rows\n"
            "and do worse than the base model on your next thesis.\n\n"
            "Use the in-app few-shot personalization instead — no GPU, works\n"
            "from about five resolved predictions. Pass --force if you want\n"
            "to train anyway.",
            file=sys.stderr,
        )
        return 1

    train_rows, eval_rows = chronological_split(rows, args.holdout)
    print(f"train {len(train_rows)} / holdout {len(eval_rows)} (chronological)")

    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:
        print(
            f"\nMissing a training dependency ({exc.name}). This is a GPU-only\n"
            "path and Hone does not install it:\n\n"
            "  pip install torch transformers peft bitsandbytes trl datasets "
            "accelerate\n",
            file=sys.stderr,
        )
        return 1

    # 4-bit NF4 with double quantization — the memory trick that makes a
    # 7B model trainable on one consumer card. Compute stays in bf16 so
    # the adapter gradients are not quantization noise.
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, quantization_config=quant, device_map="auto"
    )

    peft_config = LoraConfig(
        r=args.rank,
        lora_alpha=args.rank * 2,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=Dataset.from_list(train_rows),
        eval_dataset=Dataset.from_list(eval_rows) if eval_rows else None,
        peft_config=peft_config,
        processing_class=tokenizer,
        args=SFTConfig(
            output_dir=str(args.out),
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=4,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            logging_steps=5,
            save_strategy="epoch",
            eval_strategy="epoch" if eval_rows else "no",
            bf16=True,
            max_length=args.max_seq_length,
            report_to=[],
        ),
    )
    trainer.train()
    trainer.save_model(str(args.out))
    print(f"\nAdapter written to {args.out}")
    print(
        "\nBefore you use it: compile ten theses with the base model and ten\n"
        "with the adapter and compare them yourself. A lower training loss is\n"
        "not evidence it helps — on a dataset this size it is mostly evidence\n"
        "of memorization."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
