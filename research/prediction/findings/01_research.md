# 01 — Market and literature research for the income-hedge model

Research date: 7 November 2026. Scope: the Kalshi rules that matter to a retail hedger, the literature on hedging livelihood risk with an index, other places to get the same hedge, competitors, and (section 5, added at the coordinator's request) what Hone would need to know to price a parametric snow hedge itself.

Everything below has a source link. "Live API" means I queried `api.elections.kalshi.com/trade-api/v2/series/<ticker>` on 7 Nov 2026. "Contract terms PDF" means I downloaded Kalshi's public terms file and read it with `pdftotext`. Claims I could not confirm from a primary source are marked **[unverified]**.

Model files read: `hone/prediction/hedge.py`, `hone/prediction/liquidity.py`, `hone/prediction/contracts.py`, `hone/prediction/kalshi_client.py` and `docs/PREDICTION_MARKETS.md`.

---

## Executive summary

1. **Kalshi's per-member limit does not bind for Hone's users. Market depth does.** Every catalog contract I checked (CPI, YoY CPI, U-3, payrolls, AAA gas, tech layoffs, snowfall, ski openings) sets a *position accountability level* of **$25,000 per strike (or per market) per member**. This is a tripwire, not a hard cap: compliance can ask the member to stop adding or to reduce. Kalshi's ECONSTATB family sets 7,000,000 contracts. A worker with $12k at risk sits well under every level, so the liquidity cap stays the binding constraint.
2. **The fee assumptions are slightly wrong for exactly the liquid series.** The taker fee is `ceil(0.07·C·P·(1−P))` and the live API reports `fee_multiplier = 1` for all 41 catalog series. But CPI, YoY CPI, U-3, payrolls, Fed and AAA gas are `quadratic_with_maker_fees`, so resting orders on them pay `0.0175·C·P·(1−P)`. The docs say resting orders are "generally free", which is not true for the series that supply the most depth.
3. **Block trades and RFQ won't deepen a book for a retail hedger.** The default minimum block is **25,000 contracts**. RFQ traffic is almost all multi-leg combos with a 13-second median lifetime. Nothing I found says market makers will quote a thin economics or weather strike on request.
4. **The biggest model risk is basis, not liquidity.** `joint_states(belief, belief, ρ)` forces P(loss) = P(event). When the two differ, the variance-minimizing hedge is **L × [P(loss | event) − P(loss | no event)]**, not ρ·L. For job loss, layoff rates run about 1.2%/month in normal times and about 2%/month at the 2009 peak. That puts the hedge ratio for an unemployment contract around **0.08–0.20**, so the "11% of the wanted hedge" Kalshi can supply may already be most of the *correct* hedge.
5. **Index-insurance evidence says hedges with basis risk are rarely bought and should be sold as partial protection.** Only 5–10% of Indian farmers bought rainfall insurance. IBLI in Kenya left buyers with 62–77% of their original risk. Clarke (2016) shows demand is *hump-shaped* in risk aversion when basis risk exists. People demand a premium cut of more than 20% to accept a 1% chance that the cover fails to pay.
6. **For the two hedges Kalshi supplies best, simpler retail instruments exist.** Retirees can use TIPS ($100 minimum) and I-bonds ($25 minimum, $10k per person per year) for inflation. Social Security is already CPI-W-indexed (3.6% COLA for 2027). For gas, micro RBOB futures are 4,200 gallons per contract, which is far more than a single driver's monthly fuel. Kalshi's AAA gas binaries are the better fit at retail size.
7. **Alternative event venues exist but add little depth.** Interactive Brokers' ForecastEx lists CPI, unemployment and payrolls contracts with no commission. Polymarket US opened to the public in 2026; its economics taker fee is reported as 5%. **[unverified]** Both should be treated as secondary sources of depth, not substitutes.
8. **No direct competitor hedges personal income with event contracts.** Private unemployment insurance (IncomeAssure) and gig-income cover (Gridwise Protection) are closed to new buyers. Shiller's livelihood insurance was never built, and its closest real product (MacroShares housing) was liquidated in 2009. Parametric snow cover for businesses is active: Arbol (on ERA5 data), Vortex/MSI GuaranteedWeather and Demex/Markel.
9. **Snow sensitivity of ski demand is real but smaller than people assume, and it varies by region.** Austria's long-run elasticity of overnight stays to snow depth is about 0.10, and near zero at high elevations. A Nevada study found 0.21 and a Slovak study up to 1.2. US low-snow seasons cost about 5–16% of national skier visits, with regional collapses (Pacific Northwest −36% in 2014-15).
10. **Selling a parametric payout is regulated in a way that pricing it is not.** A contingent payment on an event is a "swap" under CEA §1a(47)(A)(ii). Individuals below roughly $5–10M invested can only trade swaps on a designated contract market (DCM). To be insurance instead, the product must be written by a state-regulated insurer and sold by licensed producers. The SEC safe harbor also requires an insurable interest and proved loss. Hone's per-user, γ-tailored advice may also fall outside the CFTC's "non-tailored publisher" exemption from commodity trading advisor (CTA) registration. **This needs counsel.**

---

## 1. Kalshi rules that constrain a hedger

### 1.1 Position limits and accountability levels

| Series (catalog ticker) | Terms file | Level per member | Source |
|---|---|---|---|
| CPI (KXCPI), core CPI, annual CPI | CPI.pdf, CORECPI.pdf, ACPI.pdf | $25,000 per member (accountability) | [CPI.pdf](https://assets.kalshi.com/contract_terms/CPI.pdf), [CORECPI.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/CORECPI.pdf), [ACPI.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/ACPI.pdf) |
| YoY CPI (KXCPIYOY) | YOYCPI.pdf | $25,000 per member | [YOYCPI.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/YOYCPI.pdf) |
| Unemployment U-3 (KXU3), max U-3 (KXU3MAX) | U3.pdf, LU3.pdf | $25,000 per member | [U3.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/U3.pdf), [LU3.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/LU3.pdf) |
| Payrolls (KXPAYROLLS) | PAYROLLS.pdf | $25,000 per strike per member | [PAYROLLS.pdf](https://assets.kalshi.com/contract_terms/PAYROLLS.pdf) |
| AAA gas (KXAAAGASM) | AAAGAS.pdf | $25,000 per strike per member | [AAAGAS.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/AAAGAS.pdf) |
| Tech layoffs | TECHLAYOFF.pdf | $25,000 per member | [TECHLAYOFF.pdf](https://assets.kalshi.com/contract_terms/TECHLAYOFF.pdf) |
| Snowfall (Aspen/Denver), Northstar, ski openings | SNOWOVERTIME.pdf, VAILSNOW.pdf, SKIOPEN.pdf | $25,000 per strike per member | [SNOWOVERTIME.pdf](https://assets.kalshi.com/contract_terms/SNOWOVERTIME.pdf), [VAILSNOW.pdf](https://assets.kalshi.com/contract_terms/VAILSNOW.pdf), [SKIOPEN.pdf](https://assets.kalshi.com/contract_terms/SKIOPEN.pdf) |
| Generic econ stats (mortgage rate, holiday retail, wages) | ECONSTATB.pdf | 7,000,000 contracts per member | [ECONSTATB.pdf](https://assets.kalshi.com/contract_terms/ECONSTATB.pdf) |

How these levels work:

* **An accountability level is a tripwire.** Under Rule 5.18 the member must give compliance information on request and stop increasing the position when told; refusal can lead to forced reduction. Hard limits are a separate rule (5.19), and market makers in Kalshi's program are exempt from them ([Oddsshopper summary of Rulebook v1.18, Aug 2026](https://www.oddsshopper.com/articles/prediction-markets/kalshi-position-limits)). This is secondary; I did not read the rulebook itself.
* **"$25,000" probably means maximum loss, not contract count.** Older Kalshi filings defined the position limit as "maximum loss exposure" of $25,000 ([CFTC filing](https://cftc.gov/filings/ptc/ptc020922kexdcm001.pdf)). For a YES bought at price p, the maximum loss is about n·p, so 25,000/p contracts. **[unverified for current wording]**
* **An earlier search summary was wrong.** It said CPI terms now carry 7,000,000 contracts. The current CPI PDFs say $25,000; only ECONSTATB says 7,000,000.

**Implication.** The $12k-at-risk worker wants about $12k notional. At p = 0.3 that is a maximum loss near $3.6k, roughly one-seventh of any accountability level. Even a ski-resort owner hedging $500k would cross the level only on a single strike. A third cap is worth adding as a *soft* warning ("above Kalshi's $25k accountability level for this strike"), not a hard limit. Spreading across strikes avoids it, because most levels are per strike.

### 1.2 Fees

* **Taker fee:** `round_up(0.07 × C × P × (1−P))`. **Maker fee**, on series that charge one: `round_up(0.0175 × C × P × (1−P))`, charged only when a resting order fills ([Kalshi fee schedule PDF, effective 5 Feb 2026](https://kalshi.com/docs/kalshi-fee-schedule.pdf); [PredictionHunt guide, Oct 2026](https://www.predictionhunt.com/blog/kalshi-fees-complete-guide-2026); [Whirligig Bear](https://whirligigbear.substack.com/p/makertaker-math-on-kalshi)). The PDF itself returned HTTP 429 to me, so the formula comes from secondary sources that agree with each other. A guide reports a schedule effective 7 July 2026, `round_up(M × 0.07 × C × P × (1−P))`, and 157 series with non-standard fees as of 10 Oct 2026. **[unverified]**
* **Live API, all 41 catalog series:** `fee_multiplier = 1`. The following are `quadratic_with_maker_fees`: KXCPI, KXCPIYOY, KXU3, KXPAYROLLS, KXFED and KXAAAGASM. All the rest are `quadratic` (taker only). The `/series/fee_changes` endpoint returned an empty list, so no fee changes are scheduled.
* **The fee as an insurance loading** (my computation): at P = 0.10, 0.30 and 0.50 the taker fee is 6.3%, 4.9% and 3.5% of the price. That is an order of magnitude cheaper than insurance-style loadings (section 5b) *where depth exists*. The spread usually costs more than the fee.
* **Cash movement:** ACH deposits and withdrawals are reported free, wires $5, debit-card deposits 2% ([Fortunly review](https://fortunly.com/reviews/kalshi-review/); [pm.wiki](https://pm.wiki/uk/learn/kalshi-withdrawal-guide)). **[unverified]**

### 1.3 Eligibility

* You must be 18 or older with a legal US residential address (50 states, DC or territories), per [Kalshi help](https://help.kalshi.com/faq/how-do-i-open-an-account). Sign-up requires SSN and ID ([next.io](https://next.io/prediction-markets/kalshi/age/)).
* **State restrictions are contested and change often.** 2026 guides list AZ, IL, MA, MD, MI, MT, NV and OH (some include NJ), and some restrictions cover only certain markets ([sailgp](https://sailgp.com/prediction-markets/kalshi/legal); [saturdaydownsouth](https://www.saturdaydownsouth.com/prediction-markets/kalshi-promo-code/legal-states/)). **[unverified, changing]**
* **Per-series exclusions:** employees of the source agency and holders of material non-public information may not trade (live API `additional_prohibitions` for KXCPIYOY). This matters for a BLS employee hedging their own job.

### 1.4 Settlement timing

* Every terms file I read says settlement is "no later than the day after the Expiration Date, unless the Market Outcome is under review" (Rule 7.1). CPI expires at 8:31 or 10:00 AM ET on release day; U-3 at 10:00 AM ET; AAA gas at 10:15 AM, 11:00 AM or 3:00 PM ET. (Contract terms PDFs above.)
* Economic contracts settle on the **first official release**; later revisions are ignored ([ECONSTAT.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/ECONSTAT.pdf)).
* **Snowfall contracts settle on a hierarchy of sources:** The Weather Company, then NWS, then OnTheSnow, or on resort-reported snow for the Vail/Northstar series (SNOWOVERTIME.pdf, VAILSNOW.pdf). That is a different data source from the one section 5 would use.
* **The timing mismatch is structural.** A monthly CPI or U-3 contract pays one day after a release that describes the *previous* month. Income losses arrive later and are spread out.

### 1.5 Do market makers deepen books? RFQ and blocks

* **Market-maker program.** Kalshi runs a Market Maker Program (status by review; benefits conditional on keeping liquidity, [help.kalshi.com](https://help.kalshi.com/en/articles/13823819-market-maker-program)). It also runs a Liquidity Incentive Program that rewards resting orders, and in 2026 restructured both into a "Designated Liquidity Provider" program running to 1 Dec 2027 ([CFTC filing](https://www.cftc.gov/filings/orgrules/rules10182634499.pdf); [SBC Americas on ending volume rewards, Oct 2026](https://sbcamericas.com/2026/10/02/kalshi-end-volume-rewards-scrutiny/)). Coverage is decided by designation, not by user demand.
* **RFQ.** Any requester can send an RFQ on any market through REST, FIX or WebSocket. Makers must confirm within 30 seconds (3 seconds in volatile markets). Only one open RFQ per market per user ([docs.kalshi.com/getting_started/rfqs](https://docs.kalshi.com/getting_started/rfqs)). In practice, the median RFQ lifetime is 13 seconds and nearly all RFQs are multi-leg combos ([Oddpool](https://www.oddpool.com/research/kalshi-rfq-market-makers)). **I found no evidence that makers answer single-leg RFQs in thin economics or weather markets.** Hone could test this empirically.
* **Blocks.** Pre-execution communication and block trades have been allowed since February 2026 (Rule 5.3). The default minimum is **25,000 contracts** (50,000 for sports, from 16 July 2026), and separate orders can't be aggregated ([help.kalshi.com block trades](https://help.kalshi.com/en/articles/15165864-block-trades); [CFTC filing](https://www.cftc.gov/filings/orgrules/rules0701268688.pdf)). Cantor's brokered block access is for institutions ([CryptoDaily](https://cryptodaily.co.uk/2026/08/cantor-kalshi-block-trades-3000-institutions)). **Not usable at retail size.**

---

## 2. Prior work: hedging livelihood risk with an index

### 2.1 Shiller: macro markets and livelihood insurance

* **The proposal.** A long-term policy pays when an index of income for *your occupation and region* falls. Insurers would lay the risk off in "macro markets", long-term claims on income aggregates ([NY Fed EPR, Athanasoulis, Shiller and van Wincoop 1999](https://www.newyorkfed.org/medialibrary/media/research/epr/99v05n1/9904atha.pdf); [Wharton summary](https://knowledge.wharton.upenn.edu/?p=3559)).
* **The argument.** Indexing to the group's income, not the person's, removes moral hazard, and premiums would reveal which occupations the market sees as threatened.
* **What happened.** None of it was built. The closest product, the MacroShares Case-Shiller housing pair (UMM/DMM), drew few assets and was liquidated in December 2009. The CME housing futures traded thinly ([24/7 Wall St](https://247wallst.com/housing/2009/12/28/case-shiller-etfs-bite-the-dust-umm-dmm/print/); [Fortune/CNN 2009](https://money.cnn.com/2009/07/06/real_estate/robert_shiller_housing_market.fortune/index.htm)).
* **Lesson for Hone.** Hedgers were natural buyers but not enough to sustain depth. Hone's job is to aggregate demand from many small hedgers, which is exactly what the thin books are missing.

### 2.2 Davis and Willen: occupation income and asset returns

* Occupation-level income shocks (estimated from the CPS) are **essentially uncorrelated with aggregate equity returns**. Size-sorted and some industry portfolios do correlate significantly for several occupations ([NBER w7905](https://www.nber.org/papers/w7905); [Boston Fed WP 13-9](https://www.bostonfed.org/publications/research-department-working-paper/2013/occupation-level-income-shocks-and-asset-returns-their-covariance-and-implications-for-portfolio-choice.aspx)). I did not retrieve exact coefficients.
* **Lesson for Hone.** A *macro* index (U-3, payrolls) is a weak proxy for one occupation's income. Sector or occupation-specific indices are better. Hone's "proxy" label for the hiring series is right, and the default ρ for it should be low (section 2.4).

### 2.3 Index insurance, basis risk and uptake

| Study | Finding | Number |
|---|---|---|
| Cole, Giné, Tobacman, Topalova, Townsend, Vickery (India rainfall) | Low uptake despite rainfall being the top-ranked risk; distance to the rain gauge (basis) lowers take-up; trust and liquidity matter | **5–10%** take-up; halving the price raised take-up **17.6 pp** ([NY Fed SR 373](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr373.pdf); [J-PAL](https://www.povertyactionlab.org/es/node/1721)) |
| Giné and Cole (Gujarat) | Price elasticity of demand | −0.66 to −0.88; range across studies −0.44 to −1.16 ([Jensen, Mude and Barrett via MPRA 60452](https://mpra.ub.uni-muenchen.de/60452/1/MPRA_paper_60452.pdf)) |
| Jensen, Barrett and Mude (Kenya IBLI livestock) | Index cuts covariate high-loss risk but leaves most total risk | Covariate risk cut by **62.8%**; buyers keep **62.3–76.7%** of original risk ([MPRA 75026](https://mpra.ub.uni-muenchen.de/75026/9/MPRA_paper_75026.pdf); AJAE 2016) |
| Clarke (2016, AEJ: Micro) | With basis risk, demand for unfairly priced index cover is **hump-shaped** in risk aversion; infinitely risk-averse buyers want none | Theory ([EconPapers](https://econpapers.repec.org/RePEc:aea:aejmic:v:8:y:2016:i:1:p:283-306)) |
| Elabed and Carter (Mali) | About 57–60% of farmers are compound-risk averse, which roughly halves potential demand; a contract with less basis risk raises demand about 40% (simulated) | ([JEBO 2015 via EconPapers](https://econpapers.repec.org/RePEc:eee:jeborg:v:118:y:2015:i:c:p:150-166); [Bellemare blog](https://marcfbellemare.com/wordpress/category/insurance)) |
| Wakker, Thaler and Tversky (1997); later experiments | "Probabilistic insurance": people want a **more than 20%** premium cut for a 1% chance the cover fails to pay; in one experiment willingness to pay fell from $54 to $29 at a 3% default risk | ([Wakker PDF](https://personal.eur.nl/wakker/pdfspubld/97.6pijru.pdf); [JRI 2018 summary](https://law-journals-books.vlex.com/vid/an-incentivecompatible-experiment-on-855588457)) |
| Correlation of index with outcome | Ground-station rainfall indices: at most **12.5%** correlation with yields; satellite indices **44–62%**; weather explains a small share of yield variance in village India | ([islandarchives](https://scholar2.islandarchives.ca/islandora/object/ir%3A23439); [arXiv 2103.11047](https://arxiv.org/pdf/2103.11047)) |

**Quantitative lessons for Hone:**

1. **Realistic basis correlations are low.** Farm-level index correlations below 0.5 are typical and often below 0.2. Hone's "direct" label (ρ near 0.9) should be reserved for contracts that settle on the same measure that drives the person's pay.
2. **People penalize "the hedge might not pay when I lose" far more than expected-utility theory predicts.** The page should show the probability of a *false negative*, P(no payout | loss), as its own number, not just ρ.
3. **Hone's exact CRRA optimization already reproduces Clarke's hump** (wealth falls in the state where the person loses and the contract pays nothing). Do not override it with a "more risk-averse means hedge more" heuristic anywhere in the UI copy.
4. **Price matters a lot (elasticity around −0.7)**, so spread and fee belong prominently in the recommendation.

### 2.4 Job loss and an unemployment index: what ρ is realistic?

* **Layoff rates.** JOLTS layoffs and discharges were **1.2% per month** through 2019 ([BLS TED](https://www.bls.gov/opub/ted/2019/6-million-hires-and-5-point-8-million-job-separations-in-july-2019.htm)). At the April 2009 peak they were about **2%** (2.7M; [EPI](https://www.epi.org/?p=149312); [BLS release](https://www.bls.gov/news.release/archives/jolts_12082009.pdf)). Almost **1 in 6** workers lost a job in 2007-09 ([Farber, NBER w21216](https://www.nber.org/papers/w21216)).
* **Illustrative calculation** (my own, not sourced). Let the contract event ("U-3 above X") have probability 0.2. Suppose a worker's annual chance of losing their job is 20–30% if the event happens and 10–12% if it doesn't. Then:
  * the phi correlation is **0.09–0.23**;
  * the variance-minimizing hedge ratio, P(loss | event) − P(loss | no event), is **0.08–0.20**;
  * P(loss) is about 0.14, which is *not* equal to P(event). Hone's code currently assumes the two are equal.
* **What this means.** Kalshi supplying about 11% of the wanted unemployment hedge is less of a shortfall than it looks. If the wanted hedge were sized with a realistic ρ and separate marginals, liquidity would rarely bind for job-loss hedges.

---

## 3. Other venues and instruments when Kalshi is thin

| Instrument | What it hedges | Minimum size | Cost | Retail access | Fit with Hone |
|---|---|---|---|---|---|
| **TIPS** (TreasuryDirect or a broker) | Inflation, linearly, on principal | **$100**, in $100 increments ([TreasuryDirect TIPS](https://treasurydirect.gov/marketable-securities/tips/)) | No fee at TreasuryDirect; 45-day hold before transfer ([TreasuryDirect](https://www.treasurydirect.gov/marketable-securities/buying-a-marketable-security/)) | Anyone with an SSN and bank account | **Best inflation alternative for retirees**: linear, no basis to CPI-U, no counterparty issue |
| **I-bonds** | CPI-U plus a fixed rate | **$25**; max **$10,000** per SSN per year; hold at least 12 months; 3-month interest penalty before 5 years ([TreasuryDirect FAQ](https://www.treasurydirect.gov/indiv/help/treasurydirect-help/faq/); [comparison](https://treasurydirect.gov/research-center/history-of-savings-bond/comparing-tips-to-i/)) | None; May–Oct 2026 composite rate 4.26% (0.90% fixed; [mymoneyblog](https://www.mymoneyblog.com/savings-i-bonds-may-2026-interest-rate.html)) | Anyone | Good for small amounts; the cap limits it |
| **Social Security COLA** | Benefits indexed to CPI-W by law; 2027 COLA 3.6% ([SSA press release](https://www.ssa.gov/news/en/press/releases/2026-10-14.html); [SSA COLA](https://www.ssa.gov/news/en/cola/index.html)) | n/a | n/a | n/a | **A natural hedge already held.** Retirees' inflation exposure L should exclude the share of spending covered by SS. |
| **ForecastEx (Interactive Brokers)** | Yes/no on CPI, unemployment, GDP, payrolls, claims and climate | 1 contract | $0 IBKR commission; ForecastEx keeps $0.01 per pair ([IBKR](https://www.interactivebrokers.com/en/index.php?f=66064); [commissions](https://brokerage.ibkr.com/en/pricing/commissions-events.php)) | IBKR account | Same instrument type as Kalshi; **second source of depth** for CPI and U-3. Depth and position limits not checked. **[unverified]** |
| **Polymarket US** (QCEX, CFTC-designated) | Event contracts | 1 contract | Economics taker fee reported **5%** (category schedule from 1 July 2026), makers free ([River Markets](https://www.rivermarkets.com/insights/polymarket-us-fees.html)) **[unverified]** | Waitlist dropped May 2026; state restrictions similar to Kalshi's; litigation ongoing ([Gambling Insider](https://www.gamblinginsider.com/?p=106291); [The Block](https://www.theblock.co/post/399234/polymarket-eyes-return-main-exchange-us-in-talks-cftc-bloomberg)) | Listings in CPI and U-3 unknown. Treat as optional. |
| **CME micro RBOB** | Wholesale gasoline | **4,200 gal** per contract ([CME rulebook ch. 435](https://www.cmegroup.com/rulebook/NYMEX/4/435.pdf)) | Commission plus margin | Futures account | **Too big.** A driver doing 40,000 mi/yr at 25 mpg (my assumption) uses about 1,600 gal/yr, so one contract is about 2.6 years of fuel. RBOB also trades $0.80–1.00/gal below the retail price with asymmetric pass-through ([JPT](https://jpt.spe.org/twa/oil-prices-fell-so-why-dont-pump-prices); [FTC WP 302](https://www.ftc.gov/sites/default/files/documents/reports/asymmetric-pass-through-u.s.gasoline-prices/wp302_0.pdf)). |
| **UGA gasoline ETF** | RBOB futures, rolled | 1 share (fractional at some brokers) | **0.97%** expense ratio plus roll yield ([ETFdb](https://etfdb.com/etf/UGA/)); does not track spot or retail gasoline ([10-Q](https://www.sec.gov/Archives/edgar/data/0001396878/000110465926057773/uga-20260331x10q.htm)) | Any brokerage | Linear and finely divisible, so it suits small fuel hedges. Needs a ρ below 1 versus AAA retail. |
| **CME micro 10-year yield futures** | Interest rates | **$10 per basis point**; about $640–720 margin in 2024 ([CME](https://www.cmegroup.com/articles/2024/micro-treasury-futures-vs-yield-futures.html); [Saxo](https://home.saxo/en-sg/content/articles/bonds/micro-treasury-yield-futures-contracts-a-simple-way-to-trade-interest-rates-markets-17042024)) | Commission plus margin | Futures account | Possible replacement for the 0–2% mortgage-rate Kalshi depth (realtors). One contract equals $1k per 100 bp, a reasonable retail size. Mortgage rates have basis to the 10-year. |
| **Sector ETFs** | Industry equity as a proxy for sector income | 1 share | Low | Any brokerage | Davis and Willen: industry portfolios correlate with some occupations' income, the aggregate market does not. Possible "proxy" fallback. Beyond this research's scope. |

---

## 4. Competitors and similar products

* **IncomeAssure** (Assura/SterlingRisk, underwritten by Great American, launched 2011). Paid up to 50% of salary for 24 weeks, combined with state UI benefits, with a 90-day exclusion at the start. It is **closed to new coverage** ([BenefitsPro](https://www.benefitspro.com/2011/08/17/assura-group-launches-unemployment-insurance); [Retirement Income Journal](https://retirementincomejournal.com/?p=7294)). A "SafetyNet" alternative is mentioned by the same source. **[unverified]**
* **Gridwise Protection** (US gig drivers). Replaced 80% of lost income after hospitalization, deactivation or a collision. **Not accepting new customers** ([gridwise.io](https://gridwise.io/protection)). Abroad, GoJek and GigaCover pay daily income for up to 84 days ([Insurance Business](https://insurancebusinessmag.com/asia/news/breaking-news/gojek-and-gigacover-launch-income-protection-cover-for-drivers-160143.aspx)).
* **Sensible Weather.** Consumer "weather guarantee" sold through resorts and campgrounds; automatic payout on measured weather. Reported price is about **8–12% of trip cost** ([Sensible help](https://sensiblehelp.zendesk.com/hc/en-us/articles/40877082840211-How-do-Weather-Guarantees-work); [Entrepreneur](https://entrepreneur.com/living/one-company-will-pay-you-to-enjoy-bad-weather-on-vacation/449743)).
* **Prediction-market hedging tools.** Hedgebook maps S&P 500 stocks to Kalshi contracts for *equity* hedging ([Crypto Briefing](https://cryptobriefing.com/hedgebook-launches-kalshi-equity-hedging/)). Vitalik Buterin has proposed AI-built prediction-market portfolios to hedge personal expenses ([Let's Data Science](https://letsdatascience.com/news/buterin-proposes-prediction-markets-provide-price-stability-38015d54)); this is a concept only. **I found no shipped product that sizes event contracts against personal income.**
* **Parametric snow cover for businesses:** Arbol, Vortex and Demex (section 5b).

---

## 5. Pricing protection ourselves

### 5a. How sensitive are ski revenues and incomes to snowfall?

| Source | Region and outcome | Estimate |
|---|---|---|
| Falk (2010), *Tourism Management* | 28 Austrian resorts, overnight stays, 1986–2006 | Long-run snow-depth elasticity **0.10**; **no effect at high-elevation resorts** ([EconPapers](https://econpapers.repec.org/RePEc:eee:touman:v:31:y:2010:i:6:p:912-924); [EconBiz](https://econbiz.de/Record/a-dynamic-panel-data-analysis-of-snow-depth-and-winter-tourism-falk-martin/10008650035)) |
| Englin and Moeltner (as cited by Gonseth 2013) | Nevada college ski trips | Snow elasticity of demand **0.21** ([Gonseth 2013](https://infoscience.epfl.ch/record/177595)) **[secondary]** |
| Slovak study (as cited) | Slovak resort | Snow-depth elasticity up to **1.2** ([same review](https://infoscience.epfl.ch/record/177595)) **[secondary]** |
| Gonseth (2013), *Climatic Change* | 74 Swiss areas | Snowmaking reduces sensitivity to poor natural snow ([IDEAS](https://ideas.repec.org/a/spr/climat/v119y2013i2p307-320.html)) |
| Damm et al. (2017), *Climate Services* | 119 European NUTS-3 regions | A significant snow–overnight stays link in only 56–66 of 119 regions; risk highest in Austria and Italy, lowest in France and Switzerland ([DOAJ](https://doaj.org/article/241a9e48fc444fd59f8b7f52bf380ae2)) |
| Shih, Nicholls and Holecek (2009), *JTR* | Two Michigan resorts, daily lift tickets | Snow depth and temperature significant; warmth consistently hurts ([VTechWorks](https://vtechworks.lib.vt.edu/handle/10919/81425)) |
| NSAA 2011-12 | US | Visits **−15.7%** in the lowest-snowfall season since 1991-92 ([PR Newswire](https://prnewswire.com/news-releases/skisnowboard-industry-201112-season-wrap-up-bright-spots-emerge-but-skier-visits-plunge-151699545.html); [SAM](https://www.saminfo.com/news/sam-headline-news/7281-424-resort-visits-tumbled-16-percent-in-2011-12)) |
| NSAA 2014-15 | US and regions | Snowfall **28%** below average nationally; visits **−5%** nationally, **−36.3% Pacific Northwest**, −6.4% Pacific Southwest ([SAM](https://www.saminfo.com/news/sam-headline-news/14657-718-seasona-s-visits-drop-5-percent-to-53-6-million); [Pique](https://www.piquenewsmagazine.com/whistler-news/us-skier-visits-down-five-per-cent-in-201415-season-2498376)) |
| 2013-14 Pacific Southwest (secondary) | California and Nevada | Snowfall −32%, visits −27.8% **[unverified]** ([same SAM coverage](https://www.saminfo.com/news/sam-headline-news/14657-718-seasona-s-visits-drop-5-percent-to-53-6-million)) |
| Burakowski and Magnusson (2012, 2018) | US | Low-snow years cost about 10% of visits (5.5M), about $1B and 17,400 jobs; good-versus-bad spread 1999–2010 was $0.8–1.9B and 13–27k jobs ([WAMC](https://www.wamc.org/us-news/2018-03-30/new-study-says-winter-sports-resorts-need-to-diversify); [Grist](https://grist.org/climate-energy/go-skiing-now-while-you-still-can/)) |

**Suggested defaults (my synthesis; label them as such in the product):**

* **What drives the loss.** It is concentrated in the bad tail: early season, the holiday weeks, and seasons below roughly 70% of normal snowfall. It is not linear.
* **Default elasticity of revenue to a seasonal-snowfall shortfall, applied only below the trigger:**
  * high-elevation Rockies and Intermountain with snowmaking: **0.2–0.3**;
  * Northeast and Midwest, where snowmaking is heavy and temperature matters more than snowfall: **0.3–0.5**, but a *snowfall* index is a weak proxy there, so use a low ρ;
  * Pacific Northwest and Sierra (lower elevation, rain risk): **0.6–1.0**.
* **Ski-instructor income.** I found **no published elasticity**. Instructors' hours are the marginal labor resorts cut, so income is plausibly *at least* as sensitive as visits. **[unverified assumption]**

### 5b. Who sells parametric snow and weather protection, on what index, at what price?

| Provider | Product | Index and data | Size and price info |
|---|---|---|---|
| **Arbol** (Arbol Insurance Services, licensed agency; Lloyd's coverholder) | Low-snowfall cover for resorts, snow removal and seasonal tourism, all 50 states | **ERA5 cumulative snowfall**. Example: trigger 35 in, full limit at 20 in, $6,666.67/in, $100k limit, window 1 Dec–27 Feb | Price by request; no minimum published ([Arbol product page](https://insurance.arbol.io/product/low-snowfall); [Arbol blog](https://arbol.io/post/weather-proofing-winter-tourism-how-parametric-insurance-protects-resort-revenue)) |
| **Vortex Weather Insurance** (MSI GuaranteedWeather) | Lack-of-snow, excess-snow, event-count and single-day covers, sold direct since Sept 2025 | "Independent snowfall data"; source not named | "No minimum eligibility requirements"; price not published ([Reinsurance News](https://www.reinsurancene.ws/vortex-launches-parametric-snow-insurance/); [PR](https://www.streetinsider.com/PRNewswire/Vortex+Weather+Insurance+Launches+Direct+Access+to+Snow+Risk+Policies/25346086.html)) |
| **Demex** (written by Evanston/Markel, non-admitted; Nephila and reinsurers take the risk) | Revenue protection (very low snow) and cost control (very high snow) | Not named | Not published ([Artemis](https://www.artemis.bm/news/demex-launches-parametric-snow-covers-backed-by-nephila-reinsurers/)) |
| **CME** | Snowfall futures and options on cities (from 2006) | Station data | **Delisted; no open interest** ([CME SER-7216](https://www.cmegroup.com/tools-information/lookups/advisories/ser/SER-7216.html)) |
| **Kalshi** | Resort snowfall and opening-date binaries | TWC, then NWS, then OnTheSnow; or resort-reported (contract terms PDFs) | Exchange fees as in section 1.2; 0–2% of the wanted hedge was available in Hone's live check |

**Price loadings** (no published loading for retail snow cover; these are benchmarks):

* Catastrophe bonds price at **2.3–2.5× expected loss** in 2026, down from 3.0× in 2025 and 3.7× in 2024 ([Artemis/AM Best](https://www.artemis.bm/news/as-cat-bond-loss-multiples-tighten-am-best-urges-investors-towards-greater-selectivity/)). These are remote tail layers; frequent weather layers carry lower multiples.
* One Indian weather-index contract carried about **47%** loading. A modelling paper finds a **10%** loading still attractive at CRRA ≈ 2 ([survey of results](https://arxiv.org/pdf/2103.11047)). Commercial premiums are built from expected loss, plus reinsurance, plus a profit loading that rises with poor data ([McIntosh slides](https://api.sambuz.com/doc/weather-index-insurance-ppt-presentation-247417)).
* Actuaries typically price with burn analysis plus a **standard-deviation loading** ([Hal/EMSE](https://hal-emse.ccsd.cnrs.fr/emse-00699607/document)).
* **Minimum deal sizes are not published by anyone.** **[unverified]**

### 5c. Where the regulatory line falls (US)

* **A parametric payout sold bilaterally is presumptively a swap.** The CEA defines a swap to include any payment "dependent on the occurrence, nonoccurrence, or the extent of the occurrence of an event or contingency associated with a potential financial, economic, or commercial consequence" ([7 U.S.C. §1a(47)(A)(ii)](https://www.law.cornell.edu/uscode/text/7/1a)).
* **Retail swaps must trade on a DCM.** It is unlawful for anyone other than an eligible contract participant to enter a swap except on, or under the rules of, a DCM ([7 U.S.C. §2(e)](https://www.law.cornell.edu/uscode/text/7/2)). An individual is an ECP only with more than **$10M** invested on a discretionary basis, or more than **$5M** when hedging an owned asset or liability ([§1a(18)(A)(xi)](https://www.law.cornell.edu/uscode/text/7/1a)). Kalshi listing a contract is what makes event exposure legal for retail.
* **The insurance route (SEC/CFTC 2012 safe harbor).** The product must:
  * give the beneficiary an insurable interest carried continuously;
  * "require that loss … occur and … be proved", with payment limited to the value of that interest;
  * not be traded separately;
  * be provided by a state-supervised insurer and regulated as insurance under state law ([17 CFR §240.3a69-1](https://www.law.cornell.edu/cfr/text/17/240.3a69-1)).

  The safe harbor is non-exclusive: products outside it get a facts-and-circumstances review ([thinkadvisor](https://www.thinkadvisor.com/amp/2011/05/23/feds-propose-more-swaps-definitions/)). This is why US parametric covers usually carry a proof-of-loss clause ([Wharton 2020](https://esg.wharton.upenn.edu/wp-content/uploads/2020/09/Parametric-Insurance-for-Disasters_Sep-2020.pdf)).
* **States.** New York explicitly authorized weather-parametric insurance (snow included) from 12 Jan 2025 under new Insurance Law §3416. It requires disclosures and **sale by licensed agents** ([Clark Hill](https://clarkhill.com/news-events/news/new-york-enacts-parametric-insurance-law); [Kennedys](https://kennedyslaw.com/en/thought-leadership/article/2025/new-york-insurance-law-adds-parametric-insurance-as-covered-insurance)). Existing sellers work through licensed agencies (Arbol) or surplus-lines carriers (Demex/Evanston).
* **Advice.** CFTC Rule 4.14(a)(9) exempts from CTA registration only advice that is standardized and **not tailored** to a client's positions or circumstances, such as newsletters, websites and "non-customized software" ([CFTC 2000 release](https://www.cftc.gov/sites/default/files/foia/fedreg00/foi000310a.htm); [CFTC letter 03-26](https://www.cftc.gov/sites/default/files/tm/letters/03letters/tm03-26.htm); [NFA exemptions](https://www.nfa.futures.org/members/cta/cta-exemptions.html)). Hone sizes positions to the user's γ and exposure, which is arguably tailored. I found no guidance specific to event contracts. **This needs counsel.**
* **The line, summarized.**
  1. Showing prices, historical burn and a computed fair value is software or publishing.
  2. Recommending a specific size of a specific contract to a specific person may require CTA registration (or an exemption) for futures, swaps and event contracts, and investment-adviser status for TIPS and ETFs ([Lowe v. SEC](https://supreme.justia.com/cases/federal/us/472/181/)).
  3. *Paying* a parametric claim is insurance (licensed insurer and producers) or a swap (a DCM for retail). Hone cannot be the counterparty itself.

### 5d. Known biases of ERA5 and Open-Meteo snowfall in mountains

* **Resolution and model mixing.** Open-Meteo's historical API serves ERA5 at 0.25° (about 25 km) and ERA5-Land at 0.1° (about 11 km). ERA5-Land has no snowfall of its own; it takes ERA5's forcing. The default "Best Match" blends ECMWF IFS at 9 km from 2017 with ERA5. **A long index must explicitly request `models=era5`**, or the record changes model mid-way ([Open-Meteo docs](https://open-meteo.com/en/docs/historical-weather-api)).
* **Fixed snow-to-liquid ratio.** Open-Meteo converts precipitation to snowfall at a fixed **7 cm snow per 10 mm water** (stated in the docs). Real mountain snow is much fluffier: Alta's median is **13.3:1** (interquartile range 10–18:1), and the ratio varies from storm to storm ([Univ. of Utah/NOAA slides](https://vlab.noaa.gov/documents/10157/137122/Steenburgh-VLabForum-11-20-2024.pdf); [Veals et al. 2025](https://www.inscc.utah.edu/~u0813947/sharing/Veals_etal_2025_v1.5.pdf)). So Open-Meteo "snowfall" will read about **half of resort-reported snowfall**. Triggers must be set as percentiles of the reanalysis's *own* history, never in resort inches.
* **Elevation bias.** ERA5 underestimates snow increasingly with elevation in Central Europe and the Alps ([The Cryosphere 2026](https://tc.copernicus.org/articles/20/2295/2026/)). The sign varies by region (overestimation on the Tibetan Plateau; [Frontiers 2019](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2019.00280/pdf)). In the western US, ERA5 has a dry bias on the West Coast ([HESS 2020](https://hess.copernicus.org/articles/24/2527/2020/)), and ERA5-driven WRF underestimates spring snow water equivalent by 33% in the Sierra Nevada but overestimates it by 10% in the Middle Rockies ([ESS Open Archive](https://essopenarchive.org/doi/full/10.22541/essoar.173031831.16231136/v1)).
* **Downscaling.** Open-Meteo applies statistical downscaling to a 90 m elevation model by default. The `elevation` parameter changes the result, so pin it to the resort's mid-mountain elevation and keep it fixed (docs).
* **SNOTEL.** About **850–900+** sites report snow water equivalent, precipitation, depth and temperature, some hourly ([NRCS](https://www.nrcs.usda.gov/programs-initiatives/sswsf-snow-survey-and-water-supply-forecasting-program); [Fleming et al. 2023](https://www.nrcs.usda.gov/sites/default/files/2023-02/J%20American%20Water%20Resour%20Assoc%20-%202023%20-%20Fleming%20-%20SNOTEL%20%20the%20Soil%20Climate%20Analysis%20Network%20%20and%20water%20supply%20forecasting%20at_1.pdf)). SNOTEL does **not** directly measure "snowfall", and its gauges undercatch. Snow water equivalent or depth on a fixed date is the natural SNOTEL index.
* **Licensing.** Open-Meteo's free tier is non-commercial; commercial use requires a paid plan (docs page, "Usage licence"). ERA5 itself is Copernicus data, free with attribution.

---

## Implications for Hone's model (ranked)

1. **Stop forcing P(loss) = P(event) in `joint_states`.** Take separate `q_loss` (or ask "chance you lose this income if the event happens / if it doesn't"). Then compute the pure hedge as **L × (P(loss | event) − P(loss | no event))**. *Test:* qe = 0.2, a = 0.3, b = 0.1 gives a pure hedge of 0.20·L and ρ ≈ 0.23. The current code would give 0.23·L with q_loss forced to 0.2.
2. **Lower the default basis correlation per hedge type** and show it next to the "direct / close / proxy" label:
   * job loss on U-3, payrolls or claims: **≤ 0.25** (default 0.15);
   * tech layoffs as a proxy for one person's job: ≤ 0.2;
   * retiree inflation on a CPI contract versus their own basket: about 0.7–0.8, since basket mix and the Social Security COLA cover part of it;
   * gas on AAA monthly versus a driver's own pump price: about 0.8–0.9;
   * snowfall on a resort-specific index versus an instructor's income: about 0.4–0.6.

   *Test:* recompute the live-check coverage table with these ρ. If the live check sized the hedge at ρ near 1, the same supply covers about 11%/0.15 ≈ 70% of a ρ = 0.15 hedge. Confirm which ρ the check used.
3. **Show the false-negative probability**, P(no payout | you lose), and the residual-risk share, 1 − ρ², as plain numbers on the page. This is how index insurers communicate basis risk; IBLI buyers keep 62–77% of their risk. *Test:* the field is present and equals p01/(p01 + p11) from `joint_states`.
4. **Fix the fee model.** Read `fee_type` per series and apply the 0.0175 maker fee on `quadratic_with_maker_fees` series (CPI, YoY CPI, U-3, payrolls, Fed, AAA gas). Keep reading `fee_multiplier` from the API. Correct "resting orders are generally free" in `contracts.py` and the docs. *Test:* `kalshi_fee(100, 0.5, maker=True, fee_type="quadratic_with_maker_fees") == 0.44`.
5. **Add the accountability level as a soft third cap.** $25,000 maximum loss per strike per member for the contracts checked, or 7,000,000 contracts for ECONSTATB series. Warn above it; don't truncate. Spreading across strikes avoids it. *Test:* a plan with n·p > 25,000 on one strike sets a `position_accountability_warning` flag.
6. **Offer alternatives when Kalshi covers less than about 50% of the hedge:**
   * inflation (retirees): TIPS ($100 minimum) or I-bonds ($25–$10k a year), and subtract Social Security-indexed income from L first;
   * gas: UGA or other fractional exposure rather than micro RBOB (4,200 gal is about 2.6 years of a driver's fuel);
   * mortgage rates: CME micro 10-year yield futures ($10/bp);
   * a second event venue: ForecastEx for CPI and U-3.

   *Test:* the plan returns an `alternatives` list whenever `coverage < 0.5`.
7. **Don't promise that RFQ or blocks add depth.** The 25,000-contract block minimum is well above retail size. A single-leg RFQ in a thin series is an empirical question. *Test:* send a few RFQs on KXU3 and KXAAAGASM and record response rate and spread before saying anything in the UI.
8. **Snow pricing (section 5 product):**
   * Use `models=era5` only, with a fixed elevation and percentile triggers.
   * Apply regional revenue elasticities only below a threshold of about 70% of normal (0.2–0.3 Rockies, 0.3–0.5 East/Midwest with low ρ, 0.6–1.0 Pacific).
   * Price as burn cost plus a standard-deviation loading, and show the result next to market benchmarks (cat bonds 2.3–2.5× expected loss, index insurance about 10–50%).
   * *Test:* back-test against NSAA regional visit changes in 2011-12, 2013-14 and 2014-15.
9. **Get legal advice before Hone (a) personalizes contract-sized recommendations at scale or (b) offers any payout itself.** Pricing and display are on the software side. Recommending sizes may need CTA or investment-adviser treatment. Paying claims needs an insurer or a DCM.

## What I could not verify

* The current KalshiEX rulebook text (Rules 5.18 and 5.19) and whether the "$25,000" level is maximum loss or notional.
* The official Kalshi fee PDF (HTTP 429). The formula comes from consistent secondary sources and the live `fee_type` field.
* Polymarket US fees and its CPI and unemployment listings.
* ForecastEx position limits and depth.
* Exact snowfall percentages by region for the NSAA seasons.
* The 2013-14 Pacific Southwest figures.
* Any published elasticity for ski-instructor income.
* Parametric snow pricing or minimum premiums from any vendor.
* Whether CTA Rule 4.14(a)(9) covers personalized event-contract sizing.
