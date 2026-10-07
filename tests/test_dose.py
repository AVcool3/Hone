"""DOSE adaptive elicitation: bank construction, inference, and selection."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from hone.risk_profile import dose as D
from hone.risk_profile.estimation import choice_probability, estimate
from hone.risk_profile.holt_laury import DEFAULT_SCALES, standard_menu
from hone.web.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def simulate(true_gamma, true_mu=0.10, n=8, seed=0):
    """A synthetic CRRA subject with Fechner noise answering adaptively."""
    rng = np.random.default_rng(seed)
    answers: list[D.DoseAnswer] = []
    for _ in range(n):
        qid, _ = D.next_question(answers)
        p = choice_probability([D.QUESTION_BANK[qid]], true_gamma, true_mu)[0]
        answers.append(D.DoseAnswer(qid, "A" if rng.random() < p else "B"))
    return answers


class TestQuestionBank:
    def test_covers_the_whole_tier_range(self):
        """A bank with gaps cannot separate the tiers it fails to reach."""
        cov = np.array(D.bank_coverage())
        finite = cov[np.isfinite(cov)]
        assert finite.min() <= -1.0
        assert finite.max() >= 4.0
        # no gap wider than a few tiers anywhere in the range people occupy
        inside = np.sort(finite[(finite >= -1.0) & (finite <= 4.0)])
        assert np.max(np.diff(inside)) < 0.5

    def test_no_dominated_questions(self):
        """A sure amount outside the gamble's range is not a question."""
        for d in D.QUESTION_BANK:
            if d.option_a.high == d.option_a.low:  # certainty equivalent
                sure = d.option_a.high
                assert d.option_b.low < sure < d.option_b.high

    def test_certainty_equivalent_inverts_the_utility(self):
        for gamma in (-0.5, 0.0, 0.999, 1.0, 1.5, 3.0):
            ce = D.certainty_equivalent(200.0, 20.0, gamma)
            assert 20.0 < ce < 200.0
        # more risk-averse means a lower certainty equivalent
        ces = [D.certainty_equivalent(200.0, 20.0, g) for g in (-1, 0, 1, 2, 4)]
        assert ces == sorted(ces, reverse=True)

    def test_bank_is_deterministic(self):
        assert [d.option_a.high for d in D.build_question_bank()] == [
            d.option_a.high for d in D.QUESTION_BANK
        ]

    def test_question_text_reads_as_english(self):
        a, b = D.question_text(D._certainty_equivalent(45.0, 200.0, 20.0, 1))
        assert a == "$45, guaranteed"
        assert "50% chance of $200" in b and "$20" in b


