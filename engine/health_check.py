"""
Health check panel: 12 automated checks + 4 contradiction detectors.
All checks are pure functions that return structured results.
"""

import numpy as np


def run_health_checks(mc_result, params, stress_results=None):
    """
    Run 12 automated health checks on MC simulation results.

    Returns:
        list of dicts, each: {id, name, status: 'pass'|'warn'|'fail',
                              value, threshold, explanation}
    """
    metrics = mc_result['_metrics']
    results_list = mc_result['results']
    n_runs = mc_result['n_runs']
    checks = []

    # --- C01: IRR positive ---
    irr = metrics['irr_median']
    checks.append({
        'id': 'C01', 'name': '年化報酬率為正',
        'status': 'pass' if irr > 0 else ('warn' if irr > -0.03 else 'fail'),
        'value': f'{irr:.1%}',
        'threshold': '>0%',
        'explanation': '報酬率為負代表 25 年下來是虧損的' if irr <= 0 else '報酬率為正',
    })

    # --- C02: Collapse probability ---
    cp = metrics['collapse_prob']
    checks.append({
        'id': 'C02', 'name': '崩潰機率低於 20%',
        'status': 'pass' if cp < 0.10 else ('warn' if cp < 0.20 else 'fail'),
        'value': f'{cp:.1%}',
        'threshold': '<20%',
        'explanation': '超過 20% 代表五次裡至少一次會燒完所有資金',
    })

    # --- C03: Payback within tolerance ---
    pb = metrics['payback_median']
    tol = params['payback_tolerance_years']
    checks.append({
        'id': 'C03', 'name': f'回本時間 ≤ {tol} 年',
        'status': 'pass' if 0 < pb <= tol else ('warn' if 0 < pb <= tol * 1.5 else 'fail'),
        'value': f'{pb:.1f}年' if pb > 0 else '未回本',
        'threshold': f'≤{tol}年',
        'explanation': '未能在容忍期限內回本' if pb <= 0 or pb > tol else '回本時間在容忍範圍內',
    })

    # --- C04: All phases activated ---
    # Check median run
    median_idx = np.argsort(mc_result['cf_curves'][:, -1])[n_runs // 2]
    r = results_list[median_idx]
    n_activated = len(r.phase_activations)
    n_total = params['total_phases']
    checks.append({
        'id': 'C04', 'name': f'全部 {n_total} 期啟動',
        'status': 'pass' if n_activated == n_total else (
            'warn' if n_activated >= n_total * 0.5 else 'fail'),
        'value': f'{n_activated}/{n_total} 期',
        'threshold': f'{n_total}/{n_total}',
        'explanation': f'只有 {n_activated} 期啟動，{n_total - n_activated} 期因入住率未達門檻被凍結'
        if n_activated < n_total else '全部分期順利啟動',
    })

    # --- C05: Occupancy P50 > 80% at year 10 ---
    occ_pcts = mc_result['occ_percentiles']
    y10_occ = occ_pcts['P50'][39] if len(occ_pcts['P50']) > 39 else 0
    checks.append({
        'id': 'C05', 'name': '第 10 年入住率 > 80%',
        'status': 'pass' if y10_occ > 0.80 else ('warn' if y10_occ > 0.70 else 'fail'),
        'value': f'{y10_occ:.0%}',
        'threshold': '>80%',
        'explanation': '第 10 年入住率偏低代表需求引擎不足',
    })

    # --- C06: Brand vitality P50 > 50 at year 15 ---
    bv_vals = [results_list[i].brand_vitality[59] for i in range(min(n_runs, 100))]
    bv_median = float(np.median(bv_vals)) if bv_vals else 50
    checks.append({
        'id': 'C06', 'name': '第 15 年品牌活力 > 50',
        'status': 'pass' if bv_median > 50 else ('warn' if bv_median > 40 else 'fail'),
        'value': f'{bv_median:.0f}/100',
        'threshold': '>50',
        'explanation': '品牌活力低於 50 代表社區開始「變老」',
    })

    # --- C07: Days cash on hand > 180 ---
    dcoh_vals = [results_list[i].emergency_reserve[-1] /
                 max(1, results_list[i].quarterly_cost[-1] / 90)
                 for i in range(min(n_runs, 100))]
    dcoh_median = float(np.median(dcoh_vals))
    checks.append({
        'id': 'C07', 'name': '現金儲備天數 > 180 天',
        'status': 'pass' if dcoh_median > 250 else ('warn' if dcoh_median > 180 else 'fail'),
        'value': f'{dcoh_median:.0f}天',
        'threshold': '>180天',
        'explanation': '低於 180 天代表應急能力嚴重不足',
    })

    # --- C08: Refund backlog manageable ---
    backlog_vals = [results_list[i].refund_backlog[-1] for i in range(min(n_runs, 100))]
    backlog_median = float(np.median(backlog_vals))
    checks.append({
        'id': 'C08', 'name': '退費積壓可控',
        'status': 'pass' if backlog_median < 1e8 else (
            'warn' if backlog_median < 5e8 else 'fail'),
        'value': f'{backlog_median/1e8:.1f}億',
        'threshold': '<1億',
        'explanation': '有大量退費無法兌現，會侵蝕品牌信任',
    })

    # --- C09: Market pool > 30% at year 25 ---
    pool_vals = [results_list[i].market_pool_remaining[-1] for i in range(min(n_runs, 100))]
    pool_median = float(np.median(pool_vals))
    pool_pct = pool_median / params['target_pool']
    checks.append({
        'id': 'C09', 'name': '市場容量未耗盡',
        'status': 'pass' if pool_pct > 0.30 else ('warn' if pool_pct > 0.15 else 'fail'),
        'value': f'{pool_pct:.0%} 剩餘',
        'threshold': '>30%',
        'explanation': '市場快被吃完了，後面幾期會找不到人',
    })

    # --- C10: Stress tests survival >= 4/6 ---
    if stress_results:
        n_passed = sum(1 for d in stress_results.values() if d['survival_rate'] > 0.50)
        checks.append({
            'id': 'C10', 'name': '壓力測試通過 ≥ 4/6',
            'status': 'pass' if n_passed >= 5 else ('warn' if n_passed >= 4 else 'fail'),
            'value': f'{n_passed}/6 通過',
            'threshold': '≥4/6',
            'explanation': '太多壓力情境撐不過代表安全邊際不足',
        })
    else:
        checks.append({
            'id': 'C10', 'name': '壓力測試通過 ≥ 4/6',
            'status': 'warn',
            'value': '未執行',
            'threshold': '≥4/6',
            'explanation': '尚未執行壓力測試',
        })

    # --- C11: Occupancy never negative or > 100% ---
    occ_ok = all(
        np.all(results_list[i].occupancy_rate >= 0)
        and np.all(results_list[i].occupancy_rate <= 1.001)
        for i in range(min(n_runs, 50))
    )
    checks.append({
        'id': 'C11', 'name': '入住率在 0-100% 範圍',
        'status': 'pass' if occ_ok else 'fail',
        'value': '正常' if occ_ok else '異常',
        'threshold': '0-100%',
        'explanation': '模型計算出不合理的入住率' if not occ_ok else '模型數值正常',
    })

    # --- C12: Exits <= Occupied ---
    exit_ok = all(
        np.all(results_list[i].exits <= results_list[i].total_occupied + 1)
        for i in range(min(n_runs, 50))
    )
    checks.append({
        'id': 'C12', 'name': '退出數 ≤ 入住數',
        'status': 'pass' if exit_ok else 'fail',
        'value': '正常' if exit_ok else '異常',
        'threshold': '退出 ≤ 入住',
        'explanation': '退出人數超過入住人數代表模型有 bug' if not exit_ok else '模型邏輯正常',
    })

    return checks


def detect_contradictions(mc_result, params, stress_results=None):
    """
    Detect 4 specific contradiction patterns that confuse users.

    Returns:
        list of dicts: {pattern, icon, message}
    """
    metrics = mc_result['_metrics']
    contradictions = []

    irr = metrics['irr_median']
    cp = metrics['collapse_prob']

    # Pattern 1: IRR < 0 but collapse < 5%
    if irr < 0 and cp < 0.05:
        contradictions.append({
            'pattern': 'irr_neg_collapse_low',
            'icon': '💡',
            'message': (
                f'崩潰率只有 {cp:.1%}，但年化報酬率是 {irr:.1%}。'
                '崩潰率低 ≠ 沒問題——不會突然倒閉但持續虧損，'
                '像慢慢漏水而非水管爆裂。'
            ),
        })

    # Pattern 2: Not all phases activated
    median_idx = np.argsort(mc_result['cf_curves'][:, -1])[mc_result['n_runs'] // 2]
    r = mc_result['results'][median_idx]
    n_activated = len(r.phase_activations)
    n_total = params['total_phases']
    total_planned = sum(params['phase_units'])
    total_actual = sum(params['phase_units'][i] for i in range(n_activated))

    if n_activated < n_total:
        contradictions.append({
            'pattern': 'phases_not_all_activated',
            'icon': '💡',
            'message': (
                f'8,000 戶計畫在目前配置下只能完成 {total_actual:,} 戶。'
                f'後續第 {n_activated + 1}-{n_total} 期因入住率未達 '
                f'{params["phase_activation_threshold"]:.0%} 門檻被凍結。'
            ),
        })

    # Pattern 3: LTV/CAC > 5 but IRR < 0
    # Estimate LTV/CAC
    avg_stay = 10
    ltv = (params['monthly_fee'] * 12 * avg_stay
           + params['deposit_amount'] * (1 - params['refund_percentage'] * 0.5))
    total_movin = r.new_move_ins.sum()
    total_mkt = params['marketing_budget_monthly'] * 12 * 25
    cac = total_mkt / max(1, total_movin)
    ltv_cac = ltv / max(1, cac) if cac > 0 else 0

    if ltv_cac > 5 and irr < 0:
        contradictions.append({
            'pattern': 'ltv_high_irr_low',
            'icon': '💡',
            'message': (
                f'每戶經濟指標健康（LTV/CAC = {ltv_cac:.1f}x），'
                f'但整體報酬率是 {irr:.1%}。'
                '問題不在每戶收費，而在入住量不足——'
                '單戶能賺錢但來的人太少。'
            ),
        })

    # Pattern 4: Stress tests all green but IRR < 0
    if stress_results:
        all_passed = all(d['survival_rate'] > 0.80 for d in stress_results.values())
        if all_passed and irr < 0:
            contradictions.append({
                'pattern': 'stress_green_irr_neg',
                'icon': '💡',
                'message': (
                    '壓力測試全部通過，但年化報酬率為負。'
                    '全部通過是因為規模小到燒不完錢，不是因為專案健康。'
                    '安全 ≠ 賺錢。'
                ),
            })

    return contradictions


def sanity_check(mc_result, params):
    """
    Common-sense verification: compare model output with manual calculation.

    Returns:
        dict with expected vs actual and match status
    """
    median_idx = np.argsort(mc_result['cf_curves'][:, -1])[mc_result['n_runs'] // 2]
    r = mc_result['results'][median_idx]

    # Pick a mid-simulation quarter (e.g., t=40, year 10) where things are stable
    t = 40
    occupied = r.total_occupied[t]
    monthly_fee = params['monthly_fee']

    expected_quarterly_fee = occupied * monthly_fee * 3
    actual_quarterly_fee = r.cf_monthly_fee[t] if hasattr(r, 'cf_monthly_fee') else r.quarterly_revenue[t]

    match = abs(expected_quarterly_fee - actual_quarterly_fee) / max(1, expected_quarterly_fee) < 0.15

    return {
        'quarter': t,
        'year': t / 4,
        'occupied': int(occupied),
        'monthly_fee': monthly_fee,
        'expected_quarterly_fee': expected_quarterly_fee,
        'actual_quarterly_fee': actual_quarterly_fee,
        'match': match,
    }
