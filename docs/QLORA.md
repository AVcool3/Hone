# Tuning a model on your own convictions

## The ask, and the arithmetic

The ambition is real and it is a good one: a model tuned on *your*
convictions and how they actually turned out should compile your theses
the way you mean them and price your confidence the way your history
earns. Nobody else's data can teach it your habits.

The arithmetic is less romantic. A retail investor with a year of active
use has perhaps thirty resolved predictions. **Thirty examples is not a
fine-tuning dataset; it is a prompt.** A LoRA trained on thirty rows
memorizes them, and a model that has memorized your last thirty calls is
worse than the base model on the thirty-first — confidently, and in your
own voice, which is the worst possible failure mode for a tool whose job
is to check your reasoning.

So Hone ships two things and is explicit about which is which.

## What works today: in-context personalization

`hone/llm/personalize.py`. Your resolved predictions go into the
compiler's system prompt:

* **Style examples** — theses paired with the structured views you edited
  them into, and whether they hit. These teach the model the corrections
  you keep making: that you always mean six months by "medium term", that
  "I like it here" is 55% and not 75%.
* **A calibration note** — one sentence stating your realized hit rate
  against your average stated confidence. This is the sentence that stops
  the model repeating your overconfidence back at you.

Examples are **outcome-balanced**, not just recent: showing only hits
would teach the model you are always right, and showing only the last ten
hands it whatever streak you happen to be on.

No GPU. No training run. Active from **five** resolved predictions, and
better every time one resolves. It also degrades gracefully — a bad
example set makes the model slightly worse, where a bad fine-tune makes
it confidently and permanently worse.

The views page shows `tuned to your last N` when it is active.

## What needs more data: QLoRA

`hone/llm/export.py` builds two datasets from resolved predictions:

| Dataset | Input | Label | Teaches |
|---|---|---|---|
| `compile` | your thesis text | the structured view **you edited it into** | your conventions and the corrections you keep making |
| `calibrate` | thesis + the move it implies | **whether it actually hit** | what your language is worth, not what you claim for it |

The second label choice is the important one. Training on *stated*
confidence teaches a model to imitate your overconfidence. Training on
outcomes teaches it what your language actually predicts — the only
version worth having.

Only **resolved** predictions are used. An open prediction has no label,
and training on its stated confidence would teach the model your priors
rather than your accuracy.

The split is **chronological**, never random. A journal is a time series;
a random split puts the same market regime on both sides, so validation
loss flatters the model and answers nothing. The only question worth
asking is whether it helps on the *next* thesis.

### Running it

```bash
pip install torch transformers peft bitsandbytes trl datasets accelerate
python training/train_qlora.py --data hone-training.jsonl --out ./adapter
```

QLoRA (Dettmers et al., 2023): the base model loads in 4-bit NF4 with
double quantization and stays frozen; only small low-rank adapters train.
That is what puts a 7B model on a single 16GB card. Rank defaults to 8 —
low on purpose, because the task is narrow and a high rank on a small
dataset is a faster route to memorizing it.

The script **refuses to run** below 200 examples unless you pass
`--force`, and prints why.

### It does not tune Claude

Claude is not fine-tunable through the public API. The adapter this
produces is a **local open-weights model** that has learned your
conventions and can run offline — a different and complementary thing.
The personalization that reaches Claude is the in-context path above.

The app says this on the export panel, because the assumption otherwise
is natural and wrong.

## Verdicts the export gives you

| Examples | Verdict | What it means |
|---|---|---|
| < 200 | `few_shot` | Use the prompt path. Training will make things worse. |
| 200–500 | `marginal` | Enough to try, not to trust. Hold out the recent fifth and beat the base model or discard it. |
| > 500 | `ready` | Worth a small-rank LoRA. Still split chronologically. |

Degenerate label distributions are flagged separately: if 95% of your
predictions missed, the calibration half is nearly all zeros and a model
trained on it learns to answer "no" to everything — accurate, and
useless.

## Known limitations

* **The compile dataset has a selection problem.** It contains theses you
  acted on, not theses you considered and dropped. The model learns to
  compile the kind of idea you commit to.
* **Thirty rows will not become three hundred quickly.** At a realistic
  rate of a few views a month, `ready` is years away for most users. The
  export exists so the data is accumulating in the right shape from day
  one, not because anyone should train tomorrow.
* **No evaluation harness ships with this.** The script prints a
  reminder to compare adapter against base on held-out theses by hand.
  Automating that comparison — and defining what "better" means for a
  structured-extraction task — is not done.
* **The calibration dataset is binary.** Each row is one Bernoulli draw
  against a stated probability, which is an extremely weak signal per
  example. This is the same small-n problem the Brier calibration in
  `hone/journal/` has, and it does not go away by moving it into a model.

## References

* Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023).
  "QLoRA: Efficient Finetuning of Quantized LLMs." *NeurIPS 2023*.
* Hu, E. J., et al. (2021). "LoRA: Low-Rank Adaptation of Large Language
  Models." *ICLR 2022*.
* Brown, T., et al. (2020). "Language Models are Few-Shot Learners."
  *NeurIPS 2020* — the reason the prompt path works at n = 5.
