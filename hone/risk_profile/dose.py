"""DOSE: Dynamically Optimized Sequential Experimentation.

The Holt-Laury menu asks thirty questions to place one number.  Most of
them are wasted: once someone's first few answers put them near γ ≈ 2, the
rows that discriminate between γ = −0.5 and γ = 0 tell us nothing we did
not already know.  Chapman, Snowberg, Wang and Camerer (2018) formalized
the alternative — keep a Bayesian posterior over the parameters and, at
each step, ask the question whose answer is expected to be most
informative about it.  Their result: a handful of adaptive questions
recover preference parameters about as precisely as a full menu, and with
markedly better test-retest reliability, because subjects stop losing
attention.

Attention is the whole point here.  A thirty-question wall is the single
largest drop-off in Hone's funnel, and a risk parameter elicited from a
bored user is a worse number than one elicited from eight questions they
actually read.

Method
------
Posterior over a discrete grid in (γ, μ), where μ is the same Fechner
noise parameter the MLE engine estimates — a user's inconsistency is
information, not an error to be discarded.

* **Likelihood** is exactly :func:`~hone.risk_profile.estimation.choice_probability`
  under the contextual-Fechner specification, so the adaptive route and
  the classic menu are the same model of the same person.  A user can
  answer some of each and both update the same posterior.
* **Question selection** maximizes the mutual information between the
  unknown parameters and the answer:

      I(θ; y) = H(E_θ[Pr(A|θ)]) − E_θ[H(Pr(A|θ))]

  with H the binary entropy.  In words: prefer the question the current
  posterior is most *undecided* about (high first term) and which each
  individual parameter value answers *decisively* (low second term).  A
  question everyone answers the same way scores zero and is never asked.
* **Stopping** on a fixed count (default 8) or once the posterior
  standard deviation on γ is tight enough that another question would not
  change the tier.

The question bank spans the whole tier range, including the certainty-
equivalent questions ("$40 for sure, or a coin flip for $100?") that
carry nearly all the information about the highly risk-averse end where
the Holt-Laury rows are almost silent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .estimation import choice_probability
from .holt_laury import Decision, Lottery, indifference_gamma
from .tiers import gamma_to_tier

#: Grid over gamma. Spans the 50-tier range with margin on both ends so
#: the posterior is never truncated at a value someone could actually hold.
GAMMA_GRID = np.linspace(-1.5, 4.5, 121)

#: Grid over the Fechner noise parameter, log-spaced: the difference
#: between mu = 0.02 and mu = 0.05 matters far more than between 1.0 and 2.0.
MU_GRID = np.exp(np.linspace(np.log(0.02), np.log(1.5), 13))

#: Default number of adaptive questions.
DEFAULT_N_QUESTIONS = 8

#: Stop early once the posterior s.d. on gamma is this tight — at 0.05 the
#: 50-tier placement (0.10-wide bins) is settled and further questions are
#: asking the user to confirm something already known.
SD_STOP = 0.05

#: Prior on gamma. Centred on the mildly risk-averse region where the
#: experimental literature puts most people (Holt & Laury 2002 found the
#: modal subject "slightly to highly risk averse"), and wide enough that
#: the data can move it anywhere, including risk-seeking.
PRIOR_GAMMA_MEAN = 0.65
#: Deliberately wide. A tighter prior is slightly better in the middle and
#: much worse at the risk-averse extreme, where it drags the posterior mean
#: down by most of a point after only eight answers.
PRIOR_GAMMA_SD = 1.60

#: Prior on log-mu: most people are fairly consistent, some are not.
PRIOR_LOG_MU_MEAN = np.log(0.15)
PRIOR_LOG_MU_SD = 1.0


# ------------------------------------------------------------ question bank
def _pair(safe_high, safe_low, risky_high, risky_low, p, number, scale=1.0):
    return Decision(
        number=number,
        option_a=Lottery(safe_high, safe_low, p),
        option_b=Lottery(risky_high, risky_low, p),
        scale=scale,
    )


def _certainty_equivalent(sure: float, high: float, low: float, number: int):
    """A sure amount against a coin flip.

    Option A pays ``sure`` whichever way the coin lands, which is how it
    reads to the user.  These questions carry most of the information at
    the risk-averse end: the Holt-Laury rows all involve two lotteries and
    lose discriminating power once the safe option is not actually safe.
    """
    return Decision(
        number=number,
        option_a=Lottery(sure, sure, 0.5),
        option_b=Lottery(high, low, 0.5),
    )


def certainty_equivalent(high: float, low: float, gamma: float, p: float = 0.5) -> float:
    """The sure amount a CRRA agent with this gamma values the lottery at.

    Inverting U(S) = p·U(high) + (1−p)·U(low) has a closed form, which is
    what makes the bank constructible rather than searched: to get a
    question whose indifference point sits exactly at some gamma, offer
    that gamma's certainty equivalent as the sure amount.
    """
    if abs(gamma - 1.0) < 1e-9:  # log utility: the geometric mean
        return float(np.exp(p * np.log(high) + (1 - p) * np.log(low)))
    eu = p * high ** (1 - gamma) + (1 - p) * low ** (1 - gamma)
    return float(eu ** (1.0 / (1 - gamma)))


#: Gammas the bank is built to discriminate at. Denser through the middle,
#: where most people actually sit and where a tier boundary is therefore
#: most likely to be the one in question.
_TARGET_GAMMAS = np.concatenate([
    np.arange(-1.25, 0.0, 0.25),
    np.arange(0.0, 2.0, 0.15),
    np.arange(2.0, 4.6, 0.3),
])

#: Coin flips the sure amount is offered against. The spread matters: a
#: wide flip ($500 vs $5) is the only instrument with any power at the
#: risk-averse extreme, because that is where the downside dominates the
#: valuation; a narrow one ($120 vs $80) separates the near-neutral middle
#: that a wide flip answers identically for everyone.
_FLIPS = ((200.0, 20.0), (500.0, 5.0), (120.0, 80.0), (60.0, 6.0))


def _round_money(x: float) -> float:
    """Round to something a person would recognize as an offer."""
    if x >= 100:
        return round(x / 5) * 5.0
    if x >= 20:
        return round(x)
    if x >= 5:
        return round(x * 2) / 2.0
    return round(x, 2)


def build_question_bank() -> list[Decision]:
    """A deterministic bank of candidate questions tiling the gamma range.

    Built by construction rather than by taste: for each target gamma and
    each flip, the sure amount is that gamma's certainty equivalent, so
    the bank's indifference points cover the whole tier range by design.
    A bank with gaps cannot separate the tiers it fails to reach, however
    cleverly questions are then selected — which is exactly what a
    hand-picked bank of Holt-Laury rows gets wrong at the risk-averse end.

    Indexed by position, so a stateless API can round-trip an answer as
    ``(question_id, choice)`` without the client echoing payoffs back —
    which would let a client rewrite the experiment.
    """
    bank: list[Decision] = []
    seen: set[tuple] = set()
    n = 0

    for high, low in _FLIPS:
        for gamma in _TARGET_GAMMAS:
            sure = _round_money(certainty_equivalent(high, low, float(gamma)))
            # A sure amount outside the flip's own range is not a question:
            # one option dominates and every user answers it the same way.
            if not (low * 1.02 < sure < high * 0.98):
                continue
            key = (high, low, sure)
            if key in seen:
                continue
            seen.add(key)
            n += 1
            bank.append(_certainty_equivalent(sure, high, low, n))

    # A handful of classic Holt-Laury rows. They add little the certainty
    # equivalents do not, but two lotteries side by side is a different
    # cognitive task from a sure thing against a gamble, and disagreement
    # between the two formats is part of what identifies the noise
    # parameter rather than being mistaken for curvature.
    for p in (0.3, 0.4, 0.5, 0.6, 0.7):
        n += 1
        bank.append(_pair(100.0, 80.0, 192.50, 5.0, float(p), n))

    return bank


QUESTION_BANK: list[Decision] = build_question_bank()


def question_text(d: Decision) -> tuple[str, str]:
    """(option A text, option B text) as a person should read them."""

    def money(x: float) -> str:
        return f"${x:,.2f}".rstrip("0").rstrip(".") if x % 1 else f"${x:,.0f}"

    if d.option_a.high == d.option_a.low:
        a = f"{money(d.option_a.high)}, guaranteed"
    else:
        a = (
            f"{int(round(d.option_a.p_high * 100))}% chance of "
            f"{money(d.option_a.high)}, otherwise {money(d.option_a.low)}"
        )
    b = (
        f"{int(round(d.option_b.p_high * 100))}% chance of "
        f"{money(d.option_b.high)}, otherwise {money(d.option_b.low)}"
    )
    return a, b


# ------------------------------------------------------------------ posterior
def _log_prior() -> np.ndarray:
    """Log prior on the (gamma, mu) grid, normalized."""
    g = GAMMA_GRID[:, None]
    log_mu = np.log(MU_GRID)[None, :]
    lp = -0.5 * ((g - PRIOR_GAMMA_MEAN) / PRIOR_GAMMA_SD) ** 2
    lp = lp - 0.5 * ((log_mu - PRIOR_LOG_MU_MEAN) / PRIOR_LOG_MU_SD) ** 2
    lp = lp - lp.max()
    p = np.exp(lp)
    return np.log(p / p.sum())


def _crra_vec(x: float, gamma: np.ndarray) -> np.ndarray:
    """CRRA utility of one payoff across the gamma grid."""
    out = np.empty_like(gamma)
    log_case = np.abs(gamma - 1.0) < 1e-10
    out[log_case] = np.log(x)
    g = gamma[~log_case]
    out[~log_case] = x ** (1.0 - g) / (1.0 - g)
    return out


def _prob_a_table(decision: Decision) -> np.ndarray:
    """Pr(choose A | gamma, mu) over the whole grid for one question.

    Shape ``(len(GAMMA_GRID), len(MU_GRID))``.  This is the contextual
    Fechner specification of :func:`hone.risk_profile.estimation.choice_probability`
    evaluated over the grid at once — vectorized because the loop version
    costs a few seconds per bank, but held to agreement with the MLE's own
    implementation by a test, since the two estimators drifting apart
    would mean two different models of the same person.
    """
    g = GAMMA_GRID
    a, b = decision.option_a, decision.option_b
    eu_a = a.p_high * _crra_vec(a.high, g) + (1 - a.p_high) * _crra_vec(a.low, g)
    eu_b = b.p_high * _crra_vec(b.high, g) + (1 - b.p_high) * _crra_vec(b.low, g)
    payoffs = [a.high, a.low, b.high, b.low]
    nu = _crra_vec(max(payoffs), g) - _crra_vec(min(payoffs), g)
    nu = np.maximum(np.abs(nu), 1e-12)

    index = (eu_a - eu_b)[:, None] / (nu[:, None] * MU_GRID[None, :])
    prob = np.exp(-np.logaddexp(0.0, -index))
    return np.clip(prob, 1e-12, 1.0 - 1e-12)


class _BankCache:
    """Lazily computed Pr(A) tables, one per bank question.

    The tables depend only on the grids and the payoffs, so they are
    computed once per process and reused across every user.
    """

    def __init__(self) -> None:
        self._tables: dict[int, np.ndarray] = {}

    def get(self, qid: int) -> np.ndarray:
        if qid not in self._tables:
            self._tables[qid] = _prob_a_table(QUESTION_BANK[qid])
        return self._tables[qid]


_CACHE = _BankCache()


def _binary_entropy(p: np.ndarray) -> np.ndarray:
    """Binary entropy in bits — 1.0 for a coin flip, 0 for a certainty."""
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


@dataclass
class DoseAnswer:
    """One answered question: bank index and the option taken."""

    question_id: int
    choice: str  # "A" or "B"

    def __post_init__(self) -> None:
        self.choice = str(self.choice).strip().upper()
        if self.choice not in ("A", "B"):
            raise ValueError("choice must be 'A' or 'B'")
        if not 0 <= self.question_id < len(QUESTION_BANK):
            raise ValueError(f"unknown question id {self.question_id}")


@dataclass
class DosePosterior:
    """Posterior over (gamma, mu) and what it implies about the user."""

    grid: np.ndarray  # (n_gamma, n_mu) probabilities, sums to 1
    gamma_mean: float
    gamma_sd: float
    gamma_ci90: tuple[float, float]
    mu_mean: float
    n_answers: int
    #: Posterior probability mass on the modal tier — how sure the
    #: placement is, in the units the user is actually shown.
    tier_confidence: float = 0.0
    tier: int = 0

    @property
    def gamma_marginal(self) -> np.ndarray:
        return self.grid.sum(axis=1)


def posterior(answers: list[DoseAnswer]) -> DosePosterior:
    """Bayesian posterior over (gamma, mu) given the answers so far."""
    log_post = _log_prior()
    for a in answers:
        table = _CACHE.get(a.question_id)
        p = table if a.choice == "A" else (1.0 - table)
        log_post = log_post + np.log(np.clip(p, 1e-12, 1.0))
    log_post -= log_post.max()
    grid = np.exp(log_post)
    grid /= grid.sum()

    marg = grid.sum(axis=1)
    mean = float(np.sum(marg * GAMMA_GRID))
    var = float(np.sum(marg * (GAMMA_GRID - mean) ** 2))
    sd = float(np.sqrt(max(var, 0.0)))

    cdf = np.cumsum(marg)
    lo = float(GAMMA_GRID[int(np.searchsorted(cdf, 0.05))])
    hi = float(GAMMA_GRID[min(int(np.searchsorted(cdf, 0.95)), GAMMA_GRID.size - 1)])

    mu_marg = grid.sum(axis=0)
    mu_mean = float(np.sum(mu_marg * MU_GRID))

    # How much posterior mass sits in the tier the user will be shown.
    tier = gamma_to_tier(mean).tier
    in_tier = np.array([gamma_to_tier(float(g)).tier == tier for g in GAMMA_GRID])
    tier_conf = float(marg[in_tier].sum())

    return DosePosterior(
        grid=grid,
        gamma_mean=mean,
        gamma_sd=sd,
        gamma_ci90=(lo, hi),
        mu_mean=mu_mean,
        n_answers=len(answers),
        tier=tier,
        tier_confidence=tier_conf,
    )


# --------------------------------------------------------------- selection
def expected_information_gain(post: DosePosterior, qid: int) -> float:
    """Mutual information, in bits, between the parameters and the answer.

    Zero when every parameter value the posterior still entertains would
    answer the same way — such a question is not worth a user's attention.
    """
    table = _CACHE.get(qid)
    p_a = float(np.sum(post.grid * table))
    marginal_entropy = float(_binary_entropy(np.array(p_a)))
    conditional_entropy = float(np.sum(post.grid * _binary_entropy(table)))
    return marginal_entropy - conditional_entropy


def _gamble(qid: int) -> tuple[float, float, float]:
    b = QUESTION_BANK[qid].option_b
    return (b.high, b.low, b.p_high)


#: How much expected information to give up for a question that doesn't
#: repeat the previous gamble. Pure information-maximization asks the same
#: coin flip six times with the sure amount nudged each round, which is
#: both tedious and reads like the tool is haggling with the user — and a
#: user who disengages costs far more than a hundredth of a bit.
# Measured, not guessed: at 0.80 the sequence stops repeating a gamble
# back to back with no measurable cost in recovery error (mean RMSE 0.353
# either way across gamma from -0.5 to 3.6); going below 0.7 starts to hurt.
DIVERSITY_TOLERANCE = 0.80


def next_question(
    answers: list[DoseAnswer], post: DosePosterior | None = None
) -> tuple[int, float]:
    """Index of the next question to ask, and its expected gain in bits.

    Most informative unasked question, except that among candidates within
    :data:`DIVERSITY_TOLERANCE` of the best, one that changes the gamble is
    preferred.
    """
    post = post or posterior(answers)
    asked = {a.question_id for a in answers}
    scored = [
        (qid, expected_information_gain(post, qid))
        for qid in range(len(QUESTION_BANK))
        if qid not in asked
    ]
    if not scored:
        raise ValueError("the question bank is exhausted")

    best_id, best_gain = max(scored, key=lambda t: t[1])
    if not answers:
        return best_id, best_gain

    recent = {_gamble(a.question_id) for a in answers[-2:]}
    fresh = [
        (qid, gain)
        for qid, gain in scored
        if gain >= DIVERSITY_TOLERANCE * best_gain and _gamble(qid) not in recent
    ]
    if fresh:
        return max(fresh, key=lambda t: t[1])
    return best_id, best_gain


def is_finished(
    post: DosePosterior,
    n_questions: int = DEFAULT_N_QUESTIONS,
    sd_stop: float = SD_STOP,
) -> bool:
    """Stop on the question budget, or early once gamma is pinned down."""
    if post.n_answers >= n_questions:
        return True
    # Never stop before a handful of answers: an early tight posterior is
    # usually the prior speaking, not the user.
    return post.n_answers >= 4 and post.gamma_sd <= sd_stop


@dataclass
class DoseResult:
    """The finished elicitation, in the same shape the rest of Hone wants."""

    gamma: float
    gamma_sd: float
    gamma_ci90: tuple[float, float]
    mu: float
    n_answers: int
    tier: int
    tier_confidence: float
    summary: str = ""
    gamma_marginal: list[float] = field(default_factory=list)


def summarize(answers: list[DoseAnswer]) -> DoseResult:
    post = posterior(answers)
    t = gamma_to_tier(post.gamma_mean)
    summary = (
        f"{post.n_answers} question{'s' if post.n_answers != 1 else ''} place you at "
        f"γ = {post.gamma_mean:.2f} (90% credible: {post.gamma_ci90[0]:.2f} to "
        f"{post.gamma_ci90[1]:.2f}) — tier {t.tier} of 50, {t.category.lower()}."
    )
    if post.tier_confidence < 0.4:
        summary += (
            " That placement is not sharp yet; a few more questions would "
            "narrow it."
        )
    return DoseResult(
        gamma=post.gamma_mean,
        gamma_sd=post.gamma_sd,
        gamma_ci90=post.gamma_ci90,
        mu=post.mu_mean,
        n_answers=post.n_answers,
        tier=t.tier,
        tier_confidence=post.tier_confidence,
        summary=summary,
        gamma_marginal=[float(x) for x in post.gamma_marginal],
    )


def bank_coverage() -> list[float]:
    """Indifference gamma of every bank question — a diagnostic.

    A bank whose indifference points cluster cannot separate the tiers it
    fails to cover, however cleverly questions are selected.
    """
    return [indifference_gamma(d) for d in QUESTION_BANK]
