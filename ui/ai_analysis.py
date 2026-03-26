"""
Dual AI system:
- Haiku: per-chart instant insight (2-3 sentences, <200 tokens each)
- Opus: full consultant report (button-triggered, 7-part, streaming)
- Sonnet: follow-up chat
"""

import os
import re
import numpy as np
import streamlit as st
from utils.formatting import RULE_NAMES

# ============================================================
# System prompts
# ============================================================

HAIKU_SYSTEM = """你是養老地產數據分析師。用最簡短的繁體中文解讀。不用英文術語。語氣直接，像跟老闆報告。不超過60字。"""

CONSULTANT_SYSTEM = """你是養老地產領域30年經驗的顧問，精通開發、精算、品牌、金融、行為設計。
為華友聯蘇澳8,000戶養生造鎮提供諮詢。

分析風格：先結論再展開、每個判斷引用具體數字、用全球案例對比、繁體中文。

全球案例知識：
【成功】泰康（27社區、燕園99.7%入住、毛利12.3%→30年回收）、Kendal（A+、DCOH759天）、
Acts（95.6%入住、75%預售才動工）、The Villages（15萬+戶、40年成長）
【失敗】Erickson（同時10園區+債務→破產）、Friendship Village（42年成功→COVID擠兌→10%回收）、
烏鎮雅園（2000+售罄入住<10%）、愛晚系（132億龐氏）

【閾值】入住>90%健康/85%警戒/80%嚴重/75%存亡/70%關閉風險
DCOH 250天最低/400-500天BBB/750+天A+ | 人力佔60-70% | 品牌老化15-25年

【蘇澳】距台北70-90分鐘、35000客群、全球僅兩處碳酸冷泉、區域醫院15-30分鐘

=== 人性影響矩陣 ===
產品就是行銷、體驗就是銷售、住戶社交就是商業模式。
矩陣三軸：人性反應（傳播/信任/好感/高價值/渴望/身份/禀賦/記憶/意義/安全）×
財務角色（免費/獲客/留客/利潤/品牌）× 用戶旅程（聽說→來訪→試住→入住→日常→探視）

行為經濟學：損失厭惡2-2.5x、峰終定律70%取決峰值+結束、口碑LTV是廣告的2-5x、
每日習慣留存是每週的3-5x、天然稀缺溢價2-3x。"""


def _md_to_html(text):
    """Convert markdown to HTML for inline rendering, with constrained heading sizes."""
    # Process line by line to handle headings
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # Headings: constrain to small sizes (Apple typography)
        if stripped.startswith('#### '):
            result.append(f'<p style="font-size:15px;font-weight:600;color:#1d1d1f;margin:10px 0 4px;">{stripped[5:]}</p>')
        elif stripped.startswith('### '):
            result.append(f'<p style="font-size:16px;font-weight:600;color:#1d1d1f;margin:12px 0 4px;">{stripped[4:]}</p>')
        elif stripped.startswith('## '):
            result.append(f'<p style="font-size:17px;font-weight:700;color:#1d1d1f;margin:14px 0 6px;">{stripped[3:]}</p>')
        elif stripped.startswith('# '):
            result.append(f'<p style="font-size:18px;font-weight:700;color:#1d1d1f;margin:16px 0 6px;">{stripped[2:]}</p>')
        elif stripped == '':
            result.append('<br>')
        else:
            result.append(f'<p style="font-size:15px;line-height:1.7;color:#1d1d1f;margin:0 0 6px;">{line}</p>')
    text = '\n'.join(result)
    # Bold: **text** -> <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#b08d57;">\1</strong>', text)
    # Italic: *text* -> <em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code: `text` -> <code>
    text = re.sub(r'`(.+?)`', r'<code style="background:#f0ede8;padding:1px 4px;border-radius:3px;font-size:13px;">\1</code>', text)
    # Lists: - item -> bullet
    text = re.sub(r'<p([^>]*)>[\s]*[-\u2022]\s*', '<p\\1 style="padding-left:16px;">\u2022 ', text)
    return text


def _get_client():
    """Get Anthropic client. Try session_state, st.secrets, then env var."""
    import streamlit as st
    key = ''
    # Method 1: user input via sidebar (session_state)
    if st.session_state.get('user_api_key'):
        key = st.session_state['user_api_key']
    # Method 2: st.secrets (Streamlit Cloud)
    if not key:
        try:
            key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass
    # Method 3: environment variable (local dev)
    if not key:
        key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=key)


