"""
Default parameters, preset dictionaries, and Monte Carlo distributions
for the Suao retirement community simulator.
"""

import numpy as np

# ============================================================
# Default Parameters (Suao-calibrated)
# ============================================================

DEFAULT_PARAMS = {
    # --- Development phases ---
    'total_phases': 8,
    'phase_units': [500, 700, 800, 1000, 1000, 1200, 1300, 1500],
    'phase_activation_threshold': 0.80,
    'min_cash_days_for_activation': 250,

    # --- Market ---
    'location': 'suao',
    'target_pool': 35000,
    'market_replenishment_rate': 0.04,
    'base_annual_conversion': 0.005,
    'distance_friction': 0.85,

    # --- Pricing ---
    'deposit_amount': 25_000_000,
    'monthly_fee': 100_000,

    # --- Refund ---
    'refund_percentage': 0.90,
    'refund_condition': 'new_occupant',
    'refund_amortization_years': 0,  # 0 = no amortization

    # --- Operations ---
    'staff_ratio': 0.4,
    'avg_staff_cost_monthly': 50_000,
    'onsen_cost_multiplier': 1.0,
    'suao_labor_premium': 1.15,

    # --- Demand drivers ---
    'insurance_factor': 1.0,
    'insurance_start_quarter': 8,
    'experience_level': 1,
    'experience_cost_monthly': 2_000_000,

    # --- Trust & protection ---
    'trust_independent': False,
    'trust_mechanism_level': 0,

    # --- Medical & care ---
    'medical_integration': 1,
    'medical_external_revenue': False,
    'ccrc_care_ratio': 0.15,

    # --- Onsen ---
    'onsen_level': 0,  # 0=none, 1=basic, 2=premium

    # --- Brand ---
    'initial_brand_trust': 30,
    'debranding_level': 2,
    'brand_aging_countermeasures': [],

    # --- Operations partner ---
    'operational_capability_init': 20,
    'team_quality': 0.8,
    'staff_turnover': 0.15,
    'op_partner_revenue_share': 0.0,

    # --- External ---
    'initial_cultural_acceptance': 0.05,
    'annual_acceptance_growth': 0.02,
    'recession_annual_prob': 0.05,
    'recession_severity': 0.6,
    'alternative_investment_rate': 0.06,
    'residual_value_appreciation': 0.03,

    # --- Capital ---
    'total_budget': 80_000_000_000,
    'annual_cost_of_capital': 0.035,
    'payback_tolerance_years': 20,
    'refinance_risk': False,

    # --- Marketing ---
    'marketing_budget_monthly': 5_000_000,

    # --- H Hotel ---
    'h_hotel_active': True,
    'h_hotel_annual_contacts': 6000,
    'h_hotel_inquiry_rate': 0.03,
    'h_hotel_close_rate': 0.12,

    # --- Competitor ---
    'competitor_active': False,
    'competitor_year': 5,
    'competitor_intensity': 'medium',

    # --- Regulation ---
    'regulation_level': 0,
    'regulation_compliance_cost': 0,

    # --- Revenue streams ---
    'revenue_streams': [],

    # --- Macro volatility preset ---
    'macro_volatility': 'stable',

    # --- 模型假設（FIX_GUIDE P1-P10 引入，標 ⚠️）---
    'liquidity_crisis_quarters': 4,       # P1: 流動性危機門檻（季）⚠️
    'brand_base_decay': 0.5,              # P6: 品牌信任季度衰減 ⚠️
    'fee_inflation_ratio': 0.0,           # P7: 月費漲幅/成本通膨比 ⚠️（預設 0=不漲）
    'ops_capability_floor': 10,           # P8: 營運能力下限 ⚠️
    # --- MC 擾動控制 ---
    'mc_uncertainty_level': 1.0,          # 整體不確定性倍率（0.5/1.0/1.5）
}


# ============================================================
# Preset Dictionaries
# ============================================================

CAPITAL_STRUCTURE_PRESETS = {
    '自有資金': {
        'total_budget': 50_000_000_000,
        'annual_cost_of_capital': 0.03,
        'payback_tolerance_years': 10,
        'refinance_risk': False,
    },
    '壽險合作': {
        'total_budget': 130_000_000_000,
        'annual_cost_of_capital': 0.025,
        'payback_tolerance_years': 30,
        'refinance_risk': False,
    },
    '專案融資': {
        'total_budget': 80_000_000_000,
        'annual_cost_of_capital': 0.05,
        'payback_tolerance_years': 7,
        'refinance_risk': True,
    },
    '混合模式': {
        'total_budget': 100_000_000_000,
        'annual_cost_of_capital': 0.035,
        'payback_tolerance_years': 20,
        'refinance_risk': False,
    },
}

