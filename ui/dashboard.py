"""
Dashboard: 3-layer visualization following spec v4 output architecture.
A. Judgment box -> B. Big numbers -> C. J-curve -> D. Waterfall
-> E. Impact attribution -> F. Before/after -> G. Occupancy -> H. Gantt
-> I. Stress -> J. Market -> K. Unit econ -> L. Brand/ops/rules -> M. Health
"""

import os
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from utils.formatting import fmt_billion, fmt_billion_short, fmt_pct, RULE_NAMES, GLOSSARY
from utils.icons import CHART, FIRE, TRENDING, DOLLAR, ACTIVITY, CHECK_CIRCLE, TARGET, AI_BRAIN, header
from engine.health_check import run_health_checks, detect_contradictions
from ui.ai_analysis import generate_haiku_insights, render_haiku_insight, render_chart_qa

# Shared Plotly font config -- Apple-style readable sizes
CHART_FONT = dict(family="Noto Sans TC, -apple-system, sans-serif", size=15, color="#1a1a1a")


def _styled(fig):
    """Apply consistent font styling to a Plotly figure. v4.7"""
    fig.update_layout(font=CHART_FONT)
    return fig


def render_dashboard(mc, params, stress=None):
    """Main entry: render all dashboard sections."""
    metrics = mc['_metrics']
    mid = np.argsort(mc['cf_curves'][:, -1])[mc['n_runs'] // 2]
    r = mc['results'][mid]
    years = np.arange(100) / 4

    # --- Get API key for per-chart Q&A ---
    _api_key = (st.session_state.get('user_api_key')
                or os.environ.get('ANTHROPIC_API_KEY', ''))
    try:
        _api_key = _api_key or st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    # --- Generate Haiku insights (all charts in parallel-ish) ---
    if 'haiku_insights' not in st.session_state:
        insights = generate_haiku_insights(mc, params, stress)
        st.session_state.haiku_insights = insights
    else:
        insights = st.session_state.haiku_insights

    # --- A. Summary Judgment Box ---
    _render_judgment(metrics, params, r)

    # --- Contradiction insights (styled cards instead of yellow st.warning) ---
    ctrs = detect_contradictions(mc, params, stress)
    if ctrs:
        for c in ctrs:
            st.markdown(f"""<div style="background:#F9F7F3; border:1px solid #E8E2D8;
                border-radius:8px; padding:14px 20px; margin:6px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <span style="color:#8B7355; font-size:0.95em; line-height:1.7;">
                ▸&ensp;{c['message']}</span>
            </div>""", unsafe_allow_html=True)

    # --- Phase activation failure warning ---
    _median_idx = np.argsort(mc['cf_curves'][:, -1])[mc['n_runs'] // 2]
    _na = len(mc['results'][_median_idx].phase_activations)
    _nt = params['total_phases']
    if _na < _nt:
        _completed_units = sum(params['phase_units'][:_na])
        _total_units = sum(params['phase_units'][:_nt])
        st.markdown(f"""<div style="background:#FAF6F1; border:1px solid #E8E2D8;
            border-radius:8px; padding:14px 20px; margin:6px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <span style="color:#8B4513; font-size:0.95em; line-height:1.7;">
            ⚠&ensp;第 {_na+1}-{_nt} 期無法啟動（入住率未達 {params['phase_activation_threshold']:.0%} 門檻）。
            {_total_units:,} 戶計畫目前只能完成 {_completed_units:,} 戶。</span>
        </div>""", unsafe_allow_html=True)

    # --- B. Summary Banner + Three Big Numbers ---
    _good = 0
    _total = 3
    _irr_ok = metrics['irr_median'] > 0.02
    _cp_ok = metrics['collapse_prob'] < 0.10
    _pb_ok = 0 < metrics['payback_median'] < 25
    _good = sum([_irr_ok, _cp_ok, _pb_ok])
    if _good == 3:
        _banner_color, _banner_bg, _banner_icon = '#4A7C59', '#F2F8F4', '✓'
        _banner_msg = f"三項核心指標全部達標"
    elif _good >= 2:
        _banner_color, _banner_bg, _banner_icon = '#B08D57', '#F9F6F0', '◐'
        _banner_msg = f"{_good}/3 項達標，{3 - _good} 項需注意"
    else:
        _banner_color, _banner_bg, _banner_icon = '#8B4513', '#FAF6F1', '⚠'
        _banner_msg = f"僅 {_good}/3 項達標，需重點關注"
    _details = []
    _details.append(f"報酬率 {'✓' if _irr_ok else '✗'}")
    _details.append(f"崩潰風險 {'✓' if _cp_ok else '✗'}")
    _details.append(f"回本時間 {'✓' if _pb_ok else '✗'}")
    st.markdown(f"""<div style="background:{_banner_bg}; border:1px solid {_banner_color}33;
        border-radius:8px; padding:10px 18px; margin:8px 0;
        display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.2em;">{_banner_icon}</span>
        <span style="color:{_banner_color}; font-weight:600; font-size:0.95em;">
            {_banner_msg}</span>
        <span style="color:#888; font-size:0.85em; margin-left:auto;">
            {'　'.join(_details)}</span>
    </div>""", unsafe_allow_html=True)

    _render_big_numbers(metrics, params)

    # --- F. Before/After ---
    if 'prev_metrics' in st.session_state and st.session_state.prev_metrics:
        _render_before_after(st.session_state.prev_metrics, metrics)

    st.divider()

    # --- C. J-Curve ---
    st.markdown("#### 25 年賺賠走勢圖")
    st.caption("藍色粗線＝最可能的情況。淺藍區域＝不確定範圍。零線以上＝賺（綠底），以下＝賠（紅底）。灰色虛線＝如果這筆錢拿去做別的投資。")
    _render_jcurve(mc, params, years)
    with st.expander("AI 解讀", expanded=False):
        render_haiku_insight('jcurve', insights)
        render_chart_qa('jcurve', '25年賺賠走勢', params, r, _api_key)

    # --- D. Waterfall ---
    st.markdown("#### 25 年收支分解")
    st.caption("這張圖分解「為什麼賺/為什麼賠」——綠色是收入來源，紅色是支出項目，最右邊是淨結果。")
    _render_waterfall(r)
    with st.expander("AI 解讀", expanded=False):
        render_haiku_insight('waterfall', insights)
        render_chart_qa('waterfall', '25年收支分解', params, r, _api_key)

    # --- G. Occupancy (promoted to main area) ---
    st.markdown("#### 入住率走勢")
    st.caption("實線＝整體住滿程度。虛線＝各期。每次新期啟動，大量空房加入，整體會突然下降——這是正常現象。")
    _render_occupancy(r, params, years)
    with st.expander("AI 解讀", expanded=False):
        render_haiku_insight('occupancy', insights)
        render_chart_qa('occupancy', '入住率走勢', params, r, _api_key)

    # --- H. Phase Gantt ---
    with st.expander("分期啟動時程表", expanded=False):
        na = len(r.phase_activations)
        nt = params['total_phases']
        if na < nt:
            st.error(f"第 {na+1}-{nt} 期無法啟動。入住率未達 {params['phase_activation_threshold']:.0%} 門檻。"
                     f"8,000 戶計畫目前只能完成 {sum(params['phase_units'][:na]):,} 戶。")
        _render_gantt(r, params, years)

    # --- I. Stress Tests ---
    if stress:
        with st.expander("壓力測試（故意模擬 6 種最壞情況，看你的策略能不能撐住）", expanded=False):
            irr = metrics['irr_median']
            all_ok = all(d['survival_rate'] > 0.80 for d in stress.values())
            if all_ok and irr < 0:
                st.warning("壓力測試全部通過但報酬為負——全部通過是因為規模小到燒不完錢。")
            _render_stress(stress)

    # --- J. Market Capacity ---
    with st.expander("市場容量（客群還剩多少）", expanded=False):
        _render_market(r, params, years)
        render_haiku_insight('market', insights)
        render_chart_qa('market', '市場容量', params, r, _api_key)

    # --- K. Unit Economics ---
    with st.expander("單戶經濟（每戶賺多少）", expanded=False):
        _render_unit_econ(r, params)

    # --- L. Brand / Ops / Rules ---
    with st.expander("品牌·營運能力·風險規則", expanded=False):
        _render_technical(r, years)

    # --- M. Health Check ---
    with st.expander("健康檢查（12 項自動驗證）", expanded=False):
        _render_health(mc, params, stress)


# ============================================================
# Section implementations
# ============================================================

def _render_judgment(m, p, r):
    """A. Colored judgment box — premium palette."""
    irr = m['irr_median']
    na = len(r.phase_activations)
    nt = p['total_phases']

    # Premium color scheme: muted tones, never pure red/yellow
    if irr < 0 and na < nt * 0.5:
        border, bg, text_color, icon = '#8B4513', '#FAF6F1', '#5C3317', '⚠'
        msg = (f"以目前配置，專案 25 年無法回本（年化報酬率 {irr:.1%}，即每 100 元每年虧 {abs(irr)*100:.1f} 元），"
               f"且只有 {na}/{nt} 期能啟動。主要原因是入住速度不足以支撐後續分期。")
    elif irr < 0:
        border, bg, text_color, icon = '#8B4513', '#FAF6F1', '#5C3317', '⚠'
        msg = f"專案預計虧損（年化報酬率 {irr:.1%}，即每 100 元每年虧 {abs(irr)*100:.1f} 元），需調整收入結構或降低成本。"
    elif irr < 0.06:
        border, bg, text_color, icon = '#B08D57', '#F9F6F0', '#6B5B3E', '◐'
        msg = f"可行但回報偏低（年化報酬率 {irr:.1%}，即每 100 元每年賺 {abs(irr)*100:.1f} 元，行業標竿 8-10%）。有改善空間。"
    else:
        border, bg, text_color, icon = '#4A7C59', '#F2F8F4', '#2D5A3A', '✓'
        msg = f"回報合理（年化報酬率 {irr:.1%}，即每 100 元每年賺 {abs(irr)*100:.1f} 元）。"

    st.markdown(f"""<div style="background:{bg}; border-left:4px solid {border};
        padding:18px 24px; border-radius:6px; margin:12px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <span style="color:{text_color}; font-size:1.05em; font-weight:600;
            letter-spacing:0.01em; line-height:1.6;">
            {icon}&ensp;{msg}</span>
    </div>""", unsafe_allow_html=True)


def _render_big_numbers(m, p):
    """B. Three big numbers with scales."""
    c1, c2, c3 = st.columns(3)

    irr = m['irr_median']
    with c1:
        scale = "很差" if irr < 0.02 else ("偏低" if irr < 0.06 else ("合理" if irr < 0.10 else "優秀"))
        st.metric("年化報酬率（每年平均賺賠%）", f"{irr:.1%}",
                   help=GLOSSARY.get('IRR', ''))
        st.caption(f"每 100 元每年{'賺' if irr > 0 else '賠'} {abs(irr)*100:.1f} 元 · {scale}")

    cp = m['collapse_prob']
    with c2:
        scale = "安全" if cp < 0.10 else ("注意" if cp < 0.20 else "危險")
        st.metric("25 年資金危機機率", f"{cp:.1%}",
                   help=GLOSSARY.get('崩潰機率', ''))
        st.caption(f"模擬上千次不同情境的結果 · {scale}")

    pb = m['payback_median']
    with c3:
        if pb > 0:
            scale = "佳" if pb < 10 else ("偏慢" if pb < 15 else "太久")
            st.metric("回本時間", f"{pb:.1f} 年", help=GLOSSARY.get('回本時間', ''))
            st.caption(f"行業一般 10-15 年 · {scale}")
        else:
            st.metric("回本時間", "25 年內未回本", help=GLOSSARY.get('回本時間', ''))
            st.caption("需要調整策略")


def _render_before_after(prev, curr):
    """F. Before/after comparison."""
    st.markdown("##### 調整前後對比")
    c1, c2, c3 = st.columns(3)

    def _dm(col, label, old, new, fmt, inv=False):
        d = new - old
        arrow = "↑" if d > 0 else ("↓" if d < 0 else "—")
        arrow_c = ("+" if (d > 0) != inv else "-") if abs(d) > 0.001 else ""
        col.markdown(f"**{label}**: {fmt(old)} → {fmt(new)} {arrow} {arrow_c}")

    _dm(c1, "報酬率", prev['irr_median'], curr['irr_median'], lambda v: f"{v:.1%}")
    _dm(c2, "崩潰率", prev['collapse_prob'], curr['collapse_prob'], lambda v: f"{v:.1%}", inv=True)
    _dm(c3, "回本", prev['payback_median'], curr['payback_median'],
        lambda v: f"{v:.1f}年" if v > 0 else "未回本", inv=True)


def _render_jcurve(mc, p, years):
    """C. J-Curve fan chart with green/red zones."""
    pcts = mc['percentiles']
    fig = go.Figure()

    # Green/red background zones
    y_max = max(abs(pcts['P95'].max()), abs(pcts['P5'].min())) / 1e8 * 1.2
    fig.add_shape(type="rect", x0=0, x1=25, y0=0, y1=y_max,
                  fillcolor="rgba(39,174,96,0.05)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, x1=25, y0=-y_max, y1=0,
                  fillcolor="rgba(192,57,43,0.05)", line_width=0, layer="below")

    # Fan bands (use 億 = 1e8)
    fig.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([pcts['P5'], pcts['P95'][::-1]]) / 1e8,
        fill='toself', fillcolor='rgba(99,110,250,0.1)',
        line=dict(width=0), name='不確定範圍', showlegend=True, visible='legendonly'))
    fig.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([pcts['P25'], pcts['P75'][::-1]]) / 1e8,
        fill='toself', fillcolor='rgba(99,110,250,0.25)',
        line=dict(width=0), name='最可能落在這範圍', showlegend=True))

    # P50 line
    p50 = pcts['P50'] / 1e8
    fig.add_trace(go.Scatter(x=years, y=p50, line=dict(color='#636EFA', width=3),
                              name='最可能走勢'))

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="#A0522D", annotation_text="損益平衡線")

    # Breakeven annotation
    pos = np.where(p50 > 0)[0]
    if len(pos) > 0:
        bk_yr = pos[0] / 4
        fig.add_annotation(x=bk_yr, y=0, text=f"← 第 {bk_yr:.1f} 年回本",
                           showarrow=True, arrowhead=2, ax=-60, ay=-30)

    # Alternative investment
    alt_rate = p.get('alternative_investment_rate', 0.06)
    alt = abs(p50[0]) * ((1 + alt_rate) ** years - 1) if abs(p50[0]) > 0 else years * 0
    fig.add_trace(go.Scatter(x=years, y=alt, line=dict(color='gray', dash='dot', width=1),
                              name=f'如果拿去做其他投資（年報酬 {alt_rate:.0%}）'))

    # 25-year endpoint
    fig.add_annotation(x=25, y=p50[-1], text=f"第 25 年：{p50[-1]*10:.0f} 億台幣",
                       showarrow=True, arrowhead=2, ax=-50, ay=-20)

    fig.update_layout(xaxis_title="年", yaxis_title="累計現金流（億台幣）",
                      height=500, margin=dict(l=60, r=20, t=30, b=50),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=14)),
                      hovermode='x unified')
    st.plotly_chart(_styled(fig), width='stretch')


