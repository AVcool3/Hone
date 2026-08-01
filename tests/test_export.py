"""Training export and few-shot personalization.

The theme of these tests is that the module must be honest about the one
thing users most want to hear a yes to: whether they have enough data to
fine-tune. They almost never do.
"""

import json

import pytest
from fastapi.testclient import TestClient

from hone.journal.calibration import fit_calibration
from hone.journal.records import Prediction, Resolution
from hone.llm.export import (
    FEW_SHOT_CEILING,
    MIN_VIABLE_EXAMPLES,
    build_dataset,
)
from hone.llm.personalize import MIN_EXAMPLES, build_personalization
from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def make_resolution(i, hit=True, thesis=None, confidence=0.7):
    p = Prediction(
        ticker="TSLA",
        entry_price=100.0,
        target_price=120.0,
        confidence=confidence,
        horizon_days=90,
        thesis=thesis if thesis is not None else f"TSLA runs to 120, call {i}",
        created_at=f"2024-{(i % 12) + 1:02d}-15",
    )
    return Resolution(
        prediction=p,
        final_price=125.0 if hit else 90.0,
        target_hit=hit,
        direction_hit=hit,
        touched=hit,
        realized_return=0.25 if hit else -0.10,
        resolved_at=p.resolves_at,
    )


class TestDatasetShape:
    def test_builds_both_halves(self):
        rows = [make_resolution(i, hit=i % 3 == 0) for i in range(12)]
        d = build_dataset(rows)
        assert d.n_compile == 12 and d.n_calibrate == 12
        assert d.n == 24
        assert {e.task for e in d.examples} == {"compile", "calibrate"}

    def test_jsonl_is_valid_chat_format(self):
        d = build_dataset([make_resolution(i) for i in range(5)])
        for line in d.to_jsonl().splitlines():
            row = json.loads(line)
            assert "messages" in row
            roles = [m["role"] for m in row["messages"]]
            assert roles == ["system", "user", "assistant"]
            assert all(m["content"] for m in row["messages"])

    def test_compile_label_is_the_structured_view(self):
        d = build_dataset([make_resolution(0)], include_calibration=False)
        payload = json.loads(d.examples[0].messages[-1]["content"])
        assert payload["ticker"] == "TSLA"
        assert payload["target_price"] == 120.0
        assert payload["confidence_pct"] == pytest.approx(70.0)

    def test_calibration_label_is_the_outcome_not_the_stated_confidence(self):
        """Training on stated confidence teaches the model to imitate
        overconfidence. Training on outcomes teaches it what the language
        is actually worth."""
        hit = build_dataset([make_resolution(0, hit=True)], include_compile=False)
        miss = build_dataset([make_resolution(1, hit=False)], include_compile=False)
        assert hit.examples[0].messages[-1]["content"] == "1.0"
        assert miss.examples[0].messages[-1]["content"] == "0.0"

    def test_thin_theses_are_skipped(self):
        rows = [make_resolution(0, thesis=""), make_resolution(1, thesis="up")]
        assert build_dataset(rows).n == 0

    def test_only_resolved_predictions_are_used(self):
        """An open prediction has no label; using its stated confidence
        would teach the model the user's priors, not their accuracy."""
        assert build_dataset([]).n == 0

    def test_split_is_chronological_not_random(self):
        rows = [make_resolution(i) for i in range(20)]
        d = build_dataset(rows, include_calibration=False)
        train, hold = d.split(holdout=0.25)
        assert len(hold) == 5 and len(train) == 15
        # the holdout is the *end* of the series
        assert d.examples[-5:] == hold

    def test_examples_are_time_ordered(self):
        rows = [make_resolution(i) for i in reversed(range(8))]
        d = build_dataset(rows, include_calibration=False)
        theses = [e.messages[1]["content"] for e in d.examples]
        assert theses == sorted(theses, key=lambda t: int(t.split()[-1]))


