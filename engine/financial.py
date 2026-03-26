"""財務計算函數 — IRR、LTV、CAC、回本時間"""

from __future__ import annotations
import numpy as np


def calc_irr(cashflows: np.ndarray, max_iter: int = 100, tol: float = 1e-6) -> float:
    """
    計算內部報酬率（IRR）— 用二分法求解

    Args:
        cashflows: 每季淨現金流陣列（負=支出，正=收入）
        max_iter: 最大迭代次數
        tol: 收斂容忍度

    Returns:
        年化 IRR（小數形式，如 0.08 = 8%）。無法收斂回傳 NaN。
    """
    if len(cashflows) == 0:
        return float('nan')

    # 全正或全負 → 無法計算 IRR
    if np.all(cashflows >= 0) or np.all(cashflows <= 0):
        return float('nan')

    def npv(rate: float) -> float:
        quarters = np.arange(len(cashflows))
        return np.sum(cashflows / (1 + rate) ** quarters)

    # 二分法搜尋季度 IRR
    low, high = -0.5, 2.0

    # 確保 low 和 high 夾住零點
    if npv(low) * npv(high) > 0:
        # 嘗試更寬的範圍
        low, high = -0.99, 10.0
        if npv(low) * npv(high) > 0:
            return float('nan')

    for _ in range(max_iter):
        mid = (low + high) / 2
        val = npv(mid)
        if abs(val) < tol:
            break
        if npv(low) * val < 0:
            high = mid
        else:
            low = mid

    quarterly_irr = (low + high) / 2
    # 轉為年化
    annual_irr = (1 + quarterly_irr) ** 4 - 1
    return annual_irr


def calc_payback_quarter(cumulative_cashflow: np.ndarray) -> int:
    """
    計算回本季度（累計現金流首次轉正的步驟）

    Args:
        cumulative_cashflow: 累計淨現金流陣列

    Returns:
        回本季度索引。永不回本回傳 -1。
    """
    positive_indices = np.where(cumulative_cashflow > 0)[0]
    if len(positive_indices) == 0:
        return -1
    return int(positive_indices[0])


def calc_payback_years(cumulative_cashflow: np.ndarray) -> float:
    """回本時間（年）。永不回本回傳 inf。"""
    q = calc_payback_quarter(cumulative_cashflow)
    if q < 0:
        return float('inf')
    return q / 4


def calc_alternative_investment_line(
    initial_investment: float,
    annual_rate: float,
    n_quarters: int,
) -> np.ndarray:
    """
    計算替代投資對比線（複利成長）

    Args:
        initial_investment: 初始投資金額（正值）
        annual_rate: 年化報酬率
        n_quarters: 季度數

    Returns:
        每季的替代投資累計報酬（作為正值）
    """
    quarterly_rate = (1 + annual_rate) ** 0.25 - 1
    quarters = np.arange(n_quarters)
    return initial_investment * ((1 + quarterly_rate) ** quarters - 1)


def calc_ltv(
    avg_deposit: float,
    monthly_fee: float,
    avg_stay_years: float,
    refund_rate: float,
) -> float:
    """
    每戶終身收入（LTV）

    Args:
        avg_deposit: 平均押金
        monthly_fee: 月費
        avg_stay_years: 平均居住年數
        refund_rate: 有效退費比例

    Returns:
        每戶終身收入（TWD）
    """
    retained_deposit = avg_deposit * (1 - refund_rate)
    total_fees = monthly_fee * 12 * avg_stay_years
    return retained_deposit + total_fees


def calc_cac(
    marketing_monthly: float,
    experience_monthly: float,
    new_move_ins_per_quarter: float,
) -> float:
    """
    每戶招募成本（CAC）

    Args:
        marketing_monthly: 月行銷預算
        experience_monthly: 月體驗行銷成本
        new_move_ins_per_quarter: 每季新入住數

    Returns:
        每戶招募成本（TWD）。無新入住回傳 inf。
    """
    if new_move_ins_per_quarter <= 0:
        return float('inf')
    quarterly_cost = (marketing_monthly + experience_monthly) * 3
    return quarterly_cost / new_move_ins_per_quarter