# ============================================================
# Haiku chart insights
# ============================================================

def generate_haiku_insights(mc, params, stress=None):
    """Generate Haiku insights for all charts. Returns dict of chart->text."""
    client = _get_client()
    if not client:
        return {}

    m = mc['_metrics']
    mid = np.argsort(mc['cf_curves'][:, -1])[mc['n_runs'] // 2]
    r = mc['results'][mid]
    na = len(r.phase_activations)

    charts = {
        'jcurve': f"J曲線：IRR={m['irr_median']:.1%}，回本={m['payback_median']:.1f}年，"
                   f"25年末累計{m['final_cf_median']/1e9:.1f}B，崩潰率{m['collapse_prob']:.1%}",
        'waterfall': f"瀑布圖：押金{r.cf_deposit_income.sum()/1e9:.1f}B、月費{r.cf_monthly_fee.sum()/1e9:.1f}B、"
                     f"建設-{r.cf_construction.sum()/1e9:.1f}B、營運-{r.cf_operating.sum()/1e9:.1f}B",
        'occupancy': f"入住率：最終{r.occupancy_rate[-1]:.0%}，{na}/{params['total_phases']}期啟動，"
                     f"冷啟動期約{np.argmax(r.occupancy_rate > 0.5) / 4:.1f}年",
        'market': f"市場：25年後剩餘{r.market_pool_remaining[-1]/params['target_pool']:.0%}，"
                  f"累計入住{r.new_move_ins.sum():.0f}戶",
    }

    insights = {}
    for key, data_str in charts.items():
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                system=HAIKU_SYSTEM,
                messages=[{"role": "user", "content": f"數據：{data_str}。用2句話說結論和原因。"}],
            )
            insights[key] = resp.content[0].text
        except Exception:
            insights[key] = ""

    return insights


def render_haiku_insight(key, insights):
    """Render a single Haiku insight below a chart."""
    text = insights.get(key, "")
    if text:
        text = _md_to_html(text)
        st.markdown(f"""<div style="background:#f7f7f5; border-left:3px solid #b08d57;
            padding:10px 14px; margin:8px 0 16px; font-size:0.9em;
            border-radius:0 8px 8px 0; color:#1a1a1a; line-height:1.6;">
            <span style="color:#b08d57; font-weight:600;">AI 解讀：</span> {text}</div>""",
            unsafe_allow_html=True)


# ============================================================
# Per-chart Q&A
# ============================================================

CHART_METHODOLOGY = {
    'jcurve': """計算公式：
累計現金流 = Σ(每季淨現金流)
每季淨現金流 = 總收入 - 總成本 - 退費 - 建設成本
總收入 = 押金收入(新入住×押金) + 月費收入(在住×月費×3) + 其他收入(多元收入流+醫療對外+溫泉對外)
總成本 = 員工成本(在住×員工配比×月薪×蘇澳加成×3) + 醫療成本 + 行銷成本 + 資金利息(累計投入×年化成本/4)
IRR = 使季度現金流淨現值為零的折現率，年化後顯示""",

    'waterfall': """計算公式：
7類收支分解，25年累計：
- 押金收入 = Σ(每季新入住 × 押金金額)
- 月費收入 = Σ(每季在住戶數 × 月費 × 3個月)
- 其他收入 = 多元收入流 + 醫療對外 + 溫泉對外
- 建設成本 = 各期啟動時的建設費用
- 營運成本 = 員工+醫療+行銷+溫泉維護+法規+分潤
- 退費支出 = 退出住戶 × 押金 × 有效退費率
- 資金利息 = 累計投入資本 × 年化資金成本 / 4""",

    'occupancy': """計算公式：
新入住 = 基礎需求(目標池×年轉化率/4) × 品牌信任因子(trust/50) × 保險因子 × 冷啟動因子(min(1,(在住/800)^0.5)) × 宏觀因子 × 距離摩擦 × 體驗加成 × 醫療加成 × 溫泉加成 × 市場消耗因子 × 競品分流 + H會館貢獻
退出 = 在住 × (死亡率+自願退出3%+轉介護率) / 4
入住率 = 在住戶數 / 已建成總戶數
新期啟動條件：前期入住率≥門檻 且 儲備天數≥最低 且 建設金≥30%""",

    'market': """計算公式：
市場容量池（動態）：
- 初始 = target_pool（預設35,000人）
- 每季消耗 = 該季新入住數
- 每年補充 = 池 × market_replenishment_rate（預設4%）
- 池 < 初始30% → base_demand按比例下降
消耗百分比 = (初始 - 剩餘) / 初始 × 100%"""
}


