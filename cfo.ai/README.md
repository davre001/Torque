# Torque business and financial plan

Prepared with cfo.ai; exported evidence organized on October 11, 2026. Forecast period: October 2026 through September 2027. All amounts are USD.

## Source evidence

- [Original cfo.ai workbook export](torque-financial-plan.xlsx): eight worksheets representing four model pages and supporting inputs. The export is preserved without edits.
- [Plan summary screenshot](screenshots/torque-plan-summary.png)
- [Monthly financial plan screenshot](screenshots/monthly-financial-plan.png)
- [Pricing and cost assumptions screenshot](screenshots/torque-assumptions.png)
- [Unit economics and sensitivity screenshot](screenshots/unit-economics-and-sensitivity.png)

Torque is a prototype that aims to turn GitHub issues into tested, verified pull requests, with bounded recovery retries. Target users are small software teams and open-source maintainers. This model is planning evidence, not evidence of existing customers or working agent performance.

## Proposed pricing

| Tier | Monthly subscription | Included issue runs | Price per extra run |
| --- | ---: | ---: | ---: |
| Maintainer | $29 | 20 | $2.50 |
| Starter | $99 | 60 | $2.25 |
| Team | $399 | 250 | $2.00 |

Prices and usage are assumptions. Included runs are attempted issues, not guaranteed successful pull requests.

## Costs and unit economics

The base case assumes 150,000 input tokens and 20,000 output tokens per attempt, priced at $3 and $15 per million respectively. These are model assumptions, not verified provider quotes or measured usage.

- LLM cost per attempt: $0.75; sandbox compute: $0.06.
- Average recovery retries: 0.60, with each retry costing 50% of the first attempt; 1.30 equivalent attempts per run.
- Cost per attempted issue run: approximately $1.08, including $0.975 in model cost, $0.078 in sandbox cost, and $0.025 for tooling/storage.
- Cost per verified pull request: approximately $1.80 at an assumed 60% success rate, allocating failed-run costs across successes.
- Modeled worst-case variable cost at two recovery retries: approximately $1.65 per run. This is not a measured limit or a token-only budget.
- Blended contribution per customer: approximately $63.19, or 54.2% of revenue.
- Fixed monthly spending: $850 ($150 hosting, $200 software/tools, $500 marketing); modeled break-even is approximately 14 customers at the assumed mix and usage.

## Revenue scenarios

September 2027 projections from the workbook's scenario comparison, rounded for readability:

| Scenario | Paying customers | Monthly revenue | Gross margin before credits | Verified PRs per month | Monthly net cash flow before credits |
| --- | ---: | ---: | ---: | ---: | ---: |
| Conservative | 31 | $3,956 | 23.9% | 869 | $246 |
| Base | 136 | $16,691 | 53.3% | 3,964 | $8,194 |
| Optimistic | 376 | $45,460 | 66.6% | 10,720 | $29,564 |

Fractional customers in the spreadsheet represent expected values, not actual customer counts.

## Cash and runway

Founder-confirmed inputs are starting cash of $0 and unpaid team expenses of $0 per month. With no starting cash, there is no funded runway: early spending requires month-to-month founder funding, reduced spending, or deferred costs. Negative modeled cash balances represent funding gaps, not available cash.

The cfo.ai narrative reports base-case monthly cash flow turning positive in January 2027, a roughly $1.2k cash deficit in December 2026, and approximately $27.8k ending cash in September 2027. It reports approximately $4.5k ending deficit in the conservative case and $102.8k ending cash in the optimistic case.

Source discrepancy: the narrative says conservative cash flow is still negative in month 12, but the workbook's month-12 comparison shows positive monthly net cash flow of $246 before credits. Positive monthly flow can coexist with a cumulative cash deficit. Use the spreadsheet value for monthly cash flow and clarify the narrative in cfo.ai before presenting it as final.

## Credits and sensitivity

The model assumes $45 of temporary, unconfirmed hackathon credits ($20 model budget and $25 AWS allowance), applied only in October 2026. These are usage credits, not starting cash. cfo.ai and Crustdata credit values are modeled at $0 because their dollar values and expiry are unconfirmed. Ongoing costs use paid-rate assumptions; receipt and eligibility must be confirmed before relying on credits.

Heavy usage is the primary modeled risk: full allowance usage reduces contribution margin from approximately 54% to 30%. The narrative reports negative contribution when higher model costs, more retries, lower success, and full usage are combined.

Before launch, measure token consumption, sandbox duration, retry costs, and verified success with actual neatlogs traces; replace assumptions with measured costs and current billing. Enforce explicit retry and dollar budgets, then reassess included allowances and overage pricing.
