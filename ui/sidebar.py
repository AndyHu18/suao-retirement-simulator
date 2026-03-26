"""
Sidebar controls: 5 groups of strategy parameters.
Quick mode = 5 dropdowns with presets.
Advanced mode = presets + expandable sliders.
"""

import streamlit as st
from engine.parameters import (
    DEFAULT_PARAMS,
    CAPITAL_STRUCTURE_PRESETS,
    DEPOSIT_REFUND_PRESETS,
    EXPERIENCE_PRESETS,
    MEDICAL_PRESETS,
    ONSEN_PRESETS,
    OPERATION_PARTNER_PRESETS,
    REGULATION_PRESETS,
    MACRO_PRESETS,
    BRAND_AGING_OPTIONS,
    REVENUE_STREAM_OPTIONS,
)


def render_sidebar():
    """Render sidebar controls and return params dict."""
    params = dict(DEFAULT_PARAMS)

    with st.sidebar:
        st.title("🏘️ 策略控制面板")

        advanced = st.toggle("進階模式", value=False,
                             help="展開所有底層參數滑桿")

        mc_runs = st.select_slider(
            "模擬次數",
            options=[100, 500, 1000, 5000],
            value=1000,
            help="蒙地卡羅模擬次數，越多越準但越慢",
        )
        params['_mc_runs'] = mc_runs

        st.divider()

        # ==========================================
        # Group 1: Capital & Financial Strategy
        # ==========================================
        st.subheader("💰 資本與財務策略")

        # 1.1 Capital structure
        cap_choice = st.selectbox(
            "資本結構",
            list(CAPITAL_STRUCTURE_PRESETS.keys()),
            index=3,  # default: mixed
            help="決定總預算、資金成本和回收期",
        )
        cap_preset = CAPITAL_STRUCTURE_PRESETS[cap_choice]

        if advanced:
            with st.expander(f"底層參數（預設：{cap_choice}）"):
                params['total_budget'] = st.slider(
                    "總預算（億）",
                    300, 1500,
                    int(cap_preset['total_budget'] / 1e8),
                    step=50,
                ) * 1e8
                params['annual_cost_of_capital'] = st.slider(
                    "年化資金成本（%）",
                    1.0, 8.0,
                    cap_preset['annual_cost_of_capital'] * 100,
                    step=0.5,
                ) / 100
                params['payback_tolerance_years'] = st.slider(
                    "回收期容忍（年）",
                    5, 35,
                    cap_preset['payback_tolerance_years'],
                )
                params['refinance_risk'] = st.checkbox(
                    "有轉貸風險",
                    value=cap_preset['refinance_risk'],
                )
        else:
            params.update(cap_preset)

        # 1.2 Deposit refund mode
        dep_choice = st.selectbox(
            "押金退還模式",
            list(DEPOSIT_REFUND_PRESETS.keys()),
            index=0,
            help="影響擠兌風險的核心因素",
        )
        dep_preset = DEPOSIT_REFUND_PRESETS[dep_choice]

        if advanced:
            with st.expander(f"底層參數（預設：{dep_choice}）"):
                params['deposit_amount'] = st.slider(
                    "押金金額（萬）",
                    500, 4000,
                    int(dep_preset['deposit_amount'] / 1e4),
                    step=100,
                ) * 1e4
                params['monthly_fee'] = st.slider(
                    "月費（萬）",
                    5, 20,
                    int(dep_preset['monthly_fee'] / 1e4),
                ) * 1e4
                params['refund_percentage'] = st.slider(
                    "退費比例（%）",
                    0, 100,
                    int(dep_preset['refund_percentage'] * 100),
                    step=5,
                ) / 100
                params['refund_amortization_years'] = st.slider(
                    "償卻年限（0=無償卻）",
                    0, 10,
                    dep_preset['refund_amortization_years'],
                )
        else:
            params.update(dep_preset)

        # 1.3 Trust protection level
        trust_options = {
            '無信託': 0,
            '基本信託': 1,
            '獨立信託+審批': 2,
            '北卡級完全保護': 3,
        }
        trust_choice = st.selectbox(
            "押金保護等級",
            list(trust_options.keys()),
            index=0,
            help="等級越高，住戶資金越安全，品牌信任加分越多",
        )
        params['trust_mechanism_level'] = trust_options[trust_choice]
        params['trust_independent'] = params['trust_mechanism_level'] >= 2

        st.divider()

        # ==========================================
        # Group 2: Demand Engine
        # ==========================================
        st.subheader("🚀 需求引擎策略")

        # 2.1 Insurance binding
        ins_on = st.checkbox("保險綁定", value=False)
        if ins_on:
            if advanced:
                params['insurance_factor'] = st.slider(
                    "保險轉化強度", 1.0, 3.0, 2.0, step=0.1)
                params['insurance_start_quarter'] = st.slider(
                    "上線季度", 1, 20, 8)
            else:
                params['insurance_factor'] = 2.0
                params['insurance_start_quarter'] = 8
        else:
            params['insurance_factor'] = 1.0

        # 2.2 Experience marketing
        exp_choice = st.selectbox(
            "體驗行銷策略",
            list(EXPERIENCE_PRESETS.keys()),
            index=1,
            help="從說明會到沉浸式體驗村",
        )
        exp_preset = EXPERIENCE_PRESETS[exp_choice]

        if advanced:
            with st.expander(f"底層參數（預設：{exp_choice}）"):
                params['experience_level'] = st.slider(
                    "體驗深度", 0.0, 3.0,
                    exp_preset['experience_level'], step=0.5)
                params['experience_cost_monthly'] = st.slider(
                    "體驗行銷月費（萬）", 50, 5000,
                    int(exp_preset['experience_cost_monthly'] / 1e4),
                    step=50) * 1e4
        else:
            params['experience_level'] = exp_preset['experience_level']
            params['experience_cost_monthly'] = exp_preset['experience_cost_monthly']

        params['h_hotel_active'] = exp_preset.get('h_hotel_active',
                                                   params['h_hotel_active'])

        # 2.3 H Hotel
        if params['h_hotel_active']:
            if advanced:
                with st.expander("H 會館參數"):
                    params['h_hotel_annual_contacts'] = st.slider(
                        "年度客群", 2000, 15000, 6000, step=500)
                    params['h_hotel_inquiry_rate'] = st.slider(
                        "諮詢率（%）", 1.0, 10.0, 3.0, step=0.5) / 100
                    params['h_hotel_close_rate'] = st.slider(
                        "成交率（%）", 5.0, 25.0, 12.0, step=1.0) / 100

        # 2.4 Marketing budget
        if advanced:
            params['marketing_budget_monthly'] = st.slider(
                "行銷預算（萬/月）", 100, 5000, 500, step=100) * 1e4

        st.divider()

        # ==========================================
        # Group 3: Product & Operations
        # ==========================================
        st.subheader("🏥 產品與營運策略")

        # 3.1 CCRC care ratio
        if advanced:
            params['ccrc_care_ratio'] = st.slider(
                "CCRC 照護配比（%）", 0, 30, 15) / 100

        # 3.2 Medical integration
        med_choice = st.selectbox(
            "醫療整合",
            list(MEDICAL_PRESETS.keys()),
            index=0,
            help="從基本診所到醫學中心",
        )
        med_preset = MEDICAL_PRESETS[med_choice]
        params['medical_integration'] = med_preset['medical_integration']

        if advanced:
            params['medical_external_revenue'] = st.checkbox(
                "醫療對外營業", value=False)

        # 3.3 Onsen
        onsen_choice = st.selectbox(
            "冷泉溫泉規格",
            list(ONSEN_PRESETS.keys()),
            index=0,
            help="蘇澳碳酸冷泉 — 全球僅兩處",
        )
        onsen_preset = ONSEN_PRESETS[onsen_choice]
        params['onsen_level'] = onsen_preset['onsen_level']
        params['onsen_cost_multiplier'] = onsen_preset['onsen_cost_multiplier']

        # 3.4 Operation partner
        op_choice = st.selectbox(
            "營運夥伴",
            list(OPERATION_PARTNER_PRESETS.keys()),
            index=0,
            help="影響營運能力的建構速度",
        )
        op_preset = OPERATION_PARTNER_PRESETS[op_choice]

        if advanced:
            with st.expander(f"底層參數（預設：{op_choice}）"):
                params['operational_capability_init'] = st.slider(
                    "初始營運能力", 10, 80,
                    op_preset['operational_capability_init'])
                params['team_quality'] = st.slider(
                    "團隊品質", 0.3, 2.0,
                    op_preset['team_quality'], step=0.1)
                params['staff_turnover'] = st.slider(
                    "人員流動率（%）", 5.0, 25.0,
                    op_preset['staff_turnover'] * 100, step=1.0) / 100
                params['op_partner_revenue_share'] = st.slider(
                    "營運分潤（%）", 0.0, 15.0,
                    op_preset['op_partner_revenue_share'] * 100, step=1.0) / 100
        else:
            params.update(op_preset)

        # 3.5 Debranding
        if advanced:
            params['debranding_level'] = st.slider(
                "去標籤化程度", 1, 3, 2,
                help="影響轉化率但需要醫療配套")

        st.divider()

        # ==========================================
        # Group 4: Development Pace
        # ==========================================
        st.subheader("📐 開發節奏策略")

        # 4.1 Phase sizes
        if advanced:
            with st.expander("各期規模（戶）"):
                phase_units = []
                defaults = DEFAULT_PARAMS['phase_units']
                for i in range(8):
                    u = st.number_input(
                        f"第 {i+1} 期",
                        min_value=200, max_value=2000,
                        value=defaults[i], step=100,
                        key=f'phase_{i}',
                    )
                    phase_units.append(u)
                params['phase_units'] = phase_units

        # 4.2 Activation conditions
        if advanced:
            with st.expander("啟動條件"):
                params['phase_activation_threshold'] = st.slider(
                    "入住率門檻（%）", 60, 95, 80) / 100
                params['min_cash_days_for_activation'] = st.slider(
                    "最低儲備天數", 100, 500, 250, step=50)

        # 4.3 Brand aging countermeasures
        if advanced:
            selected_cm = st.multiselect(
                "品牌老化對抗措施",
                list(BRAND_AGING_OPTIONS.keys()),
                help="可多選，效果疊加上限 70%",
            )
            params['brand_aging_countermeasures'] = selected_cm

        # 4.4 Revenue streams
        selected_streams = st.multiselect(
            "多元收入流",
            list(REVENUE_STREAM_OPTIONS.keys()),
            help="選擇額外收入來源",
        )
        params['revenue_streams'] = selected_streams

        # Check prerequisites and show warnings
        for s in selected_streams:
            info = REVENUE_STREAM_OPTIONS[s]
            if info['requires_onsen'] and params.get('onsen_level', 0) == 0:
                st.warning(f"⚠️「{s}」需要冷泉溫泉設施")
            if info['requires_ccrc'] and params['ccrc_care_ratio'] < 0.05:
                st.warning(f"⚠️「{s}」需要 CCRC 照護配比 > 5%")
            if info['requires_trust'] > 0:
                st.info(f"ℹ️「{s}」需要品牌信任 > {info['requires_trust']}")

        # 4.5 Market replenishment
        if advanced:
            params['market_replenishment_rate'] = st.slider(
                "市場容量年補充率（%）", 1.0, 8.0, 4.0, step=0.5) / 100

        st.divider()

        # ==========================================
        # Group 5: External Environment
        # ==========================================
        st.subheader("🌐 外部環境")

        # 5.1 Regulation
        reg_choice = st.selectbox(
            "法規環境",
            list(REGULATION_PRESETS.keys()),
            index=0,
        )
        reg_preset = REGULATION_PRESETS[reg_choice]
        params.update(reg_preset)

        # 5.2 Cultural acceptance
        if advanced:
            params['initial_cultural_acceptance'] = st.slider(
                "初始文化接受度（%）", 1, 20, 5) / 100
            params['annual_acceptance_growth'] = st.slider(
                "年增率（百分點）", 0.5, 4.0, 2.0, step=0.5) / 100

        # 5.3 Macro economy
        macro_choice = st.selectbox(
            "宏觀經濟",
            list(MACRO_PRESETS.keys()),
            index=1,
        )
        params.update(MACRO_PRESETS[macro_choice])

        # 5.4 Competitor
        comp_on = st.checkbox("競品進入", value=False)
        if comp_on:
            params['competitor_active'] = True
            if advanced:
                params['competitor_year'] = st.slider(
                    "競品進入年份", 3, 20, 5)
                params['competitor_intensity'] = st.selectbox(
                    "競品強度", ['medium', 'strong'],
                    format_func=lambda x: '中度' if x == 'medium' else '強勢')
            else:
                params['competitor_year'] = 5
                params['competitor_intensity'] = 'medium'

        # 5.5 Alternative investment rate
        if advanced:
            params['alternative_investment_rate'] = st.slider(
                "替代投資回報率（%）", 3.0, 12.0, 6.0, step=0.5) / 100

        # Residual value appreciation
        if advanced:
            params['residual_value_appreciation'] = st.slider(
                "殘值年增值率（%）", 0.0, 5.0, 3.0, step=0.5) / 100

        # ==========================================
        # Group 6: Advanced Model Assumptions
        # ==========================================
        st.divider()
        with st.expander("⚙️ 進階模型假設", expanded=False):
            st.caption(
                "以下參數影響模擬計算核心邏輯。"
                "標有 ⚠️ 為模型假設而非實證數據。"
                "修改前請閱讀各參數說明。"
            )

            st.markdown("**崩潰判定**")
            params['liquidity_crisis_quarters'] = st.slider(
                "流動性危機門檻（季）⚠️",
                min_value=1, max_value=12, value=4,
                help="淨流動性連續為負多少季觸發崩潰。"
                     "預設 4 季（1 年）。較保守可設 2 季，較寬鬆可設 8 季。"
                     "此為模型假設，無行業統一標準。",
            )

            st.markdown("**收入假設**")
            _fee_inf_on = st.checkbox(
                "啟用月費年度調漲 ⚠️",
                value=False,
                help="規格書預設月費固定不漲（保守假設）。"
                     "開啟後月費將隨成本通膨按比例調漲。",
            )
            if _fee_inf_on:
                params['fee_inflation_ratio'] = st.slider(
                    "月費漲幅 / 成本通膨比",
                    min_value=0.1, max_value=1.0, value=0.7, step=0.1,
                    help="0.7 = 成本漲 2% 時月費漲 1.4%。",
                )
            else:
                params['fee_inflation_ratio'] = 0.0

            st.markdown("**品牌動態**")
            params['brand_base_decay'] = st.slider(
                "品牌信任季度衰減 ⚠️",
                min_value=0.1, max_value=2.0, value=0.5, step=0.1,
                help="品牌信任每季自然衰減值。規格書預設 0.5。"
                     "信託 level 2 時信任將趨近上限，可調高此值增加波動。",
            )

            st.markdown("**營運能力**")
            params['ops_capability_floor'] = st.slider(
                "營運能力下限 ⚠️",
                min_value=0, max_value=30, value=10,
                help="營運能力的最低值。預設 10，代表即使條件最差仍有基本運作能力。"
                     "設為 0 = 允許能力完全歸零（規格書原始行為）。",
            )

            st.markdown("**蒙地卡羅擾動**")
            _mc_label = st.select_slider(
                "整體不確定性水位",
                options=["保守（低擾動）", "中等（預設）", "積極（高擾動）"],
                value="中等（預設）",
                help="控制所有 MC 擾動參數的幅度。"
                     "保守 = σ×0.5，中等 = 預設值，積極 = σ×1.5。",
            )
            _mc_map = {
                "保守（低擾動）": 0.5,
                "中等（預設）": 1.0,
                "積極（高擾動）": 1.5,
            }
            params['mc_uncertainty_level'] = _mc_map[_mc_label]

    return params