def _build_chart_context(chart_key, params, result):
    """Build structured context string for per-chart Q&A."""
    methodology = CHART_METHODOLOGY.get(chart_key, '')

    params_summary = (
        f"當前策略配置：\n"
        f"預算{params['total_budget']/1e8:.0f}億、押金{params['deposit_amount']/1e4:.0f}萬、月費{params['monthly_fee']/1e4:.0f}萬\n"
        f"保險{'開啟(強度'+str(params['insurance_factor'])+')' if params['insurance_factor']>1 else '未開啟'}\n"
        f"信託Lv{params['trust_mechanism_level']}、醫療Lv{params['medical_integration']}、溫泉Lv{params.get('onsen_level',0)}\n"
        f"目標客群{params['target_pool']:,}人、年轉化率{params['base_annual_conversion']*100:.1f}%\n"
        f"各期規模：{params['phase_units'][:params['total_phases']]}"
    )

    r = result
    if chart_key in ('jcurve', 'jcurve_s'):
        cf = r.cumulative_cashflow
        data = (
            f"此圖數據：\n"
            f"Y1累計={cf[3]/1e9:.1f}B, Y5={cf[19]/1e9:.1f}B, Y10={cf[39]/1e9:.1f}B, "
            f"Y15={cf[59]/1e9:.1f}B, Y25={cf[99]/1e9:.1f}B\n"
            f"最終淨現金流={cf[99]/1e9:.1f}B\n"
            f"啟動{len(r.phase_activations)}/{params['total_phases']}期"
        )
    elif chart_key in ('waterfall', 'waterfall_s'):
        data = (
            f"此圖數據（25年累計）：\n"
            f"押金收入={r.cf_deposit_income.sum()/1e8:.0f}億\n"
            f"月費收入={r.cf_monthly_fee.sum()/1e8:.0f}億\n"
            f"其他收入={r.cf_other_revenue.sum()/1e8:.0f}億\n"
            f"建設成本=-{r.cf_construction.sum()/1e8:.0f}億\n"
            f"營運成本=-{r.cf_operating.sum()/1e8:.0f}億\n"
            f"退費支出=-{r.cf_refund.sum()/1e8:.0f}億\n"
            f"資金利息=-{r.cf_capital_cost.sum()/1e8:.0f}億\n"
            f"淨結果={r.cumulative_cashflow[99]/1e8:.0f}億"
        )
    elif chart_key in ('occupancy', 'occupancy_s'):
        data = (
            f"此圖數據：\n"
            f"最終入住率={r.occupancy_rate[99]*100:.0f}%\n"
            f"啟動期數={len(r.phase_activations)}/{params['total_phases']}\n"
            f"累計入住={r.new_move_ins.sum():.0f}戶\n"
            f"累計退出={r.exits.sum():.0f}戶\n"
            f"Y1入住率={r.occupancy_rate[3]*100:.0f}%, Y5={r.occupancy_rate[19]*100:.0f}%, "
            f"Y10={r.occupancy_rate[39]*100:.0f}%"
        )
    elif chart_key == 'market':
        data = (
            f"此圖數據：\n"
            f"初始池={params['target_pool']:,}\n"
            f"25年後剩餘={r.market_pool_remaining[99]:.0f}（{r.market_pool_remaining[99]/params['target_pool']*100:.0f}%）\n"
            f"年補充率={params['market_replenishment_rate']*100:.0f}%\n"
            f"累計入住消耗={r.new_move_ins.sum():.0f}戶"
        )
    else:
        data = ""

    return f"{methodology}\n\n{params_summary}\n\n{data}"