DEPOSIT_REFUND_PRESETS = {
    '全額可退90%（需新住戶入住）': {
        'refund_percentage': 0.90,
        'refund_condition': 'new_occupant',
        'refund_amortization_years': 0,
        'deposit_amount': 25_000_000,
        'monthly_fee': 100_000,
    },
    '部分可退50%（退出即退）': {
        'refund_percentage': 0.50,
        'refund_condition': 'on_exit',
        'refund_amortization_years': 0,
        'deposit_amount': 25_000_000,
        'monthly_fee': 100_000,
    },
    '漸進償卻（5年歸零）': {
        'refund_percentage': 0.70,
        'refund_condition': 'on_exit',
        'refund_amortization_years': 5,
        'deposit_amount': 25_000_000,
        'monthly_fee': 100_000,
    },
    '不可退但低押金': {
        'refund_percentage': 0.0,
        'refund_condition': 'on_exit',
        'refund_amortization_years': 0,
        'deposit_amount': 8_000_000,
        'monthly_fee': 130_000,
    },
}

EXPERIENCE_PRESETS = {
    '基礎（樣品屋+說明會）': {
        'experience_level': 0.5,
        'experience_cost_monthly': 2_000_000,
        'h_hotel_active': False,
    },
    '中度（H會館短住+跟進）': {
        'experience_level': 1.5,
        'experience_cost_monthly': 8_000_000,
        'h_hotel_active': True,
    },
    '深度（度假轉化）': {
        'experience_level': 2.5,
        'experience_cost_monthly': 20_000_000,
        'h_hotel_active': True,
    },
    '極致（沉浸體驗村）': {
        'experience_level': 3.0,
        'experience_cost_monthly': 50_000_000,
        'h_hotel_active': True,
    },
}

MEDICAL_PRESETS = {
    '基本診所': {
        'medical_integration': 1,
        'medical_setup_cost': 50_000_000,
        'medical_monthly_cost': 3_000_000,
        'medical_boost': 1.0,
        'medical_trust_bonus': 0,
    },
    '區域醫院合作（聖母/陽大）': {
        'medical_integration': 2,
        'medical_setup_cost': 200_000_000,
        'medical_monthly_cost': 8_000_000,
        'medical_boost': 1.15,
        'medical_trust_bonus': 5,
    },
    '醫學中心+園區二級醫院': {
        'medical_integration': 3,
        'medical_setup_cost': 800_000_000,
        'medical_monthly_cost': 25_000_000,
        'medical_boost': 1.30,
        'medical_trust_bonus': 15,
    },
}

ONSEN_PRESETS = {
    '無': {
        'onsen_level': 0,
        'onsen_cost_multiplier': 1.0,
        'onsen_setup_cost': 0,
        'onsen_brand_boost': 0.0,
        'onsen_external_revenue': 0,
    },
    '基礎（公共浴場+SPA）': {
        'onsen_level': 1,
        'onsen_cost_multiplier': 1.5,
        'onsen_setup_cost': 300_000_000,
        'onsen_brand_boost': 0.10,
        'onsen_external_revenue': 2_000_000,
    },
    '高規格（+個人湯屋+對外健檢）': {
        'onsen_level': 2,
        'onsen_cost_multiplier': 1.8,
        'onsen_setup_cost': 800_000_000,
        'onsen_brand_boost': 0.20,
        'onsen_external_revenue': 10_000_000,
    },
}

OPERATION_PARTNER_PRESETS = {
    '自行營運': {
        'operational_capability_init': 20,
        'team_quality': 0.8,
        'staff_turnover': 0.15,
        'op_partner_revenue_share': 0.0,
    },
    '外包物業': {
        'operational_capability_init': 35,
        'team_quality': 0.5,
        'staff_turnover': 0.20,
        'op_partner_revenue_share': 0.0,
    },
    '專業營運商合作': {
        'operational_capability_init': 60,
        'team_quality': 1.2,
        'staff_turnover': 0.10,
        'op_partner_revenue_share': 0.05,
    },
    '合資營運（三權分立）': {
        'operational_capability_init': 55,
        'team_quality': 1.5,
        'staff_turnover': 0.08,
        'op_partner_revenue_share': 0.08,
    },
}

