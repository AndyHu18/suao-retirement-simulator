"""
Dashboard output: 3-layer visualization.
Layer 1: Big numbers + J-curve + before/after comparison
Layer 2: Stress tests, Gantt, market capacity, tornado, unit economics
Layer 3: Occupancy trajectory, brand vitality, ops capability, rules panel
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from utils.formatting import fmt_billion, fmt_pct, fmt_years, RULE_NAMES


def render_dashboard(mc_result, params, stress_results=None):
    """Render the full dashboard."""
    _render_layer1(mc_result, params)
    _render_layer2(mc_result, params, stress_results)
    _render_layer3(mc_result, params)


def _render_layer1(mc, params):
    """Layer 1: Big numbers + J-curve (must fit in first screen)."""
    metrics = mc['_metrics']
    st.markdown("---")

    # --- 3 Big Numbers ---
    col1, col2, col3 = st.columns(3)

    with col1:
        irr = metrics['irr_median']
        irr_color = "green" if irr > 0.05 else ("orange" if irr > 0 else "red")
        st.metric(
            "IRR 中位數",
            f"{irr:.1%}",
            help="內部報酬率（含殘值）",
        )

    with col2:
        cp = mc['collapse_prob']
        cp_color = "🟢" if cp < 0.10 else ("🟡" if cp < 0.20 else "🔴")
        st.metric(
            f"崩潰機率 {cp_color}",
            f"{cp:.1%}",
            help="25年內資金小於零的機率",
        )

    with col3:
        pb = metrics['payback_median']
        never_pct = metrics.get('payback_never_pct', 0)
        pb_label = fmt_years(pb * 4) if pb > 0 else "未回本"
        pb_help = "累計現金流持續為正的起始年份（非首次轉正）"
        if never_pct > 0:
            pb_help += f"　|　{never_pct:.0%} 的模擬永不回本"
        st.metric("回本時間中位數", pb_label, help=pb_help)

    # --- Before/After Comparison ---
    if 'prev_metrics' in st.session_state and st.session_state.prev_metrics:
        prev = st.session_state.prev_metrics
        st.markdown("#### 決策前後對比")
        c1, c2, c3, c4 = st.columns(4)
        _delta_metric(c1, "IRR", prev['irr_median'], irr, fmt_pct_val)
        _delta_metric(c2, "崩潰機率", prev['collapse_prob'], cp, fmt_pct_val, invert=True)
        _delta_metric(c3, "回本時間", prev['payback_median'], pb, lambda x: f"{x:.1f}年", invert=True)
        _delta_metric(c4, "最大資金需求", prev['max_funding_need'],
                      metrics['max_funding_need'], lambda x: fmt_billion(x))

    # --- J-Curve Fan Chart ---
    st.markdown("#### J 曲線 — 累計現金流")

    years = np.arange(100) / 4
    pcts = mc['percentiles']

    fig = go.Figure()

    # Fan bands
    fig.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([pcts['P5'], pcts['P95'][::-1]]) / 1e9,
        fill='toself', fillcolor='rgba(99,110,250,0.1)',
        line=dict(width=0), name='P5-P95', showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([pcts['P25'], pcts['P75'][::-1]]) / 1e9,
        fill='toself', fillcolor='rgba(99,110,250,0.25)',
        line=dict(width=0), name='P25-P75', showlegend=True,
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=years, y=pcts['P50'] / 1e9,
        line=dict(color='#636EFA', width=3),
        name='中位數 (P50)',
    ))

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="red",
                  annotation_text="回本線")

    # Alternative investment baseline
    alt_rate = params['alternative_investment_rate']
    initial_invest = abs(pcts['P50'][0])
    alt_line = initial_invest * ((1 + alt_rate) ** years - 1) / 1e9
    fig.add_trace(go.Scatter(
        x=years, y=alt_line,
        line=dict(color='gray', width=1, dash='dot'),
        name=f'替代投資 ({alt_rate:.0%}/年)',
    ))

    fig.update_layout(
        xaxis_title="年",
        yaxis_title="累計現金流（十億 TWD）",
        height=500,
        margin=dict(l=60, r=20, t=30, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode='x unified',
    )
    st.plotly_chart(fig, width='stretch')


def _render_layer2(mc, params, stress_results):
    """Layer 2: Expandable deep analysis."""

    # --- Stress Test Results ---
    if stress_results:
        with st.expander("🔥 壓力測試結果", expanded=False):
            cols = st.columns(3)
            for i, (name, data) in enumerate(stress_results.items()):
                with cols[i % 3]:
                    surv = data['survival_rate']
                    color = "🟢" if surv > 0.80 else ("🟡" if surv > 0.50 else "🔴")
                    st.markdown(f"**{color} {name}**")
                    st.markdown(f"存活率: **{surv:.0%}**")
                    st.caption(data['description'])
                    if data['fail_quarter_median'] is not None:
                        st.caption(f"中位失敗: 第{data['fail_quarter_median']/4:.1f}年")

    # --- Phase Activation Gantt ---
    with st.expander("📊 分期啟動甘特圖", expanded=False):
        _render_gantt(mc, params)

    # --- Market Capacity ---
    with st.expander("📈 市場容量消耗曲線", expanded=False):
        _render_market_capacity(mc, params)

    # --- Tornado Chart ---
    with st.expander("🌪️ 敏感度龍捲風圖", expanded=False):
        st.info("調整參數後重新執行以生成敏感度分析")
        if '_tornado_data' in mc:
            _render_tornado(mc['_tornado_data'])

    # --- Unit Economics ---
    with st.expander("💵 單戶經濟模型", expanded=False):
        _render_unit_economics(mc, params)


def _render_layer3(mc, params):
    """Layer 3: Technical support charts."""

    with st.expander("📉 技術指標面板", expanded=False):
        # Tabs for different metrics
        tab1, tab2, tab3, tab4 = st.tabs([
            "入住率軌跡", "品牌活力", "營運能力", "規則觸發"
        ])

        # Use median run for display
        median_idx = np.argsort(mc['cf_curves'][:, -1])[len(mc['cf_curves']) // 2]
        r = mc['results'][median_idx]
        years = np.arange(100) / 4

        with tab1:
            fig = go.Figure()
            # Overall occupancy
            fig.add_trace(go.Scatter(
                x=years, y=r.occupancy_rate * 100,
                name='整體入住率', line=dict(width=2),
            ))
            # Per-phase occupancy
            for pid, occ_arr in r.phase_occupancy.items():
                if pid in r.phase_activations:
                    fig.add_trace(go.Scatter(
                        x=years, y=occ_arr * 100,
                        name=f'第{pid+1}期',
                        line=dict(width=1, dash='dot'),
                    ))
            fig.add_hline(y=85, line_dash="dash", line_color="orange",
                          annotation_text="85% 警戒線")
            fig.update_layout(
                yaxis_title="入住率（%）", xaxis_title="年",
                height=350, margin=dict(l=50, r=20, t=30, b=40),
            )
            st.plotly_chart(fig, width='stretch')

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=r.brand_trust,
                name='品牌信任', line=dict(color='#AB63FA'),
            ))
            fig.add_trace(go.Scatter(
                x=years, y=r.brand_vitality,
                name='品牌活力', line=dict(color='#00CC96'),
            ))
            fig.update_layout(
                yaxis_title="指數", xaxis_title="年",
                height=350, margin=dict(l=50, r=20, t=30, b=40),
            )
            st.plotly_chart(fig, width='stretch')

        with tab3:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=r.operational_capability,
                name='營運能力', line=dict(color='#FFA15A'),
            ))
            fig.update_layout(
                yaxis_title="營運能力指數", xaxis_title="年",
                height=350, yaxis_range=[0, 100],
                margin=dict(l=50, r=20, t=30, b=40),
            )
            st.plotly_chart(fig, width='stretch')

        with tab4:
            _render_rules_panel(r)


def _render_gantt(mc, params):
    """Render phase activation timeline."""
    median_idx = np.argsort(mc['cf_curves'][:, -1])[len(mc['cf_curves']) // 2]
    r = mc['results'][median_idx]

    gantt_data = []
    for pid in range(params['total_phases']):
        if pid in r.phase_activations:
            start_q = r.phase_activations[pid]
            # Find when phase reaches 80% occupancy
            occ = r.phase_occupancy[pid]
            fill_q = start_q
            for t in range(start_q, 100):
                if occ[t] >= 0.80:
                    fill_q = t
                    break
            else:
                fill_q = 99

            gantt_data.append({
                'phase': f'第{pid+1}期 ({params["phase_units"][pid]}戶)',
                'start': start_q / 4,
                'build_end': (start_q + 8) / 4,
                'fill_end': fill_q / 4,
            })
        else:
            gantt_data.append({
                'phase': f'第{pid+1}期 ({params["phase_units"][pid]}戶)',
                'start': None,
                'build_end': None,
                'fill_end': None,
            })

    fig = go.Figure()
    for i, d in enumerate(gantt_data):
        if d['start'] is not None:
            # Construction bar
            fig.add_trace(go.Bar(
                y=[d['phase']], x=[d['build_end'] - d['start']],
                base=d['start'], orientation='h',
                marker_color='#636EFA', name='建設' if i == 0 else None,
                showlegend=(i == 0),
            ))
            # Fill-up bar
            fig.add_trace(go.Bar(
                y=[d['phase']], x=[d['fill_end'] - d['build_end']],
                base=d['build_end'], orientation='h',
                marker_color='#00CC96', name='填滿至80%' if i == 0 else None,
                showlegend=(i == 0),
            ))
        else:
            fig.add_trace(go.Bar(
                y=[d['phase']], x=[0], base=0, orientation='h',
                marker_color='lightgray',
                name='未啟動' if i == len(gantt_data) - 1 else None,
                showlegend=(i == len(gantt_data) - 1),
            ))

    fig.update_layout(
        barmode='overlay', xaxis_title="年",
        height=350, margin=dict(l=120, r=20, t=30, b=40),
    )
    st.plotly_chart(fig, width='stretch')


def _render_market_capacity(mc, params):
    """Market pool consumption curve."""
    median_idx = np.argsort(mc['cf_curves'][:, -1])[len(mc['cf_curves']) // 2]
    r = mc['results'][median_idx]
    years = np.arange(100) / 4

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=years, y=r.market_pool_remaining,
        name='剩餘市場容量', line=dict(color='#636EFA'),
    ), secondary_y=False)

    cumulative_movin = np.cumsum(r.new_move_ins)
    fig.add_trace(go.Scatter(
        x=years, y=cumulative_movin,
        name='累計入住', line=dict(color='#EF553B'),
    ), secondary_y=True)

    fig.add_hline(y=params['target_pool'] * 0.3,
                  line_dash="dash", line_color="orange",
                  annotation_text="30% 壓力線")

    fig.update_yaxes(title_text="剩餘市場容量", secondary_y=False)
    fig.update_yaxes(title_text="累計入住戶數", secondary_y=True)
    fig.update_layout(
        xaxis_title="年", height=350,
        margin=dict(l=60, r=60, t=30, b=40),
    )
    st.plotly_chart(fig, width='stretch')


def _render_tornado(tornado_data):
    """Tornado sensitivity chart."""
    if not tornado_data:
        return

    names = [d['name'] for d in tornado_data]
    low = [d['low'] for d in tornado_data]
    high = [d['high'] for d in tornado_data]
    base_irr = tornado_data[0].get('base', 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=[h - base_irr for h in high],
        base=base_irr, orientation='h',
        marker_color='#00CC96', name='+20%',
    ))
    fig.add_trace(go.Bar(
        y=names, x=[l - base_irr for l in low],
        base=base_irr, orientation='h',
        marker_color='#EF553B', name='-20%',
    ))
    fig.update_layout(
        barmode='overlay', xaxis_title="IRR 變化",
        height=400, margin=dict(l=150, r=20, t=30, b=40),
    )
    st.plotly_chart(fig, width='stretch')


def _render_unit_economics(mc, params):
    """Single-unit economics display."""
    # Estimate LTV and CAC from median run
    median_idx = np.argsort(mc['cf_curves'][:, -1])[len(mc['cf_curves']) // 2]
    r = mc['results'][median_idx]

    avg_stay_years = 10  # rough average
    monthly_fee = params['monthly_fee']
    deposit = params['deposit_amount']
    staff_cost_per_unit = (params['avg_staff_cost_monthly']
                           * params['staff_ratio']
                           * params['suao_labor_premium'])

    ltv = (monthly_fee * 12 * avg_stay_years
           + deposit * (1 - params['refund_percentage'] * 0.5))
    service_cost = staff_cost_per_unit * 12 * avg_stay_years
    net_ltv = ltv - service_cost

    total_movin = r.new_move_ins.sum()
    total_mkt = params['marketing_budget_monthly'] * 12 * 25
    cac = total_mkt / max(1, total_movin)

    ltv_cac = net_ltv / max(1, cac)

    col1, col2, col3 = st.columns(3)
    col1.metric("單戶 LTV（淨）", fmt_billion(net_ltv))
    col2.metric("CAC（客戶取得成本）", fmt_billion(cac))
    col3.metric("LTV / CAC", f"{ltv_cac:.1f}x")

    st.caption(f"假設平均停留 {avg_stay_years} 年 | "
               f"月費 {monthly_fee/1e4:.0f}萬 | "
               f"服務成本 {staff_cost_per_unit/1e4:.1f}萬/月")


def _render_rules_panel(r):
    """Show rule trigger status at end of simulation."""
    final_rules = r.rules_status[-1]

    for i, name in enumerate(RULE_NAMES):
        status = final_rules[i]
        if status == 0:
            st.markdown(f"🟢 {name}")
        elif status == 1:
            st.markdown(f"🟡 {name} — 接近觸發")
        else:
            if "✦" in name:
                st.markdown(f"🔵 {name} — 已啟動")
            else:
                st.markdown(f"🔴 {name} — 已觸發")


def _delta_metric(col, label, old_val, new_val, fmt_fn, invert=False):
    """Show before->after metric with delta."""
    delta = new_val - old_val
    if invert:
        delta_color = "inverse"
    else:
        delta_color = "normal"

    col.metric(
        label,
        fmt_fn(new_val),
        delta=f"{delta:+.2f}" if abs(delta) > 0.001 else "不變",
        delta_color=delta_color,
    )


def fmt_pct_val(v):
    return f"{v:.1%}"