def render_chart_qa(chart_key, chart_label, params, result, api_key):
    """Render a Q&A section below each chart."""

    history_key = f"chart_chat_{chart_key}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Show existing conversation
    for msg in st.session_state[history_key]:
        if msg['role'] == 'user':
            st.markdown(
                f"<div style='background:#f0f0f0;padding:8px 12px;border-radius:8px;"
                f"margin:4px 0;font-size:14px;'>"
                f"<strong>你的問題：</strong>{msg['content']}</div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='background:#f7f7f5;border-left:3px solid #b08d57;"
                f"padding:8px 12px;margin:4px 0;font-size:14px;line-height:1.6;'>"
                f"{_md_to_html(msg['content'])}</div>",
                unsafe_allow_html=True)

    # Input
    q = st.text_input(
        f"💬 問 AI 關於{chart_label}的問題", key=f"qa_input_{chart_key}",
        placeholder="例如：為什麼入住率一直上不去？")
    if q:
        if not api_key:
            st.warning("需要 Anthropic API Key 才能使用 AI 追問。請在側邊欄輸入或設定 Streamlit Secrets。")
        else:
            context = _build_chart_context(chart_key, params, result)
            sys_prompt = (
                f"你是養老地產數據分析師。根據以下模擬數據回答問題。"
                f"只用繁體中文，不用英文術語。引用具體數字。"
                f"不要用 # 標題。用 **粗體** 強調重點。\n\n{context}"
            )
            messages = []
            for msg in st.session_state[history_key]:
                messages.append(msg)
            messages.append({"role": "user", "content": q})

            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=400,
                    system=sys_prompt,
                    messages=messages,
                )
                answer = resp.content[0].text
                st.session_state[history_key].append({"role": "user", "content": q})
                st.session_state[history_key].append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"AI 回答失敗: {e}")


# ============================================================
# Opus full report
# ============================================================

def _generate_haiku_summary(client, params, metrics, mc, stress):
    """Generate a quick Haiku first-pass analysis of the full simulation."""
    mid = np.argsort(mc['cf_curves'][:, -1])[mc['n_runs'] // 2]
    r = mc['results'][mid]
    na = len(r.phase_activations)

    data = (
        f"配置：預算{params['total_budget']/1e8:.0f}億、押金{params['deposit_amount']/1e4:.0f}萬、"
        f"月費{params['monthly_fee']/1e4:.0f}萬、保險{params['insurance_factor']:.1f}、"
        f"信託Lv{params['trust_mechanism_level']}、醫療Lv{params['medical_integration']}\n"
        f"結果：IRR={metrics['irr_median']:.1%}、崩潰率={metrics['collapse_prob']:.1%}、"
        f"回本={metrics['payback_median']:.1f}年、啟動{na}/{params['total_phases']}期\n"
        f"押金收入{r.cf_deposit_income.sum()/1e8:.0f}億、月費{r.cf_monthly_fee.sum()/1e8:.0f}億、"
        f"建設-{r.cf_construction.sum()/1e8:.0f}億、營運-{r.cf_operating.sum()/1e8:.0f}億、"
        f"退費-{r.cf_refund.sum()/1e8:.0f}億"
    )

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=(
                "你是養老地產顧問。用繁體中文，不用英文術語。"
                "給出 3-5 段分析：1.整體判斷 2.為什麼是這結果 3.最該優先調整什麼。"
                "每段不超過 50 字。語氣直接，像跟董事長報告。用數字說話。"
                "格式規則：不要用 # 標題。用「1. 標題」的純文字編號。用 **粗體** 強調重點。"
            ),
            messages=[{"role": "user", "content": f"分析這組模擬結果：\n{data}"}],
        )
        return resp.content[0].text
    except Exception:
        return ""


