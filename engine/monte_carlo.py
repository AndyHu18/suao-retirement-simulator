"""
Monte Carlo wrapper and stress test runner.
"""

import numpy as np
from .model import run_simulation
from .financial import calc_irr
from .parameters import sample_mc_params, STRESS_SCENARIOS


def run_monte_carlo(params, n_runs=1000, seed=42):
    """
    Run N Monte Carlo simulations with parameter perturbation.

    Returns:
        dict with:
            - results: list of SimulationResult
            - irr_values: array of IRR estimates
            - collapse_prob: fraction of runs with negative funds
            - payback_quarters: array of payback times (-1 if never)
            - max_funding_need: array of max negative cumulative CF
            - percentiles: dict of P5/P25/P50/P75/P95 cumulative CF curves
    """
    rng = np.random.RandomState(seed)
    results = []
    n_quarters = 100

    # Collect cumulative CF curves for percentile calculation
    cf_curves = np.zeros((n_runs, n_quarters))

    for i in range(n_runs):
        p = sample_mc_params(params, rng)
        r = run_simulation(p, rng=np.random.RandomState(rng.randint(0, 2**31)))
        results.append(r)
        cf_curves[i] = r.cumulative_cashflow

    # --- Aggregate metrics ---
    # Collapse probability
    collapse_count = sum(1 for r in results if r.failed_quarter >= 0)
    collapse_prob = collapse_count / n_runs

    # P3: Payback = 最後一次從負轉正、之後持續為正的時間點
    payback_quarters = np.full(n_runs, -1, dtype=int)
    for i, r in enumerate(results):
        cf = r.cumulative_cashflow
        # 如果最終為負，永不回本
        if cf[-1] <= 0:
            continue
        # 從後往前找最後一個 <= 0 的位置，它的下一個就是真正回本點
        for t in range(n_quarters - 1, -1, -1):
            if cf[t] <= 0:
                payback_quarters[i] = t + 1
                break
        else:
            # 全程都 > 0（不太可能但防禦性處理）
            payback_quarters[i] = 0

    # Max funding need (most negative point in cumulative CF)
    max_funding_need = np.array([r.cumulative_cashflow.min() for r in results])

    # P2: IRR — 用正確的二分法 calc_irr()，而非簡化 CAGR
    irr_values = np.zeros(n_runs)
    for i, r in enumerate(results):
        # 建構季度現金流陣列：cumulative_cf 的差分
        cf = r.cumulative_cashflow.copy()
        cashflows = np.zeros(n_quarters)
        cashflows[0] = cf[0]  # 第一季（含初始投入）
        cashflows[1:] = np.diff(cf)

        # 最後一季加上殘值（終端價值）
        residual = (r.total_occupied[-1] * params['deposit_amount']
                    * (1 + params['residual_value_appreciation']) ** 25)
        cashflows[-1] += residual

        # 用二分法求季度 IRR，已自動轉年化
        annual_irr = calc_irr(cashflows)
        irr_values[i] = annual_irr if not np.isnan(annual_irr) else 0.0

    # Percentiles
    percentiles = {
        'P5': np.percentile(cf_curves, 5, axis=0),
        'P25': np.percentile(cf_curves, 25, axis=0),
        'P50': np.percentile(cf_curves, 50, axis=0),
        'P75': np.percentile(cf_curves, 75, axis=0),
        'P95': np.percentile(cf_curves, 95, axis=0),
    }

    # Occupancy percentiles
    occ_curves = np.array([r.occupancy_rate for r in results])
    occ_percentiles = {
        'P25': np.percentile(occ_curves, 25, axis=0),
        'P50': np.percentile(occ_curves, 50, axis=0),
        'P75': np.percentile(occ_curves, 75, axis=0),
    }

    return {
        'results': results,
        'cf_curves': cf_curves,
        'irr_values': irr_values,
        'collapse_prob': collapse_prob,
        'payback_quarters': payback_quarters,
        'max_funding_need': max_funding_need,
        'percentiles': percentiles,
        'occ_percentiles': occ_percentiles,
        'n_runs': n_runs,
    }


def extract_metrics(mc_result):
    """Extract key metrics from MC result for comparison."""
    valid_payback = mc_result['payback_quarters'][mc_result['payback_quarters'] > 0]
    n_total = len(mc_result['payback_quarters'])
    n_never = np.sum(mc_result['payback_quarters'] < 0)

    # P3: 如果超過一半跑不回本，payback_median 標記為 -1（未回本）
    if n_never > n_total / 2:
        pb_median = -1
    elif len(valid_payback) > 0:
        pb_median = float(np.median(valid_payback) / 4)
    else:
        pb_median = -1

    return {
        'irr_median': float(np.median(mc_result['irr_values'])),
        'irr_p25': float(np.percentile(mc_result['irr_values'], 25)),
        'irr_p75': float(np.percentile(mc_result['irr_values'], 75)),
        'collapse_prob': mc_result['collapse_prob'],
        'payback_median': pb_median,
        'payback_never_pct': n_never / n_total,  # P3: 永不回本比例
        'max_funding_need': float(np.median(mc_result['max_funding_need'])),
        'final_cf_median': float(np.median(mc_result['cf_curves'][:, -1])),
    }


def run_stress_tests(params, n_runs=200):
    """
    Run all 6 stress scenarios, each with n_runs MC iterations.

    Returns:
        dict of scenario_name -> {metrics, survival_rate, fail_quarter_median}
    """
    results = {}
    for name, scenario in STRESS_SCENARIOS.items():
        rng = np.random.RandomState(42)
        runs = []
        for _ in range(n_runs):
            p = sample_mc_params(params, rng)
            r = run_simulation(
                p,
                rng=np.random.RandomState(rng.randint(0, 2**31)),
                stress_scenario=scenario,
            )
            runs.append(r)

        n_survived = sum(1 for r in runs if r.failed_quarter < 0)
        fail_quarters = [r.failed_quarter for r in runs if r.failed_quarter >= 0]

        results[name] = {
            'description': scenario['description'],
            'survival_rate': n_survived / n_runs,
            'fail_quarter_median': (np.median(fail_quarters)
                                    if fail_quarters else None),
            'n_runs': n_runs,
        }

    return results


def run_comparison_scenarios(base_params, n_runs=500):
    """
    Run 4 comparison scenarios for AI analysis.
    Returns dict of scenario_name -> extract_metrics result.
    """
    scenarios = {}

    # 1. Core package: trust + insurance + medical
    core = dict(base_params)
    core['trust_independent'] = True
    core['trust_mechanism_level'] = 2
    core['insurance_factor'] = 2.0
    core['medical_integration'] = 3
    scenarios['核心配套（信託+保險+醫療）'] = core

    # 2. Trust only
    trust_only = dict(base_params)
    trust_only['trust_independent'] = True
    trust_only['trust_mechanism_level'] = 2
    scenarios['僅加信託'] = trust_only

    # 3. Insurance only
    ins_only = dict(base_params)
    ins_only['insurance_factor'] = 2.0
    scenarios['僅加保險'] = ins_only

    # 4. Scale down
    scale_down = dict(base_params)
    scale_down['phase_units'] = [500] + base_params['phase_units'][1:]
    scenarios['首期縮至500戶'] = scale_down

    results = {}
    for name, p in scenarios.items():
        mc = run_monte_carlo(p, n_runs=n_runs, seed=123)
        results[name] = extract_metrics(mc)

    return results
