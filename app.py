"""
養生造鎮決策模擬器 v4 — Premium Edition
"""

import streamlit as st
import numpy as np
import os
import sys

# Version tag: force clear stale AI caches when code updates
_APP_VERSION = "v4.7"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env):
    for line in open(_env, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from engine.model import run_simulation
from engine.monte_carlo import run_monte_carlo, extract_metrics, run_stress_tests
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard, render_dashboard_single
from ui.ai_analysis import render_ai_analysis
from ui.methodology import render_methodology

st.set_page_config(
    page_title="養生造鎮決策模擬器",
    page_icon=":house:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Load premium CSS theme
# ============================================================
_css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'theme.css')
if os.path.exists(_css_path):
    with open(_css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================
st.markdown("""
<div style="text-align:center;padding:12px 0 4px;">
    <h1 style="font-family:'Noto Serif TC',serif;color:#2c2c2c;font-size:2.2em;
        margin:0;letter-spacing:0.06em;">養生造鎮決策模擬器</h1>
    <p style="color:#8b7355;font-size:0.95em;margin:6px 0 0;letter-spacing:0.1em;">
        華友聯 · 宜蘭蘇澳 · 8,000 戶 · 25 年蒙地卡羅模擬 · v2.0</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 使用指南 — 卡片式設計
# ============================================================
with st.expander("如何使用這個模擬器？", expanded=True):
    # Card navigation
    st.markdown("""
    <div class="guide-card-grid">
        <div class="guide-card">
            <span class="guide-card-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c9a96e" stroke-width="2">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
            </span>
            <div class="guide-card-title">快速上手</div>
            <div class="guide-card-desc">三步驟開始使用</div>
        </div>
        <div class="guide-card">
            <span class="guide-card-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c9a96e" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                </svg>
            </span>
            <div class="guide-card-title">計算原理</div>
            <div class="guide-card-desc">模型如何計算</div>
        </div>
        <div class="guide-card">
            <span class="guide-card-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c9a96e" stroke-width="2">
                    <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
            </span>
            <div class="guide-card-title">圖表怎麼看</div>
            <div class="guide-card-desc">讀懂每張圖表</div>
        </div>
        <div class="guide-card">
            <span class="guide-card-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#c9a96e" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
                </svg>
            </span>
            <div class="guide-card-title">策略怎麼選</div>
            <div class="guide-card-desc">最佳操作順序</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_start, tab_logic, tab_charts, tab_choose = st.tabs([
        "快速上手", "計算原理", "圖表怎麼看", "策略怎麼選",
    ])

    with tab_start:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
<div style="background:white;border:1px solid #e8e0d4;border-radius:12px;padding:20px;height:100%;">
<h4 style="color:#c9a96e;margin-top:0;">Step 1 — 調策略</h4>

左邊面板有 **5 組控制桿**：

| 組別 | 在決定什麼 |
|------|----------|
| 💰 資本與財務 | 錢從哪來、押金怎麼退 |
| 🚀 需求引擎 | 怎麼讓人來住 |
| 🏥 產品與營運 | 蓋什麼、誰來管 |
| 📅 開發節奏 | 蓋幾期、怎麼防老化 |
| 🌐 外部環境 | 外面世界會怎樣 |
</div>
""", unsafe_allow_html=True)

        with c2:
            st.markdown("""
<div style="background:white;border:1px solid #e8e0d4;border-radius:12px;padding:20px;height:100%;">
<h4 style="color:#c9a96e;margin-top:0;">Step 2 — 看預覽</h4>

每次調完參數，右邊**立刻更新**：

- 最上方**彩色判斷框** → 結論
- **三個大數字** → 最重要的指標
- **走勢圖** → 25 年的趨勢

這是「固定運氣」的快速預覽，適合比較不同策略。
</div>
""", unsafe_allow_html=True)

        with c3:
            st.markdown("""
<div style="background:white;border:1px solid #e8e0d4;border-radius:12px;padding:20px;height:100%;">
<h4 style="color:#c9a96e;margin-top:0;">Step 3 — 跑模擬</h4>

策略調好後，點「**開始蒙地卡羅模擬**」：

- **1000 種不同運氣**的模擬
- **6 組壓力測試**（經濟崩盤等）
- **12 項健康檢查**

跑完後可啟動 **AI 顧問分析**。
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div style="background:linear-gradient(135deg,#f8f4f0,#f0ebe4);border-radius:10px;
    padding:14px 20px;margin:16px 0;border-left:4px solid #c9a96e;">
    <span style="color:#8b7355;font-size:0.9em;">
    💡 <b>預設值是最保守的「什麼都沒開」配置。</b>結果通常是虧損——這是正常的。
    目的是讓你看到「不做任何事」的後果，然後一步步加上配套看改善多少。
    </span>
</div>
""", unsafe_allow_html=True)

    with tab_logic:
        st.markdown("""
### 計算原理

模擬器把未來 **25 年切成 100 個季度**，每一季依序計算 5 件事：
""")

        with st.container():
            st.markdown("""
**1️⃣ 這一季有多少新住戶來？**

```
新入住 = 基礎需求 × 品牌信任 × 保險通路 × 冷啟動
         × 經濟好壞 × 距離摩擦 × 體驗行銷
         × 醫療加成 × 溫泉加成 × 市場剩餘量
         + H會館導入
```

- **基礎需求**：大台北 35,000 高淨值長者，每年 0.5% 考慮入住 ≈ 每季 44 戶潛在需求
- **品牌信任**（0-100）：30 分 = 60% 需求，60 分 = 100%
- **冷啟動**：住到 800 戶後需求才達正常水準

**2️⃣ 這一季有多少住戶離開？**

| 原因 | 年化比率 | 說明 |
|------|---------|------|
| 自然死亡 | 1.2%-16% | 依年齡，65 歲 1.2%、90 歲 16% |
| 自願搬走 | 3% | 搬去離子女更近等 |
| 轉介護棟 | 2%-15% | 75 歲以下 2%、85+ 15% |

**3️⃣ 錢怎麼進出？**  收入 = 押金 + 月費 + 其他。支出 = 建設 + 營運 + 退費 + 利息。

**4️⃣ 品牌信任怎麼變？**  加分（口碑 +2/季、信託等級 ×1.5/季）vs 減分（衰退 -0.3/季、負面事件）。

**5️⃣ 下一期能否啟動？**  入住率 ≥ 80% + 儲備 ≥ 250 天 + 建設金 ≥ 30%，三條件同時滿足。
""")

        st.markdown("""
---
**蒙地卡羅模擬** = 上面跑 **1,000 遍**，每遍給不同的「運氣」。看結果分布。
""")

    with tab_charts:
        st.markdown("""
### 圖表說明

| 圖表 | 怎麼看 | 關鍵指標 |
|------|--------|---------|
| **判斷框** | 紅=虧損、黃=偏弱、綠=合理 | 一句話結論 |
| **三個大數字** | 報酬率/危機率/回本 | 加好壞標尺 |
| **25年走勢圖** | 藍線=最可能、淺藍=範圍 | 何時回本 |
| **收支分解** | 綠柱=收入、紅柱=支出 | 哪項最大 |
| **入住率** | 實線=整體、虛線=各期 | 85%警戒線 |
| **壓力測試** | 6種壞事的存活率 | >80%安全 |
| **健康檢查** | 12項自動驗證 | 全綠=可信 |
""")

    with tab_choose:
        st.markdown("""
### 建議操作順序

| 步驟 | 操作 | 預期效果 |
|------|------|---------|
| 1 | 先看預設結果 | 了解「裸配置」有多慘 |
| 2 | ✅ 勾選「保險綁定」 | 報酬率大幅改善 |
| 3 | 押金保護 →「獨立信託+審批」 | 品牌信任穩定 |
| 4 | 醫療 →「區域醫院合作」 | 入住率 +15% |
| 5 | 溫泉 →「高規格湯屋」 | 品牌差異化 +20% |
| 6 | 點「開始蒙地卡羅模擬」 | 看完整分布 |

---

**核心概念：配套一起開才有效（飛輪效應）**

信任高 → 來的人多 → 入住率高 → 口碑好 → 信任更高 → …（正循環）

預設配置（什麼都沒開）是虧損的。同時開啟 **保險 + 信託 + 醫療**，結果會翻轉。
""")


def _params_hash(params):
    items = []
    for k, v in sorted(params.items()):
        if k.startswith('_'):
            continue
        if isinstance(v, (list, tuple)):
            items.append((k, tuple(v)))
        elif isinstance(v, dict):
            items.append((k, tuple(sorted(v.items()))))
        else:
            items.append((k, v))
    return hash(tuple(items))


# --- Sidebar ---
params = render_sidebar()
mc_runs = params.pop('_mc_runs', 1000)

# === Layer 1: 單次模擬（即時） ===
single = run_simulation(params, rng=np.random.RandomState(42))

# === Layer 2: MC 按鈕區 + 蒙地卡羅視覺介紹 ===
st.markdown(f"""
<div style="background:linear-gradient(135deg, #fdfcfa 0%, #f8f3ec 100%);
    border:2px solid #d4b896;border-radius:16px;padding:32px 36px;margin:24px 0;
    box-shadow:0 4px 20px rgba(176,141,87,0.12);">

  <div style="text-align:center;margin-bottom:20px;">
    <span style="font-size:32px;letter-spacing:2px;">🎲</span>
    <h3 style="font-size:22px;font-weight:700;color:#1d1d1f;margin:8px 0 4px;
        letter-spacing:0.02em;">蒙地卡羅模擬</h3>
    <p style="font-size:13px;color:#8b7355;margin:0;letter-spacing:0.06em;">
        MONTE CARLO SIMULATION</p>
  </div>

  <div style="display:flex;gap:16px;margin:20px 0 24px;">
    <div style="flex:1;background:white;border-radius:12px;padding:16px;text-align:center;
        border:1px solid #e8ddd0;">
      <div style="font-size:28px;font-weight:700;color:#b08d57;">1</div>
      <div style="font-size:13px;color:#6e6e73;line-height:1.5;margin-top:4px;">
        上方的結果是<br><strong style="color:#1d1d1f;">固定運氣</strong>的單次預覽</div>
    </div>
    <div style="flex:1;background:white;border-radius:12px;padding:16px;text-align:center;
        border:1px solid #e8ddd0;">
      <div style="font-size:28px;font-weight:700;color:#b08d57;">{mc_runs:,}</div>
      <div style="font-size:13px;color:#6e6e73;line-height:1.5;margin-top:4px;">
        蒙地卡羅跑<br><strong style="color:#1d1d1f;">{mc_runs:,} 種不同運氣</strong></div>
    </div>
    <div style="flex:1;background:white;border-radius:12px;padding:16px;text-align:center;
        border:1px solid #e8ddd0;">
      <div style="font-size:28px;font-weight:700;color:#b08d57;">?%</div>
      <div style="font-size:13px;color:#6e6e73;line-height:1.5;margin-top:4px;">
        告訴你<br><strong style="color:#1d1d1f;">賺和賠的機率</strong>各多少</div>
    </div>
  </div>

  <p style="font-size:14px;color:#6e6e73;text-align:center;line-height:1.7;margin:0 0 8px;">
    經濟衰退、住戶突然退出、利率飆升⋯⋯這些「壞運氣」不一定會發生，但<strong style="color:#1d1d1f;">可能</strong>會。<br>
    蒙地卡羅把每種可能都跑一遍，讓你知道：<strong style="color:#b08d57;">最好、最壞、最可能</strong>的結果分別是什麼。
  </p>

</div>
""", unsafe_allow_html=True)

col_l, col_btn, col_r = st.columns([1, 2, 1])
with col_btn:
    run_mc = st.button(
        f"開始蒙地卡羅模擬（{mc_runs:,} 次）",
        type="primary",
        use_container_width=True,
    )

if 'mc' in st.session_state:
    st.markdown('<p style="text-align:center;color:#86868b;font-size:13px;margin:4px 0 0;">✓ 已有模擬結果。調整參數後再次點擊可更新。</p>', unsafe_allow_html=True)

# Force clear stale caches when app version changes
if st.session_state.get('_app_version') != _APP_VERSION:
    for k in ['haiku_insights', 'haiku_summary', 'opus_report', 'mc', 'stress',
              'consultant_history', 'current_metrics', 'prev_metrics']:
        st.session_state.pop(k, None)
    # Also clear per-chart chat histories
    for k in list(st.session_state.keys()):
        if k.startswith('chart_chat_'):
            del st.session_state[k]
    st.session_state['_app_version'] = _APP_VERSION

mc = st.session_state.get('mc')
stress = st.session_state.get('stress')

if run_mc:
    if 'current_metrics' in st.session_state:
        st.session_state.prev_metrics = st.session_state.current_metrics
    # Clear AI caches so new insights are generated
    st.session_state.pop('haiku_insights', None)
    st.session_state.pop('haiku_summary', None)
    st.session_state.pop('opus_report', None)

    # --- 模擬等待期間的小知識輪播（隨機 + 配圖 + 閱讀速度） ---
    import time
    from ui.tip_carousel import get_shuffled_tips, render_tip_card

    tips = get_shuffled_tips()
    tip_box = st.empty()
    progress_bar = st.progress(0, text=f"正在模擬 {mc_runs:,} 種不同情境...")
    _tip_state = [0, time.time()]  # [current_index, last_switch_time]
    TIP_INTERVAL = 8  # 秒 — 正常閱讀速度

    def _show_tip(idx):
        tid, title, body = tips[idx % len(tips)]
        html = render_tip_card(tid, title, body, idx % len(tips), len(tips), "模擬進行中")
        tip_box.markdown(html, unsafe_allow_html=True)

    def _on_progress(done, total):
        pct = int(done / total * 70)
        progress_bar.progress(pct, text=f"已完成 {done:,} / {total:,} 次模擬...")
        # 基於時間輪播，不基於進度
        now = time.time()
        if now - _tip_state[1] >= TIP_INTERVAL:
            _tip_state[0] += 1
            _tip_state[1] = now
            _show_tip(_tip_state[0])

    _show_tip(0)
    mc = run_monte_carlo(params, n_runs=mc_runs, seed=42, progress_callback=_on_progress)
    metrics = extract_metrics(mc)
    mc['_metrics'] = metrics
    progress_bar.progress(70, text="模擬完成！正在跑壓力測試...")

    with st.spinner("正在跑 6 組壓力測試（故意模擬壞事發生）..."):
        stress = run_stress_tests(params, n_runs=200)

    progress_bar.progress(100, text="完成！正在生成分析報告...")
    tip_box.empty()  # 模擬完成後清除提示
    progress_bar.empty()

    st.session_state.mc = mc
    st.session_state.stress = stress
    st.session_state.current_metrics = metrics
    st.session_state.current_params = dict(params)

# === Dashboard ===
if mc is not None:
    metrics = mc['_metrics']
    render_dashboard(mc, params, stress)
else:
    render_dashboard_single(single, params)

# === Tabs: AI Analysis + Methodology ===
tab_ai, tab_method = st.tabs(["🤖 AI 分析報告", "📐 方法論"])

with tab_ai:
    render_ai_analysis(params, mc=mc, stress=stress)

with tab_method:
    render_methodology()

# --- Footer ---
st.markdown(f"""
<div class="footer-text">
    所有數值為模擬結果，僅供決策參考。金額：新台幣 | 時間步長：每季 | 模擬期：25 年。
    <span style="color:#c0c0c0;font-size:11px;">{_APP_VERSION}</span>
</div>
""", unsafe_allow_html=True)