def render_ai_analysis(params, mc=None, stress=None):
    """Render AI analysis section. Always visible; disabled when MC not yet run."""
    st.divider()
    from utils.icons import AI_BRAIN, header
    st.markdown(header(AI_BRAIN, "AI 顧問分析"), unsafe_allow_html=True)

    has_mc = mc is not None and '_metrics' in mc
    metrics = mc['_metrics'] if has_mc else None

    if not has_mc:
        st.markdown(
            '<div style="background:#f7f7f5;border-radius:10px;'
            'padding:16px 20px;border-left:3px solid #b08d57;">'
            '<span style="color:#4a4a4a;font-size:1em;">'
            '請先點擊上方「<b>開始蒙地卡羅模擬</b>」跑完模擬後，AI 會自動生成初步分析。'
            '</span></div>',
            unsafe_allow_html=True,
        )
        return

    # === Layer 1: Haiku auto-analysis (runs automatically after MC) ===
    client = _get_client()
    if not client:
        st.warning("需要 Anthropic API Key 才能使用 AI 分析功能")
        user_key = st.text_input(
            "輸入 Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="你的 key 不會被儲存，只在本次瀏覽器 session 中使用"
        )
        if user_key:
            st.session_state['user_api_key'] = user_key
            st.rerun()
        return

    # Auto-generate Haiku summary
    if 'haiku_summary' not in st.session_state:
        with st.spinner("AI 正在分析模擬結果..."):
            summary = _generate_haiku_summary(client, params, metrics, mc, stress)
            st.session_state.haiku_summary = summary

    if st.session_state.get('haiku_summary'):
        summary_html = _md_to_html(st.session_state.haiku_summary)
        st.markdown(f"""<div style="background:#f7f7f5; border:1px solid #e0ddd7;
            border-radius:10px; padding:18px 22px; margin:12px 0;">
            <div style="color:#b08d57; font-weight:600; font-size:0.9em;
                margin-bottom:10px; letter-spacing:0.04em;">初步分析（AI 自動生成）</div>
            <div class="ai-output" style="color:#1a1a1a; font-size:1em; line-height:1.8;">
                {summary_html}</div>
        </div>""", unsafe_allow_html=True)

    # === Layer 2: Opus deep analysis (button-triggered) ===
    st.markdown("")
    col1, col2 = st.columns([1, 3])
    with col1:
        run_btn = st.button("啟動深度顧問分析", type="primary")
    with col2:
        if 'opus_report' in st.session_state:
            st.caption("已有深度報告。可再次點擊更新，或在下方追問。")
        else:
            st.caption("由 Opus 生成完整七部分顧問報告（含 4 組對比模擬，約 30-60 秒）")

    if not run_btn and 'opus_report' not in st.session_state:
        return

    if run_btn:
        # Run comparison scenarios with tip carousel
        import time
        from ui.tip_carousel import get_shuffled_tips, render_tip_to_container
        from engine.monte_carlo import run_comparison_scenarios

        ai_tips = get_shuffled_tips()
        ai_tip_box = st.empty()
        ai_progress = st.empty()
        ai_progress.caption("正在跑 4 組對比模擬...")

        # Show first tip
        tid, title, body = ai_tips[0]
        render_tip_to_container(ai_tip_box, tid, title, body, 0, len(ai_tips), "AI 分析準備中")

        comparison = run_comparison_scenarios(params, n_runs=300)
        ai_tip_box.empty()
        ai_progress.empty()

        # Get median run data
        mid = np.argsort(mc['cf_curves'][:, -1])[mc['n_runs'] // 2]
        r = mc['results'][mid]

        # Build data package
        user_msg = _build_opus_prompt(params, metrics, comparison, r, stress)

        # Stream response
        with st.container():
            placeholder = st.empty()
            full_text = ""
            try:
                with client.messages.stream(
                    model="claude-opus-4-6",
                    max_tokens=8000,
                    system=CONSULTANT_SYSTEM,
                    messages=[{"role": "user", "content": user_msg}],
                ) as stream:
                    for text in stream.text_stream:
                        full_text += text
                        placeholder.markdown(full_text)
            except Exception as e:
                st.error(f"AI 分析失敗: {e}")
                return

        st.session_state.opus_report = full_text
        st.session_state.consultant_history = [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": full_text},
        ]

    # Display cached report
    elif 'opus_report' in st.session_state:
        st.markdown('<div class="ai-output">', unsafe_allow_html=True)
        st.markdown(st.session_state.opus_report)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Follow-up chat ---
    if 'consultant_history' in st.session_state:
        st.divider()
        st.markdown("##### 繼續追問")

        followup = st.text_area("你的問題", height=80,
            placeholder="例如：保險綁定具體怎麼談？如果首期改300戶？")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("送出追問", type="primary") and followup:
                st.session_state.consultant_history.append(
                    {"role": "user", "content": followup})
                try:
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=4000,
                        system=CONSULTANT_SYSTEM + "\n\n" + MODEL_METHODOLOGY,
                        messages=st.session_state.consultant_history,
                    )
                    reply = resp.content[0].text
                    st.session_state.consultant_history.append(
                        {"role": "assistant", "content": reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"追問失敗: {e}")
        with c2:
            if st.button("複製全文"):
                full = "\n\n---\n\n".join(
                    m['content'] for m in st.session_state.consultant_history
                    if m['role'] == 'assistant'
                )
                st.code(full, language=None)

        # Display conversation history
        for msg in st.session_state.consultant_history:
            if msg['role'] == 'assistant' and msg['content'] != st.session_state.get('opus_report'):
                st.markdown("---")
                st.markdown(msg['content'])
            elif msg['role'] == 'user' and msg['content'] != st.session_state.consultant_history[0].get('content'):
                st.markdown(f"> **你的追問：** {msg['content']}")


MODEL_METHODOLOGY = """## 模型計算邏輯摘要

核心公式：
- 新入住/季 = 基礎需求(目標池×年轉化率/4) × 品牌信任(trust/50) × 保險因子 × 冷啟動((在住/800)^0.5) × 宏觀 × 距離摩擦 × 體驗boost × 醫療boost × 溫泉boost × 市場消耗 × 競品分流 + H會館
- 退出/季 = 在住 × (年齡死亡率+3%自願+轉介護率) / 4
- 品牌信任/季 = 前值 + 入住率加成(occ>85%:+2) + 信託(level×1.5) + 文化(×0.5) + 規模(>100:+0.3) + 溫泉加成 - 老化衰減 - 隨機衝擊(2%機率)
- 資金利息 = 累計投入 × 年化成本 / 4
- 營運能力 = 前值 + 團隊品質 + 學習曲線 - 流動率×2 - 0.5
- 市場池：初始35000，每季消耗=新入住，年補充=池×補充率
- 分期啟動：前期occ≥門檻 且 儲備≥天數 且 建設金≥30%
- 崩潰判定：營運現金+應急+押金池 < 0

重要模型盲點（分析時必須提醒）：
- 定價↔需求的反饋缺失：調高押金不會顯示需求下降
- 觸點設計品質缺失：無法區分「花多但體驗差」vs「花少但設計精」
"""


def _build_opus_prompt(params, metrics, comparison, r, stress):
    """Build the full data package for Opus."""
    lines = []
    lines.append(MODEL_METHODOLOGY)
    lines.append("## 策略配置")
    lines.append(f"- 總預算: {params['total_budget']/1e8:.0f}億 | 資金成本: {params['annual_cost_of_capital']:.1%}")
    lines.append(f"- 押金: {params['deposit_amount']/1e4:.0f}萬 | 月費: {params['monthly_fee']/1e4:.0f}萬")
    lines.append(f"- 退費: {params['refund_percentage']:.0%} | 信託: Lv{params['trust_mechanism_level']}")
    lines.append(f"- 保險: {params['insurance_factor']:.1f} | 醫療: Lv{params['medical_integration']}")
    lines.append(f"- 溫泉: Lv{params.get('onsen_level', 0)} | 體驗: Lv{params['experience_level']}")
    lines.append(f"- 首期: {params['phase_units'][0]}戶 | 門檻: {params['phase_activation_threshold']:.0%}")

    lines.append("\n## 模擬結果")
    lines.append(f"- IRR: {metrics['irr_median']:.1%} | 崩潰: {metrics['collapse_prob']:.1%}")
    lines.append(f"- 回本: {metrics['payback_median']:.1f}年 | 最大需求: {metrics['max_funding_need']/1e9:.1f}B")
    lines.append(f"- 啟動: {len(r.phase_activations)}/{params['total_phases']}期")

    lines.append("\n## 逐年數據")
    for y in range(25):
        q = y * 4 + 3  # End of year
        lines.append(
            f"Y{y+1}: CF={r.cumulative_cashflow[q]/1e8:.0f}億, "
            f"occ={r.occupancy_rate[q]*100:.0f}%, "
            f"trust={r.brand_trust[q]:.0f}"
        )

    lines.append("\n## 對比模擬")
    for name, m in comparison.items():
        lines.append(f"**{name}**: IRR {m['irr_median']:.1%} | 崩潰 {m['collapse_prob']:.1%} | "
                     f"回本 {m['payback_median']:.1f}年")

    if stress:
        lines.append("\n## 壓力測試")
        for name, d in stress.items():
            lines.append(f"- {name}: 存活率 {d['survival_rate']:.0%}")

    lines.append("\n## 規則狀態")
    final = r.rules_status[-1]
    for i, name in enumerate(RULE_NAMES):
        if final[i] > 0:
            lines.append(f"- [{'已觸發' if final[i]==2 else '接近觸發'}] {name}")

    lines.append("""
請提供完整顧問分析，涵蓋七部分：
一、整體判斷（能不能做？一段話結論）
二、因果診斷（從瀑布圖追根因，用因果鏈 A→B→C）
三、組合效應（對比模擬解讀，哪些有超線性增強？缺什麼最致命？）
四、配套行動方案（第一層：必須同步 / 第二層：增強 / 第三層：選擇題）
五、風險地圖（規則觸發 + 歷史案例）
六、如果你是決策者（站在董事長位置，現在做什麼？用數字支撐）
七、觸點設計機會掃描（用人性影響矩陣，3-5個建議，每個附模擬器參數調整指引）
所有分析引用具體數字。格式要求：使用 ### 作為最高級標題，不要用 # 或 ##。""")

    return "\n".join(lines)