class TestLikelihood:
    def test_grid_table_matches_the_mle_likelihood(self):
        """The adaptive route and the classic menu must be one model.

        The table is vectorized for speed; if it ever drifts from
        choice_probability the two estimators are describing different
        people.
        """
        for qid in (0, 7, len(D.QUESTION_BANK) // 2, len(D.QUESTION_BANK) - 1):
            table = D._prob_a_table(D.QUESTION_BANK[qid])
            for gi in (0, 40, 80, 120):
                for mi in (0, 6, 12):
                    expected = choice_probability(
                        [D.QUESTION_BANK[qid]],
                        float(D.GAMMA_GRID[gi]),
                        float(D.MU_GRID[mi]),
                    )[0]
                    assert table[gi, mi] == pytest.approx(expected, rel=1e-9)


class TestPosterior:
    def test_prior_is_normalized_and_sits_where_the_literature_does(self):
        post = D.posterior([])
        assert post.grid.sum() == pytest.approx(1.0)
        # The grid truncates the normal asymmetrically (-1.5 is 1.3 sd below
        # the mean, +4.5 is 2.4 sd above), so the prior mean sits somewhat
        # higher than PRIOR_GAMMA_MEAN. It must still land in the mildly
        # risk-averse region and stay wide enough for data to move it.
        assert 0.5 < post.gamma_mean < 1.2
        assert post.gamma_sd > 1.0
        assert post.n_answers == 0

    def test_answers_narrow_the_posterior(self):
        wide = D.posterior([]).gamma_sd
        narrow = D.posterior(simulate(1.2, n=8)).gamma_sd
        assert narrow < wide * 0.75

    def test_credible_interval_brackets_the_mean(self):
        post = D.posterior(simulate(0.8, n=8))
        lo, hi = post.gamma_ci90
        assert lo < post.gamma_mean < hi

    def test_taking_every_sure_thing_reads_as_risk_averse(self):
        answers = []
        for _ in range(8):
            qid, _ = D.next_question(answers)
            answers.append(D.DoseAnswer(qid, "A"))
        assert D.posterior(answers).gamma_mean > 2.5

    def test_taking_every_gamble_reads_as_risk_seeking(self):
        answers = []
        for _ in range(8):
            qid, _ = D.next_question(answers)
            answers.append(D.DoseAnswer(qid, "B"))
        assert D.posterior(answers).gamma_mean < 0.0

    @pytest.mark.parametrize("true_gamma", [-0.5, 0.3, 1.2, 2.5])
    def test_recovers_the_true_parameter(self, true_gamma):
        errors = [
            D.summarize(simulate(true_gamma, seed=s)).gamma - true_gamma
            for s in range(12)
        ]
        assert abs(np.mean(errors)) < 0.35
        assert np.sqrt(np.mean(np.square(errors))) < 0.5

    def test_beats_the_full_menu_where_the_menu_is_blind(self):
        """The Holt-Laury rows cannot discriminate above gamma ~ 1.5.

        Their indifference points top out there, so a highly risk-averse
        subject answers every row identically and the MLE is left guessing.
        Eight adaptive questions do not have that blind spot — which is the
        substantive reason for this module, beyond the shorter funnel.
        """
        true_gamma = 3.0
        dose_err, menu_err = [], []
        for seed in range(10):
            dose_err.append(
                D.summarize(simulate(true_gamma, seed=seed)).gamma - true_gamma
            )
            rng = np.random.default_rng(seed + 5000)
            choices = []
            for scale in DEFAULT_SCALES:
                menu = standard_menu(scale)
                p = choice_probability(menu, true_gamma, 0.10)
                choices.append(["A" if rng.random() < pi else "B" for pi in p])
            menu_err.append(estimate(choices).gamma - true_gamma)
        rmse = lambda e: float(np.sqrt(np.mean(np.square(e))))  # noqa: E731
        assert rmse(dose_err) < rmse(menu_err)


class TestSelection:
    def test_gain_is_in_bits_and_bounded(self):
        post = D.posterior([])
        gains = [
            D.expected_information_gain(post, q)
            for q in range(len(D.QUESTION_BANK))
        ]
        assert 0.0 <= min(gains)
        assert max(gains) <= 1.0  # one binary answer cannot carry more

    def test_a_dominated_question_is_worth_far_less_than_a_chosen_one(self):
        """$250 guaranteed beats both outcomes of a $200/$20 coin flip.

        Its information content is not exactly zero — someone who takes the
        gamble anyway reveals a large noise parameter, and mu is part of what
        is being estimated — but it says nothing about curvature, so it must
        score well below the question selection actually picks. This is why
        the bank filters such pairs out rather than spending a user's
        attention on one.
        """
        post = D.posterior([])
        dominated = D._certainty_equivalent(250.0, 200.0, 20.0, 999)
        table = D._prob_a_table(dominated)
        p_a = float(np.sum(post.grid * table))
        gain = float(D._binary_entropy(np.array(p_a))) - float(
            np.sum(post.grid * D._binary_entropy(table))
        )
        _, chosen_gain = D.next_question([])
        assert gain < chosen_gain

    def test_never_repeats_a_question(self):
        answers = []
        for _ in range(15):
            qid, _ = D.next_question(answers)
            assert qid not in {a.question_id for a in answers}
            answers.append(D.DoseAnswer(qid, "A"))

    def test_varies_the_gamble_rather_than_haggling(self):
        """Pure information-maximization nudges one sure amount repeatedly.

        That is tedious and reads like negotiation; the diversity rule
        should keep consecutive questions from reusing the same gamble.
        """
        answers = []
        gambles = []
        for _ in range(8):
            qid, _ = D.next_question(answers)
            gambles.append(D._gamble(qid))
            answers.append(D.DoseAnswer(qid, "A"))
        repeats = sum(1 for i in range(1, len(gambles)) if gambles[i] == gambles[i - 1])
        assert repeats <= 3
        assert len(set(gambles)) >= 3

    def test_information_gain_decreases_as_belief_sharpens(self):
        answers = simulate(1.0, n=6)
        first = D.expected_information_gain(D.posterior([]), answers[0].question_id)
        _, later = D.next_question(answers)
        assert later < first


class TestStopping:
    def test_stops_at_the_budget(self):
        post = D.posterior(simulate(1.0, n=8))
        assert D.is_finished(post, n_questions=8)
        assert not D.is_finished(D.posterior(simulate(1.0, n=5)), n_questions=8)

    def test_never_stops_on_an_early_tight_posterior(self):
        """Two answers cannot pin gamma down; that would be the prior talking."""
        post = D.posterior(simulate(1.0, n=2))
        post.gamma_sd = 0.001  # force the tight-posterior branch
        assert not D.is_finished(post, n_questions=8)


class TestDoseEndpoint:
    def test_first_call_returns_a_question_and_the_prior(self, client):
        res = client.post("/api/dose", json={"answers": []})
        assert res.status_code == 200
        body = res.json()
        assert body["finished"] is False
        q = body["question"]
        assert q["number"] == 1 and q["total"] == 8
        assert q["option_a"] and q["option_b"]
        assert q["expected_information_gain"] > 0
        st = body["state"]
        assert st["n_answers"] == 0
        assert len(st["gamma_grid"]) == len(st["gamma_marginal"])
        assert st["gamma_marginal"][0] >= 0

    def test_full_run_finishes_and_places_a_tier(self, client):
        answers = []
        for _ in range(12):
            body = client.post("/api/dose", json={"answers": answers}).json()
            if body["finished"]:
                break
            answers.append(
                {"question_id": body["question"]["question_id"], "choice": "A"}
            )
        assert body["finished"] is True
        assert body["question"] is None
        st = body["state"]
        assert st["n_answers"] == 8
        assert 1 <= st["tier"]["tier"] <= 50
        assert st["tier"]["num_tiers"] == 50
        assert st["gamma_ci90"][0] < st["gamma"] < st["gamma_ci90"][1]
        assert "credible" in st["summary"]

    def test_replaying_the_same_answers_is_exact(self, client):
        """Stateless: the posterior is a pure function of the answer list."""
        answers = [{"question_id": 3, "choice": "A"},
                   {"question_id": 11, "choice": "B"}]
        a = client.post("/api/dose", json={"answers": answers}).json()
        b = client.post("/api/dose", json={"answers": answers}).json()
        assert a == b

    def test_unknown_question_id_rejected(self, client):
        res = client.post(
            "/api/dose", json={"answers": [{"question_id": 99999, "choice": "A"}]}
        )
        assert res.status_code == 422

    def test_bad_choice_rejected(self, client):
        res = client.post(
            "/api/dose", json={"answers": [{"question_id": 1, "choice": "maybe"}]}
        )
        assert res.status_code == 422

    def test_question_budget_is_configurable(self, client):
        body = client.post("/api/dose", json={"answers": [], "n_questions": 5}).json()
        assert body["question"]["total"] == 5

    def test_answers_reference_the_server_bank(self, client):
        """A client cannot rewrite the experiment it is scored on.

        Answers carry an index, never payoffs, so the lotteries the
        posterior conditions on are always the ones the server served.
        """
        body = client.post("/api/dose", json={"answers": []}).json()
        assert set(body["question"]) >= {"question_id", "option_a", "option_b"}
        assert "payoffs" not in body["question"]