REGULATION_PRESETS = {
    '維持現狀（無專法）': {
        'regulation_level': 0,
        'regulation_compliance_cost': 0,
    },
    '5年內基本規範': {
        'regulation_level': 1,
        'regulation_compliance_cost': 10_000_000,
    },
    '10年內佛羅里達級': {
        'regulation_level': 3,
        'regulation_compliance_cost': 30_000_000,
    },
}

MACRO_PRESETS = {
    '穩定（3%/年）': {'recession_annual_prob': 0.03, 'recession_severity': 0.7},
    '溫和（5%/年）': {'recession_annual_prob': 0.05, 'recession_severity': 0.6},
    '高波動（8%/年）': {'recession_annual_prob': 0.08, 'recession_severity': 0.4},
}

BRAND_AGING_OPTIONS = {
    '序列開發（每7-10年新產品線）': {
        'decay_reduction': 0.30,
        'age_reduction': 3,
        'cost_per_cycle': 500_000_000,
    },
    '物理區隔（自立/介護分開）': {
        'decay_reduction': 0.20,
        'age_reduction': 0,
        'cost_per_cycle': 0,
    },
    '年齡漸進式定價': {
        'decay_reduction': 0.0,
        'age_reduction': 5,
        'cost_per_cycle': 0,
    },
    '彈性會員層級（短住/度假）': {
        'decay_reduction': 0.15,
        'age_reduction': 0,
        'cost_per_cycle': 0,
    },
    '社區活動持續投入': {
        'decay_reduction': 0.10,
        'age_reduction': 0,
        'cost_per_cycle': 0,
    },
}

REVENUE_STREAM_OPTIONS = {
    '商業地產出租': {
        'monthly_revenue': 8_000_000,
        'setup_cost': 500_000_000,
        'ramp_quarters': 8,
        'scales_with_occupancy': True,
        'requires_onsen': False,
        'requires_ccrc': False,
        'requires_trust': 0,
        'cold_start_benefit': False,
    },
    '醫療健檢對外': {
        'monthly_revenue': 5_000_000,
        'setup_cost': 200_000_000,
        'ramp_quarters': 4,
        'scales_with_occupancy': False,
        'requires_onsen': False,
        'requires_ccrc': False,
        'requires_trust': 0,
        'cold_start_benefit': False,
    },
    '度假旅居（樂養）': {
        'monthly_revenue': 12_000_000,
        'setup_cost': 300_000_000,
        'ramp_quarters': 6,
        'scales_with_occupancy': False,
        'requires_onsen': False,
        'requires_ccrc': False,
        'requires_trust': 0,
        'cold_start_benefit': True,
    },
    '冷泉SPA對外': {
        'monthly_revenue': 10_000_000,
        'setup_cost': 400_000_000,
        'ramp_quarters': 4,
        'scales_with_occupancy': False,
        'requires_onsen': True,
        'requires_ccrc': False,
        'requires_trust': 0,
        'cold_start_benefit': False,
    },
    '活動場地出租': {
        'monthly_revenue': 3_000_000,
        'setup_cost': 150_000_000,
        'ramp_quarters': 4,
        'scales_with_occupancy': False,
        'requires_onsen': False,
        'requires_ccrc': False,
        'requires_trust': 0,
        'cold_start_benefit': False,
    },
    '長照外部接案': {
        'monthly_revenue': 6_000_000,
        'setup_cost': 100_000_000,
        'ramp_quarters': 8,
        'scales_with_occupancy': False,
        'requires_onsen': False,
        'requires_ccrc': True,
        'requires_trust': 0,
        'cold_start_benefit': False,
    },
    '品牌授權/顧問': {
        'monthly_revenue': 2_000_000,
        'setup_cost': 20_000_000,
        'ramp_quarters': 12,
        'scales_with_occupancy': False,
        'requires_onsen': False,
        'requires_ccrc': False,
        'requires_trust': 60,
        'cold_start_benefit': False,
    },
}


# ============================================================
# Mortality & Exit Rate Tables
# ============================================================

AGE_MORTALITY_TABLE = {
    65: 0.012, 70: 0.020, 75: 0.035,
    80: 0.060, 85: 0.100, 90: 0.160,
}

AGE_CARE_TRANSFER_TABLE = {
    75: 0.02, 80: 0.05, 85: 0.10, 90: 0.15,
}

ANNUAL_VOLUNTARY_EXIT_RATE = 0.03


