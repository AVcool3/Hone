"""The earnings-call evidence behind the quote engine's sensitivities
(research/prediction/data/calls, findings/11) must stay well-formed:
every statement linked to its Quartr source, and every business and
weather risk named the way the engine names them."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("call_sensitivity", ROOT / "research/prediction/call_sensitivity.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_call_statement_is_sourced_and_named_correctly():
    cs = _module()
    df = cs.load()
    assert len(df) >= 150
    assert cs.problems(df) == []


def test_summary_covers_every_business():
    cs = _module()
    s = cs.summary(cs.load())
    from hone.prediction.quote import BUSINESSES
    assert set(s.business_key) == set(BUSINESSES)
    # every business has at least some call evidence
    assert (s.rows > 0).all()