def _render_waterfall(r):
    """D. Waterfall chart -- 25-year cashflow decomposition."""
    categories = ['押金收入', '月費收入', '其他收入', '建設成本', '營運成本', '退費支出', '資金利息', '淨結果']
    values = [
        r.cf_deposit_income.sum(), r.cf_monthly_fee.sum(), r.cf_other_revenue.sum(),
        -r.cf_construction.sum(), -r.cf_operating.sum(), -r.cf_refund.sum(), -r.cf_capital_cost.sum(),
    ]
    net = sum(values)
    measures = ['relative'] * 7 + ['total']
    values.append(net)

    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measures,
        x=categories, y=[v / 1e8 for v in values],
        connector=dict(line=dict(color="rgb(63,63,63)")),
        increasing=dict(marker_color="#4A7C59"),
        decreasing=dict(marker_color="#8B4513"),
        totals=dict(marker_color="#2980b9"),
        text=[fmt_billion_short(v) for v in values],
        textposition="outside",
    ))
    fig.update_layout(yaxis_title="億台幣", height=400,
                      margin=dict(l=60, r=20, t=30, b=50), showlegend=False)
    st.plotly_chart(_styled(fig), width='stretch')


def _render_occupancy(r, p, years):
    """G. Occupancy chart with phase annotations."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=r.occupancy_rate * 100,
                              name='整體入住率', line=dict(width=2.5)))
    for pid, occ in r.phase_occupancy.items():
        if pid in r.phase_activations:
            fig.add_trace(go.Scatter(x=years, y=occ * 100,
                                      name=f'第{pid+1}期', line=dict(width=1, dash='dot'),
                                      visible='legendonly'))
    # Phase activation annotations
    for pid, q in r.phase_activations.items():
        if pid > 0:
            fig.add_vline(x=q / 4, line_dash="dot", line_color="gray")
            fig.add_annotation(x=q / 4, y=100, text=f"第{pid+1}期啟動",
                               showarrow=False, yshift=10, font=dict(size=13))

    fig.add_hline(y=85, line_dash="dash", line_color="orange", annotation_text="85% 警戒線")
    fig.add_hline(y=p['phase_activation_threshold'] * 100, line_dash="dash",
                  line_color="#A0522D", annotation_text=f"{p['phase_activation_threshold']:.0%} 啟動門檻")
    fig.update_layout(yaxis_title="入住率（%）", xaxis_title="年",
                      height=400, margin=dict(l=50, r=20, t=30, b=40))
    st.plotly_chart(_styled(fig), width='stretch')


def _render_gantt(r, p, years):
    """H. Phase Gantt chart."""
    fig = go.Figure()
    for pid in range(p['total_phases']):
        label = f"第{pid+1}期（{p['phase_units'][pid]}戶）"
        if pid in r.phase_activations:
            sq = r.phase_activations[pid]
            fig.add_trace(go.Bar(y=[label], x=[2], base=sq / 4, orientation='h',
                                  marker_color='#636EFA', name='建設' if pid == 0 else None,
                                  showlegend=(pid == 0)))
            fig.add_trace(go.Bar(y=[label], x=[25 - sq / 4 - 2], base=sq / 4 + 2,
                                  orientation='h', marker_color='#00CC96',
                                  name='營運中' if pid == 0 else None, showlegend=(pid == 0)))
        else:
            fig.add_trace(go.Bar(y=[label], x=[0], base=0, orientation='h',
                                  marker_color='#A0522D', name='未啟動' if pid == p['total_phases'] - 1 else None,
                                  showlegend=(pid == p['total_phases'] - 1)))
    fig.update_layout(barmode='overlay', xaxis_title="年", height=350,
                      margin=dict(l=140, r=20, t=30, b=40))
    st.plotly_chart(_styled(fig), width='stretch')


def _render_stress(stress):
    """I. Stress test results grid."""
    cols = st.columns(3)
    for i, (name, data) in enumerate(stress.items()):
        with cols[i % 3]:
            s = data['survival_rate']
            ic = "#22C55E" if s > 0.80 else ("#F59E0B" if s > 0.50 else "#EF4444")
            st.markdown(f'<span style="color:{ic}">&#9679;</span> **{name}**', unsafe_allow_html=True)
            st.markdown(f"不倒閉的機率: **{s:.0%}**")
            st.caption(data['description'])
            if data['fail_quarter_median'] is not None:
                st.caption(f"如果撐不住，平均在第 {data['fail_quarter_median']/4:.1f} 年出問題")


def _render_market(r, p, years):
    """J. Market capacity consumption."""
    st.caption(f"目標客群共 {p.get('target_pool', 35000):,} 人。若客群快速耗盡，後期入住將減速。")
    consumed_pct = 1 - r.market_pool_remaining / p['target_pool']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=consumed_pct * 100, name='潛在客群已消耗比例',
                              line=dict(color='#636EFA', width=2)))
    fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="70% 警戒")
    fig.add_hline(y=100, line_dash="dash", line_color="#A0522D", annotation_text="100% 耗盡")
    fig.update_layout(yaxis_title="市場已消耗（%）", xaxis_title="年",
                      yaxis_range=[0, 120], height=350,
                      margin=dict(l=50, r=20, t=30, b=40))
    st.plotly_chart(_styled(fig), width='stretch')


def _render_unit_econ(r, p):
    """K. Unit economics."""
    avg_stay = 10
    ltv = p['monthly_fee'] * 12 * avg_stay + p['deposit_amount'] * (1 - p['refund_percentage'] * 0.5)
    svc = p['avg_staff_cost_monthly'] * p['staff_ratio'] * p['suao_labor_premium'] * 12 * avg_stay
    net_ltv = ltv - svc
    total_movin = r.new_move_ins.sum()
    cac = p['marketing_budget_monthly'] * 300 / max(1, total_movin)
    ratio = net_ltv / max(1, cac)

    c1, c2, c3 = st.columns(3)
    c1.metric("每戶終身收入（淨）", fmt_billion(net_ltv), help=GLOSSARY.get('LTV', ''))
    c2.metric("每戶招募成本", fmt_billion(cac), help=GLOSSARY.get('CAC', ''))
    scale = "健康" if ratio > 3 else ("偏低" if ratio > 1 else "危險")
    c3.metric("收入 / 招募成本比", f"{ratio:.1f} 倍（{scale}）", help=GLOSSARY.get('LTV/CAC', ''))
    st.caption(f"{ratio:.1f} 倍（健康標準：大於 3 倍。比值越高，獲客投資回報越大）")


def _render_technical(r, years):
    """L. Brand + ops + rules panel."""
    t1, t2, t3 = st.tabs(["品牌", "營運", "風險規則"])
    with t1:
        st.caption("品牌信任 = 潛在住戶對社區的信心（0-100 分）。品牌活力 = 對新客群的吸引力。")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=r.brand_trust, name='品牌信任'))
        fig.add_trace(go.Scatter(x=years, y=r.brand_vitality, name='品牌活力'))
        fig.add_hline(y=50, line_dash="dot", line_color="orange", annotation_text="50 分 = 基準線")
        fig.update_layout(yaxis_title="分數（0-100）", xaxis_title="年", height=300, yaxis_range=[0, 100])
        st.plotly_chart(_styled(fig), width='stretch')
    with t2:
        st.caption("營運能力 = 日常管理的水準（0-100 分）。越有經驗分數越高。")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=r.operational_capability, name='營運能力'))
        fig.add_hline(y=40, line_dash="dot", line_color="#A0522D", annotation_text="40 分 = 危險線")
        fig.update_layout(yaxis_title="分數（0-100）", xaxis_title="年", height=300, yaxis_range=[0, 100])
        st.plotly_chart(_styled(fig), width='stretch')
    with t3:
        st.caption("綠色 = 安全、黃色 = 接近觸發、紅色 = 已觸發、藍色 = 正向循環已啟動")
        final = r.rules_status[-1]
        for i, name in enumerate(RULE_NAMES):
            s = final[i]
            clr = "#22C55E" if s == 0 else ("#F59E0B" if s == 1 else ("#3B82F6" if "正向" in name or "循環" in name else "#EF4444"))
            st.markdown(f'<span style="color:{clr}">&#9679;</span> {name}', unsafe_allow_html=True)


def _render_health(mc, params, stress):
    """M. Health check panel."""
    checks = run_health_checks(mc, params, stress)
    n_pass = sum(1 for c in checks if c['status'] == 'pass')
    n_total = len(checks)

    # Summary score line
    if n_pass == n_total:
        _h_color = "#22C55E"
    elif n_pass >= n_total * 0.7:
        _h_color = "#F59E0B"
    else:
        _h_color = "#EF4444"
    st.markdown(f'<div style="font-size:1.1em; font-weight:600; margin-bottom:8px;">'
                f'<span style="color:{_h_color};">健康分數：{n_pass}/{n_total} 通過</span></div>',
                unsafe_allow_html=True)

    with st.expander("查看 12 項詳細檢查"):
        cols = st.columns(3)
        for i, c in enumerate(checks):
            with cols[i % 3]:
                icon_clr = "#22C55E" if c['status'] == 'pass' else ("#F59E0B" if c['status'] == 'warn' else "#EF4444")
                st.markdown(f'<span style="color:{icon_clr}">&#9679;</span> **{c["name"]}**', unsafe_allow_html=True)
                st.caption(f"{c['value']} / 標準: {c['threshold']}")
                if c['status'] != 'pass':
                    st.caption(c['explanation'])


# ============================================================
# Single-run preview (instant, before MC is triggered)
# ============================================================

def render_dashboard_single(r, params):
    """Lightweight dashboard from a single deterministic run.
    Shows immediately when user adjusts parameters, before MC is triggered."""
    # Get API key for chart Q&A
    _api_key = (st.session_state.get('user_api_key')
                or os.environ.get('ANTHROPIC_API_KEY', ''))
    try:
        _api_key = _api_key or st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    years = np.arange(100) / 4
    na = len(r.phase_activations)
    nt = params['total_phases']

    # --- Quick judgment ---
    final_cf = r.cumulative_cashflow[-1]
    cf_yi = fmt_billion_short(abs(final_cf))
    if final_cf < 0 and na < nt * 0.5:
        border, bg, text_color = '#8B4513', '#FAF6F1', '#5C3317'
        msg = f"預覽：目前配置 25 年累計虧損 {cf_yi}，只有 {na}/{nt} 期能啟動。點擊「開始模擬」看完整分析。"
    elif final_cf < 0:
        border, bg, text_color = '#8B4513', '#FAF6F1', '#5C3317'
        msg = f"預覽：25 年累計虧損 {cf_yi}。點擊「開始模擬」看完整分析。"
    elif final_cf < params['total_budget'] * 0.1:
        border, bg, text_color = '#B08D57', '#F9F6F0', '#6B5B3E'
        msg = f"預覽：25 年累計獲利 {cf_yi}，但相對投入偏低。"
    else:
        border, bg, text_color = '#4A7C59', '#F2F8F4', '#2D5A3A'
        msg = f"預覽：25 年累計獲利 {cf_yi}。"

    st.markdown(f"""<div style="background:{bg}; border-left:4px solid {border};
        padding:18px 24px; border-radius:6px; margin:12px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <span style="color:{text_color}; font-size:1.05em; font-weight:600;
            letter-spacing:0.01em; line-height:1.6;">{msg}</span>
    </div>""", unsafe_allow_html=True)

    # --- Quick numbers ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("最終入住率", f"{r.occupancy_rate[-1]:.0%}")
    with c2:
        st.metric("啟動期數", f"{na} / {nt} 期")
    with c3:
        st.metric("25 年累計現金流", fmt_billion_short(final_cf))

    # --- J-curve (single run, no fan) ---
    st.markdown("#### 25 年賺賠走勢（單次預覽）")
    st.caption("這是固定參數的單次模擬。點「開始模擬」跑千次隨機情境看完整分布。")

    fig = go.Figure()
    cf_yi_arr = r.cumulative_cashflow / 1e8  # 億
    fig.add_trace(go.Scatter(x=years, y=cf_yi_arr, line=dict(color='#636EFA', width=2.5),
                              name='累計現金流'))
    fig.add_hline(y=0, line_dash="dash", line_color="#A0522D", annotation_text="損益平衡線")

    # Breakeven
    pos = np.where(cf_yi_arr > 0)[0]
    if len(pos) > 0:
        bk = pos[0] / 4
        fig.add_annotation(x=bk, y=0, text=f"← 第 {bk:.1f} 年回本",
                           showarrow=True, arrowhead=2, ax=-60, ay=-30)

    fig.update_layout(xaxis_title="年", yaxis_title="億台幣",
                      height=400, margin=dict(l=60, r=20, t=30, b=50))
    st.plotly_chart(_styled(fig), width='stretch')
    render_chart_qa('jcurve_s', '25年賺賠走勢', params, r, _api_key)

    # --- Waterfall ---
    st.markdown("#### 收支分解")
    _render_waterfall(r)
    render_chart_qa('waterfall_s', '收支分解', params, r, _api_key)

    # --- Occupancy ---
    st.markdown("#### 入住率走勢")
    _render_occupancy(r, params, years)
    render_chart_qa('occupancy_s', '入住率走勢', params, r, _api_key)

    # --- Phase status ---
    if na < nt:
        st.warning(f"第 {na+1}-{nt} 期無法啟動。"
                   f"8,000 戶計畫目前只能完成 {sum(params['phase_units'][:na]):,} 戶。")