# ============================================================
# Monte Carlo Distribution Samplers
# ============================================================

def sample_mc_params(params, rng):
    """
    Given base params and an RNG, return a perturbed copy
    with alpha/beta/gamma noise applied.

    三級擾動體系（規格書定義）：
      α 級 σ=0.05 → ±15%（穩定參數）
      β 級 σ=0.15~0.20 → ±30%（有明確波動）
      γ 級 σ=0.3~0.4 → ±50%（高度不確定）

    所有 sigma 受 mc_uncertainty_level 倍率控制。
    """
    p = dict(params)
    u = p.get('mc_uncertainty_level', 1.0)

    # === α 級（±15%）===
    p['monthly_fee'] = int(p['monthly_fee'] * rng.normal(1.0, 0.05 * u))
    p['staff_ratio'] = max(0.1, p['staff_ratio'] * rng.normal(1.0, 0.05 * u))
    p['refund_percentage'] = min(1.0, max(0.3,
        p['refund_percentage'] * rng.normal(1.0, 0.05 * u)))

    # === β 級（±30%）===
    p['base_annual_conversion'] = max(0.001,
        p['base_annual_conversion'] * rng.normal(1.0, 0.20 * u))
    p['total_budget'] = p['total_budget'] * rng.normal(1.0, 0.15 * u)

    # === γ 級（±50%）===
    if p['insurance_factor'] > 1.0:
        p['insurance_factor'] = max(1.0,
            p['insurance_factor'] * rng.lognormal(0, 0.3 * u))
    if p['h_hotel_active']:
        p['h_hotel_close_rate'] = max(0.01,
            p['h_hotel_close_rate'] * rng.lognormal(0, 0.4 * u))
    p['annual_cost_of_capital'] = max(0.01,
        p['annual_cost_of_capital'] * rng.lognormal(0, 0.3 * u))

    # === 宏觀衝擊相關性（規格書機制：閾值觸發，~7% 機率）===
    macro_shock = rng.normal(0, 1)
    if macro_shock < -1.5:
        p['base_annual_conversion'] *= (1 + 0.5 * macro_shock)
        p['monthly_fee'] = int(p['monthly_fee'] * (1 + 0.1 * macro_shock))
        p['annual_cost_of_capital'] *= (1 - 0.2 * macro_shock)

    return p


# ============================================================
# Stress Test Scenarios
# ============================================================

STRESS_SCENARIOS = {
    '溫和衰退': {
        'description': '第3年，macro=0.7，持續6季',
        'trigger_quarter': 12,
        'duration': 6,
        'macro_override': 0.7,
        'extra_exit_rate': 0.0,
        'trust_shock': 0,
        'new_move_in_zero': False,
        'cost_inflation': 0.0,
    },
    '嚴重衰退': {
        'description': '第3年，macro=0.4 + 15%退費潮，持續8季',
        'trigger_quarter': 12,
        'duration': 8,
        'macro_override': 0.4,
        'extra_exit_rate': 0.15,
        'trust_shock': 0,
        'new_move_in_zero': False,
        'cost_inflation': 0.0,
    },
    '信任危機': {
        'description': '第2年，新入住歸零2季 + 20%退費 + 信任-40',
        'trigger_quarter': 8,
        'duration': 2,
        'macro_override': 1.0,
        'extra_exit_rate': 0.20,
        'trust_shock': -40,
        'new_move_in_zero': True,
        'cost_inflation': 0.0,
    },
    '成本通膨': {
        'description': '第4年，成本年增8%，持續12季',
        'trigger_quarter': 16,
        'duration': 12,
        'macro_override': 1.0,
        'extra_exit_rate': 0.0,
        'trust_shock': 0,
        'new_move_in_zero': False,
        'cost_inflation': 0.08,
    },
    '複合災難': {
        'description': '嚴重衰退+成本通膨同時',
        'trigger_quarter': 12,
        'duration': 8,
        'macro_override': 0.4,
        'extra_exit_rate': 0.15,
        'trust_shock': 0,
        'new_move_in_zero': False,
        'cost_inflation': 0.08,
    },
    '無新血存活': {
        'description': '第5年起新入住永久歸零',
        'trigger_quarter': 20,
        'duration': 80,
        'macro_override': 1.0,
        'extra_exit_rate': 0.0,
        'trust_shock': 0,
        'new_move_in_zero': True,
        'cost_inflation': 0.0,
    },
}