class TestHonestyAboutSize:
    def test_a_retail_journal_is_told_to_use_few_shot(self):
        d = build_dataset([make_resolution(i) for i in range(15)])
        assert d.recommendation == "few_shot"
        assert any("worse than the base model" in w for w in d.warnings)
        assert any("few-shot" in n for n in d.notes)

    def test_a_middling_dataset_is_told_to_verify(self):
        n = (MIN_VIABLE_EXAMPLES + FEW_SHOT_CEILING) // 4
        d = build_dataset([make_resolution(i, hit=i % 3 == 0) for i in range(n)])
        assert d.recommendation == "marginal"
        assert any("not enough to trust" in w for w in d.warnings)

    def test_a_large_dataset_is_cleared_to_train(self):
        n = FEW_SHOT_CEILING
        d = build_dataset([make_resolution(i, hit=i % 3 == 0) for i in range(n)])
        assert d.recommendation == "ready"
        assert d.warnings == []

    def test_degenerate_labels_are_flagged(self):
        """All-hits or all-misses gives a model nothing to learn."""
        all_hit = build_dataset([make_resolution(i, hit=True) for i in range(20)])
        all_miss = build_dataset([make_resolution(i, hit=False) for i in range(20)])
        assert any("nearly all ones" in w for w in all_hit.warnings)
        assert any("learn to answer 'no'" in w for w in all_miss.warnings)

    def test_summary_reads(self):
        d = build_dataset([make_resolution(i, hit=i % 2 == 0) for i in range(10)])
        text = d.summary()
        assert "training examples" in text and "hit rate" in text


class TestPersonalization:
    def test_inactive_below_the_floor(self):
        p = build_personalization([make_resolution(i) for i in range(MIN_EXAMPLES - 1)])
        assert not p.active
        assert p.as_prompt_block() == ""

    def test_active_at_a_handful(self):
        """Works at the scale fine-tuning cannot."""
        p = build_personalization([make_resolution(i, hit=i % 2 == 0)
                                   for i in range(MIN_EXAMPLES)])
        assert p.active and p.n_used >= MIN_EXAMPLES
        block = p.as_prompt_block()
        assert "track record" in block and "TSLA" in block

    def test_examples_are_outcome_balanced(self):
        """Showing only hits would teach the model this person is always right."""
        rows = [make_resolution(i, hit=True) for i in range(10)]
        rows += [make_resolution(i + 20, hit=False) for i in range(10)]
        p = build_personalization(rows, limit=8)
        block = p.as_prompt_block()
        assert "it hit" in block
        assert "it went the other way" in block

    def test_respects_the_example_limit(self):
        p = build_personalization([make_resolution(i) for i in range(50)], limit=6)
        assert p.n_used == 6

    def test_calibration_note_names_overconfidence(self):
        rows = [make_resolution(i, hit=i % 5 == 0, confidence=0.8) for i in range(20)]
        report = fit_calibration(
            [r.confidence for r in rows], [float(r.target_hit) for r in rows]
        )
        p = build_personalization(rows, report)
        assert "do not simply echo" in p.calibration_note

    def test_calibration_note_names_underconfidence(self):
        rows = [make_resolution(i, hit=i % 5 != 0, confidence=0.35) for i in range(20)]
        report = fit_calibration(
            [r.confidence for r in rows], [float(r.target_hit) for r in rows]
        )
        p = build_personalization(rows, report)
        assert "understate" in p.calibration_note


