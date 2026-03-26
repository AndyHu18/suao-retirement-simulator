"""
Sidebar controls: 5 strategy groups.
Quick mode = 5 dropdowns. Advanced = presets + expandable sliders.
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
    MACRO_PRESETS,
    REGULATION_PRESETS,
    BRAND_AGING_OPTIONS,
    REVENUE_STREAM_OPTIONS,
)
from utils.icons import MONEY, ROCKET, HOSPITAL, CALENDAR, GLOBE, BOOK, header, HOUSE


def render_sidebar():
    """Render sidebar. Returns params dict."""
    params = dict(DEFAULT_PARAMS)

    with st.sidebar:
        st.markdown(header(HOUSE, "策略控制面板", level=2), unsafe_allow_html=True)

        # Advanced mode — prominent card design
        st.markdown("""<div style="background:linear-gradient(135deg,#f7f5f0,#efe9dd);
            border:1.5px solid #d4bc8a;border-radius:10px;padding:14px 16px;margin:8px 0 16px;
            cursor:pointer;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#b08d57" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
                <span style="font-weight:600;color:#1a1a1a;font-size:15px;">進階模式</span>
            </div>
            <div style="color:#7a6234;font-size:13px;line-height:1.5;">
                開啟後可微調每一個底層參數、自訂每期戶數、查看可信度標記
            </div>
        </div>""", unsafe_allow_html=True)
        adv = st.toggle("開啟進階模式", False)

        mc_runs = st.select_slider("模擬次數", [100, 500, 1000, 5000], 1000,
                                    help="跑幾次不同情境的模擬。越多越準但越慢。")
        params['_mc_runs'] = mc_runs

        # Quick guide
        st.markdown("""<div class="sidebar-guide">
            <b>操作方式：</b>選策略 → 右邊即時預覽 → 滿意後按「開始模擬」<br>
            預設配置故意什麼都沒開，方便你看加配套的效果。
        </div>""", unsafe_allow_html=True)

        st.divider()

        # ===== Group 1: Capital & Financial =====
        st.markdown(header(MONEY, "資本與財務", level=3), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-guide">決定資金來源和收費方式。影響整體可行性。</div>',
                    unsafe_allow_html=True)

        cap = st.selectbox("資本結構", list(CAPITAL_STRUCTURE_PRESETS.keys()) + ['自訂（輸入實際數字）'],
                            index=3, help="資金從哪來、利息多少、能等多久回本。")
        if cap == '自訂（輸入實際數字）':
            params['total_budget'] = st.number_input("實際總預算（億）", 100, 2000, 800) * 1e8
            params['annual_cost_of_capital'] = st.number_input("年化資金成本（%）", 0.5, 15.0, 3.5) / 100
            params['payback_tolerance_years'] = st.number_input("回收期容忍（年）", 3, 50, 20)
        else:
            params.update(CAPITAL_STRUCTURE_PRESETS[cap])
            if adv:
                with st.expander("底層參數"):
                    params['total_budget'] = st.slider("總預算（億）", 300, 1500,
                        int(CAPITAL_STRUCTURE_PRESETS[cap]['total_budget'] / 1e8), 50) * 1e8
                    params['annual_cost_of_capital'] = st.slider("資金成本（%）", 1.0, 8.0,
                        CAPITAL_STRUCTURE_PRESETS[cap]['annual_cost_of_capital'] * 100, 0.5) / 100
                    params['payback_tolerance_years'] = st.slider("回收期（年）", 5, 35,
                        CAPITAL_STRUCTURE_PRESETS[cap]['payback_tolerance_years'])

        dep = st.selectbox("押金退還", list(DEPOSIT_REFUND_PRESETS.keys()) + ['自訂（輸入實際數字）'], index=0,
                            help="住戶押金怎麼退？直接影響擠兌風險。")
        if dep == '自訂（輸入實際數字）':
            params['deposit_amount'] = st.number_input("押金（萬）", 500, 4000, 2500) * 1e4
            params['monthly_fee'] = st.number_input("月費（萬）", 5, 20, 10) * 1e4
            params['refund_percentage'] = st.number_input("退費比例（%）", 0, 100, 90) / 100
            params['refund_amortization_years'] = st.number_input("償卻年限", 0, 10, 0)
        else:
            params.update(DEPOSIT_REFUND_PRESETS[dep])
            if adv:
                with st.expander("押金底層"):
                    params['deposit_amount'] = st.slider("押金（萬）", 500, 4000,
                        int(DEPOSIT_REFUND_PRESETS[dep]['deposit_amount'] / 1e4), 100) * 1e4
                    params['monthly_fee'] = st.slider("月費（萬）", 5, 20,
                        int(DEPOSIT_REFUND_PRESETS[dep]['monthly_fee'] / 1e4)) * 1e4

        trust_opts = {'無信託': 0, '基本信託': 1, '獨立信託+審批': 2, '北卡級完全保護': 3}
        trust = st.selectbox("押金保護等級", list(trust_opts.keys()), index=0,
                              help="住戶的幾千萬押金怎麼保管。等級越高住戶越安心。")
        params['trust_mechanism_level'] = trust_opts[trust]
        params['trust_independent'] = trust_opts[trust] >= 2

        st.divider()

        # ===== Group 2: Demand Engine =====
        st.markdown(header(ROCKET, "需求引擎", level=3), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-guide">怎麼讓人來住。這些投入的效果有 30-50% 不確定性。'
                    '<br><b>關鍵：保險綁定是最大槓桿。</b></div>', unsafe_allow_html=True)

        ins = st.checkbox("保險綁定通路", False, help="跟壽險公司合作，讓保戶優先入住。你能談但結果取決於對方。")
        if ins:
            if adv:
                params['insurance_factor'] = st.slider("綁定強度", 1.0, 3.0, 2.0, 0.1,
                    help="實際效果可能有 30-50% 偏差。")
                params['insurance_start_quarter'] = st.slider("上線季度", 1, 20, 8)
            else:
                params['insurance_factor'] = 2.0

        exp = st.selectbox("體驗行銷", list(EXPERIENCE_PRESETS.keys()), index=1,
                            help="讓潛在客戶「先來住住看」。花了錢但效果取決於執行品質。")
        exp_preset = EXPERIENCE_PRESETS[exp]
        params['experience_level'] = exp_preset['experience_level']
        params['experience_cost_monthly'] = exp_preset['experience_cost_monthly']
        params['h_hotel_active'] = exp_preset.get('h_hotel_active', params['h_hotel_active'])
        if adv:
            with st.expander("體驗底層"):
                params['experience_level'] = st.slider("體驗深度", 0.0, 3.0,
                    exp_preset['experience_level'], 0.5)
                params['experience_cost_monthly'] = st.slider("體驗行銷月費（萬）", 50, 5000,
                    int(exp_preset['experience_cost_monthly'] / 1e4), 50) * 1e4

        if params['h_hotel_active'] and adv:
            with st.expander("H 會館"):
                params['h_hotel_annual_contacts'] = st.slider("年客群", 2000, 15000, 6000, 500)
                params['h_hotel_inquiry_rate'] = st.slider("諮詢率%", 1.0, 10.0, 3.0, 0.5,
                    help="低可信度（偏差 50%+）。有實際數據建議替換。") / 100
                params['h_hotel_close_rate'] = st.slider("成交率%", 5.0, 25.0, 12.0, 1.0,
                    help="低可信度（偏差 50%+）。有實際數據建議替換。") / 100

        if adv:
            params['marketing_budget_monthly'] = st.slider("行銷預算（萬/月）", 100, 5000, 500, 100) * 1e4
            st.markdown("---")
            st.caption("[低可信度]以下為低可信度參數（建議用實際數據替換）")
            params['target_pool'] = st.number_input(
                "目標客群池", 10000, 100000, int(params['target_pool']), 1000,
                help="[低可信度]低可信度（±50%+）。大台北65歲以上高淨值人口估計。有實際市調數據請替換。")
            params['base_annual_conversion'] = st.slider(
                "基礎年轉化率 (%)", 0.1, 2.0, float(params['base_annual_conversion']) * 100, 0.1,
                help="[低可信度]低可信度（±50%+）。目標客群每年轉為入住的比率。全球CCRC平均約0.5%。") / 100

        st.divider()

        # ===== Group 3: Product & Operations =====
        st.markdown(header(HOSPITAL, "產品與營運", level=3), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-guide">蓋什麼設施、找誰營運。醫療和溫泉是蘇澳的核心差異化。</div>',
                    unsafe_allow_html=True)

        if adv:
            params['ccrc_care_ratio'] = st.slider("介護棟佔比%", 0, 30, 15,
                help="社區裡留多少比例給需要照護的長者") / 100

        med = st.selectbox("醫療整合", list(MEDICAL_PRESETS.keys()), index=0,
                            help="醫療是長者選養老社區最在意的事。效果有 30% 不確定性。")
        params['medical_integration'] = MEDICAL_PRESETS[med]['medical_integration']
        if adv:
            params['medical_external_revenue'] = st.checkbox("醫療對外營業", False)

        onsen = st.selectbox("冷泉溫泉", list(ONSEN_PRESETS.keys()), index=0,
                              help="蘇澳碳酸冷泉——全球僅兩處。")
        params['onsen_level'] = ONSEN_PRESETS[onsen]['onsen_level']
        params['onsen_cost_multiplier'] = ONSEN_PRESETS[onsen]['onsen_cost_multiplier']

        op = st.selectbox("營運夥伴", list(OPERATION_PARTNER_PRESETS.keys()), index=0,
                           help="誰來經營日常營運。效果有 30% 不確定性。")
        params.update(OPERATION_PARTNER_PRESETS[op])
        if adv:
            params['debranding_level'] = st.slider("去標籤化程度", 1, 3, 2,
                help="1=養生語言 2=生活方式 3=純生活品牌")
            st.markdown("---")
            st.caption("[低可信度]以下為低可信度參數（建議用實際數據替換）")
            params['staff_ratio'] = st.slider(
                "每戶員工配比", 0.2, 0.8, float(params['staff_ratio']), 0.05,
                help="[低可信度]低可信度（±50%+）。每位住戶對應的員工數。業界0.3-0.6。")
            params['avg_staff_cost_monthly'] = st.number_input(
                "員工平均月薪", 30000, 80000, int(params['avg_staff_cost_monthly']), 1000,
                help="[低可信度]低可信度（±50%+）。蘇澳地區實際行情。")

        st.divider()

        # ===== Group 4: Development Pace =====
        st.markdown(header(CALENDAR, "開發節奏", level=3), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-guide">8 期怎麼蓋、怎麼防止社區「變老」。品牌老化對抗可多選疊加。</div>',
                    unsafe_allow_html=True)

        if adv:
            with st.expander("各期規模"):
                units = []
                defs = DEFAULT_PARAMS['phase_units']
                for i in range(8):
                    u = st.number_input(f"第{i+1}期", 200, 2000, defs[i], 100, key=f'pu{i}')
                    units.append(u)
                params['phase_units'] = units

            with st.expander("啟動條件"):
                params['phase_activation_threshold'] = st.slider("入住率門檻%", 60, 95, 80) / 100
                params['min_cash_days_for_activation'] = st.slider("最低儲備天數", 100, 500, 250, 50)

            selected_cm = st.multiselect("品牌老化對抗", list(BRAND_AGING_OPTIONS.keys()),
                                          help="可多選。效果疊加上限 70%。讓社區不會「變老」。")
            params['brand_aging_countermeasures'] = selected_cm
        else:
            selected_cm = st.multiselect("品牌老化對抗", list(BRAND_AGING_OPTIONS.keys()),
                                          help="可多選。讓社區不會「變老」的策略。")
            params['brand_aging_countermeasures'] = selected_cm

        streams = st.multiselect("多元收入流", list(REVENUE_STREAM_OPTIONS.keys()),
                                  help="可多選。除了月費和押金以外的額外收入來源。")
        params['revenue_streams'] = streams
        for s in streams:
            info = REVENUE_STREAM_OPTIONS[s]
            if info['requires_onsen'] and params.get('onsen_level', 0) == 0:
                st.warning(f"「{s}」需要冷泉設施")
            if info['requires_ccrc'] and params['ccrc_care_ratio'] < 0.05:
                st.warning(f"「{s}」需要介護配比 > 5%")

        if adv:
            params['market_replenishment_rate'] = st.slider(
                "市場容量年補充率%", 1.0, 8.0, 4.0, 0.5,
                help="外部假設。你不能控制，只是做情境假設。") / 100

        st.divider()

        # ===== Group 5: External =====
        st.markdown(header(GLOBE, "外部環境", level=3), unsafe_allow_html=True)
        st.markdown('<div class="sidebar-guide">這些你無法控制，只是在做情境假設。'
                    '<br>用不同假設做壓力測試。</div>', unsafe_allow_html=True)

        reg = st.selectbox("法規環境", list(REGULATION_PRESETS.keys()), index=0)
        params.update(REGULATION_PRESETS[reg])

        if adv:
            params['initial_cultural_acceptance'] = st.slider("初始文化接受度%", 1, 20, 5) / 100
            params['annual_acceptance_growth'] = st.slider("年增百分點", 0.5, 4.0, 2.0, 0.5) / 100

        macro = st.selectbox("宏觀經濟", list(MACRO_PRESETS.keys()), index=1)
        params.update(MACRO_PRESETS[macro])

        comp = st.checkbox("競品進入", False)
        if comp:
            params['competitor_active'] = True
            if adv:
                params['competitor_year'] = st.slider("進入年份", 3, 20, 5)
                params['competitor_intensity'] = st.selectbox("強度", ['medium', 'strong'],
                    format_func=lambda x: '中度' if x == 'medium' else '強勢')

        if adv:
            params['alternative_investment_rate'] = st.slider(
                "替代投資回報%", 3.0, 12.0, 6.0, 0.5,
                help="如果這筆錢不蓋養老村，拿去做別的投資能賺多少。") / 100
            params['residual_value_appreciation'] = st.slider(
                "殘值年增值率（%）", 0.0, 5.0, 3.0, step=0.5) / 100
            params['initial_brand_trust'] = st.slider(
                "初始品牌信任", 0, 100, int(params['initial_brand_trust']),
                help="[低可信度]低可信度（±50%+）。華友聯目前的養老品牌知名度。0=完全未知，100=業界標竿。")

        # ==========================================
        # Group 6: Advanced Model Assumptions
        # ==========================================
        st.divider()
        with st.expander("進階模型假設", expanded=False):
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

        # --- Glossary ---
        with st.expander("術語表"):
            from utils.formatting import GLOSSARY
            for term, expl in GLOSSARY.items():
                st.markdown(f"**{term}**：{expl}")

    return params