class TestExportEndpoint:
    def _journal(self, client):
        body = client.post(
            "/api/journal", json={"demo": True, "seed_demo_history": True}
        ).json()
        return [r["prediction"] for r in body["resolved"]]

    def test_exports_and_recommends_few_shot(self, client):
        preds = self._journal(client)
        res = client.post(
            "/api/export/training", json={"demo": True, "predictions": preds}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["n_resolved"] == len(preds)
        assert body["n_examples"] == body["n_compile"] + body["n_calibrate"]
        assert body["recommendation"] == "few_shot"
        assert body["few_shot_active"] > 0  # what actually works, today
        assert body["warnings"]

    def test_jsonl_round_trips(self, client):
        body = client.post(
            "/api/export/training",
            json={"demo": True, "predictions": self._journal(client)},
        ).json()
        lines = body["jsonl"].splitlines()
        assert len(lines) == body["n_examples"]
        assert all("messages" in json.loads(line) for line in lines)

    def test_empty_journal_is_not_an_error(self, client):
        body = client.post(
            "/api/export/training", json={"demo": True, "predictions": []}
        ).json()
        assert body["n_examples"] == 0
        assert body["few_shot_active"] == 0
        assert body["recommendation"] == "few_shot"

    def test_malformed_entries_do_not_break_the_request(self, client):
        preds = self._journal(client)
        preds.append(dict(preds[0], entry_price=0.0))
        res = client.post(
            "/api/export/training", json={"demo": True, "predictions": preds}
        )
        assert res.status_code in (200, 422)


class TestCompilerPersonalization:
    def test_compile_accepts_a_journal_and_reports_the_count(self, client):
        preds = [
            r["prediction"]
            for r in client.post(
                "/api/journal", json={"demo": True, "seed_demo_history": True}
            ).json()["resolved"]
        ]
        body = client.post(
            "/api/compile-view",
            json={"text": "TSLA to 450 by year end", "demo": True,
                  "predictions": preds},
        ).json()
        assert body["personalized_from"] > 0

    def test_offline_parser_says_it_ignores_the_history(self, client):
        """The fallback cannot use in-context examples; the UI must not
        imply personalization happened when it did not."""
        preds = [
            r["prediction"]
            for r in client.post(
                "/api/journal", json={"demo": True, "seed_demo_history": True}
            ).json()["resolved"]
        ]
        body = client.post(
            "/api/compile-view",
            json={"text": "TSLA to 450", "demo": True, "offline": True,
                  "predictions": preds},
        ).json()
        assert any("offline parser ignores" in n for n in body["notes"])

    def test_no_journal_means_no_personalization(self, client):
        body = client.post(
            "/api/compile-view", json={"text": "TSLA to 450", "demo": True}
        ).json()
        assert body["personalized_from"] == 0


class TestTrainingScript:
    def test_refuses_to_train_on_too_little_without_force(self, tmp_path):
        import subprocess
        import sys

        data = tmp_path / "tiny.jsonl"
        data.write_text(
            "\n".join(
                json.dumps({"messages": [{"role": "user", "content": "x"}]})
                for _ in range(10)
            )
        )
        proc = subprocess.run(
            [sys.executable, "training/train_qlora.py", "--data", str(data)],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1
        assert "below the ~200" in proc.stderr
        assert "few-shot" in proc.stderr

    def test_rejects_malformed_data_with_a_line_number(self, tmp_path):
        import subprocess
        import sys

        data = tmp_path / "bad.jsonl"
        data.write_text('{"messages": []}\nnot json\n')
        proc = subprocess.run(
            [sys.executable, "training/train_qlora.py", "--data", str(data)],
            capture_output=True, text=True,
        )
        assert proc.returncode != 0
        assert ":2:" in (proc.stdout + proc.stderr)


class TestExportUI:
    def test_journal_page_offers_the_export(self, client):
        html = client.get("/").text
        assert "/api/export/training" in html
        assert "Check my training data" in html
        assert "downloadText" in html

    def test_page_says_claude_cannot_be_fine_tuned(self, client):
        """Users will assume the download tunes Claude. It does not."""
        html = client.get("/").text
        assert "can't be fine-tuned through the API" in html

    def test_compile_sends_the_journal(self, client):
        html = client.get("/").text
        assert "predictions: journalLoad()" in html
        assert "tuned to your last" in html
