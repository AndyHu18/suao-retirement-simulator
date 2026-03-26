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

# Hero banner
_hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'hero_banner.png')
if os.path.exists(_hero_path):
    st.image(_hero_path, use_container_width=True)

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
<h4 style="color:#b08d57;margin-top:0;">Step 1 — 調策略</h4>

左邊面板有 **5 組控制桿**：

| 組別 | 在決定什麼 |
|------|----------|
| 資本與財務 | 錢從哪來、押金怎麼退 |
| 需求引擎 | 怎麼讓人來住 |
| 產品與營運 | 蓋什麼、誰來管 |
| 開發節奏 | 蓋幾期、怎麼防老化 |
| 外部環境 | 外面世界會怎樣 |
</div>
""", unsafe_allow_html=True)
        with c2:
            st.markdown("""
<div style="background:white;border:1px solid #e8e0d4;border-radius:12px;padding:20px;height:100%;">
<h4 style="color:#b08d57;margin-top:0;">Step 2 — 看預覽</h4>

每次調完參數，右邊**立刻更新**：

- 最上方**彩色判斷框** → 一句話結論
- **三個大數字** → 報酬率 / 危機率 / 回本年數
- **走勢圖** → 25 年的入住與現金流趨勢

這是「固定運氣」的快速預覽，適合 A/B 比較不同策略。
</div>
""", unsafe_allow_html=True)
        with c3:
            st.markdown("""
<div style="background:white;border:1px solid #e8e0d4;border-radius:12px;padding:20px;height:100%;">
<h4 style="color:#b08d57;margin-top:0;">Step 3 — 跑模擬</h4>

策略調好後，點「**開始蒙地卡羅模擬**」：

- **1,000 種不同運氣**的完整模擬
- **6 組壓力測試**（經濟崩盤、信任危機…）
- **12 項健康檢查** + 矛盾偵測
- 可啟動 **AI 顧問**做策略建議
</div>
""", unsafe_allow_html=True)
        st.markdown("""
<div style="background:linear-gradient(135deg,#f9f6f0,#f0ebe4);border-radius:10px;
    padding:14px 20px;margin:16px 0;border-left:4px solid #b08d57;">
    <span style="color:#8b7355;font-size:0.9em;">
    <b>預設值是最保守的「什麼都沒開」配置。</b>結果通常是虧損的——這是正常的，不是 bug。
    目的是讓你看到「不做任何事」的後果，然後一步步加上配套、觀察每一步改善多少。
    </span>
</div>
""", unsafe_allow_html=True)
        st.markdown("""
<div style="background:#fff;border:1px solid #e8e0d4;border-radius:10px;padding:14px 20px;margin:8px 0;">
    <span style="color:#8b7355;font-size:0.9em;">
    <b>跑完模擬後你會拿到什麼？</b><br>
    1. 年化報酬率的分布範圍（不是一個數字，是一整條鐘型曲線）<br>
    2. 「最壞情況下撐不撐得住」的壓力測試結果<br>
    3. 12 項自動健康檢查，幫你抓出隱藏的結構性問題<br>
    4. AI 顧問會標出「矛盾點」——例如報酬率為負但崩潰率很低，代表不會倒但一直在虧
    </span>
</div>
""", unsafe_allow_html=True)

    with tab_logic:
        st.markdown("### 計算原理")
        st.markdown("模擬器把未來 **25 年切成 100 個季度**，每一季依序計算 **5 件事**，然後再用蒙地卡羅方法重複跑 1,000 遍。")

        st.markdown("---")
        st.markdown("#### 計算一：這一季有多少新住戶來？")
        st.markdown("每季的新入住人數由 **11 個因子相乘** 再加上 H 會館導入：")
        st.markdown("""
<div style="background:#f9f6f0;border:1px solid #e8e0d4;border-radius:8px;padding:16px;margin:8px 0;">
<table style="width:100%;border-collapse:collapse;font-size:0.9em;">
<tr style="border-bottom:2px solid #b08d57;"><th style="text-align:left;padding:6px;">因子</th><th style="text-align:left;padding:6px;">計算方式</th><th style="text-align:left;padding:6px;">預設值</th></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>基礎需求</b></td><td style="padding:6px;">目標客群 × 年轉化率 / 4</td><td style="padding:6px;">35,000 × 0.5% = <b>~44 戶/季</b></td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>品牌信任</b></td><td style="padding:6px;">信任分 / 50（封頂 3.0，下限 0.1）</td><td style="padding:6px;">初始 30 分 → 0.6x</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>保險通路</b></td><td style="padding:6px;">第 2 年後啟動</td><td style="padding:6px;">關=1.0x；開=最高 2.0x</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>冷啟動</b></td><td style="padding:6px;">(在住/800)^0.5，下限 0.2</td><td style="padding:6px;">100 戶=0.35x；800 戶=1.0x</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>距離摩擦</b></td><td style="padding:6px;">0.85 + 行銷預算/10億×0.02</td><td style="padding:6px;">預設 0.85（蘇澳偏遠劣勢）</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>醫療加成</b></td><td style="padding:6px;">依等級</td><td style="padding:6px;">基本=1.0x；區域=1.15x；中心=1.3x</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>溫泉加成</b></td><td style="padding:6px;">依等級</td><td style="padding:6px;">無=1.0x；高規格=1.2x</td></tr>
<tr><td style="padding:6px;"><b>市場剩餘</b></td><td style="padding:6px;">剩餘客群/(初始×30%)</td><td style="padding:6px;">低於 30% 開始減速</td></tr>
</table></div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 計算二：這一季有多少住戶離開？")
        st.markdown("""
<div style="background:#f9f6f0;border:1px solid #e8e0d4;border-radius:8px;padding:16px;margin:8px 0;">
<table style="width:100%;border-collapse:collapse;font-size:0.9em;">
<tr style="border-bottom:2px solid #b08d57;"><th style="text-align:left;padding:6px;">退出原因</th><th style="text-align:center;padding:6px;">65歲</th><th style="text-align:center;padding:6px;">75歲</th><th style="text-align:center;padding:6px;">85歲</th><th style="text-align:center;padding:6px;">90歲</th></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;">自然死亡（年化）</td><td style="text-align:center;">1.2%</td><td style="text-align:center;">3.5%</td><td style="text-align:center;">10%</td><td style="text-align:center;">16%</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;">轉介護棟（年化）</td><td style="text-align:center;">—</td><td style="text-align:center;">2%</td><td style="text-align:center;">10%</td><td style="text-align:center;">15%</td></tr>
<tr><td style="padding:6px;">自願搬走（固定）</td><td colspan="4" style="text-align:center;">全年齡 3%/年</td></tr>
</table></div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 計算三：錢怎麼進出？")
        st.markdown("""
<div style="background:#f9f6f0;border:1px solid #e8e0d4;border-radius:8px;padding:16px;margin:8px 0;">
<b style="color:#2e7d32;">收入</b>：月費（在住×月費×3）+ 新住戶押金 + 多元營收 + 醫療/溫泉外收<br>
<b style="color:#c62828;">支出</b>：人事（在住×人力比×薪資×蘇澳+15%）+ 溫泉維護 + 醫療成本 + 行銷 + 資金利息 + 退費 + 營運分潤
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 計算四：品牌信任怎麼變？")
        st.markdown("品牌信任 0-100 分，每季加減分：入住率>85% +2 / 信託等級×1.5 / 基礎衰減 -0.5 / 2%機率負面事件 -10~30 / 退費擠壓打95折")

        st.markdown("---")
        st.markdown("#### 計算五：下一期能否啟動？")
        st.markdown("三條件同時滿足：**入住率 ≥ 80%** + **現金儲備 ≥ 250 天** + **建設金 ≥ 造價 30%**。啟動後施工 2 年。")

        st.markdown("---")
        st.markdown("#### IRR（年化報酬率）怎麼算？")
        st.markdown("把 100 季淨現金流 + 最後一季殘值，用**二分法**找到讓淨現值=0 的折現率。殘值 = 在住人數 × 押金 × 1.03^25。")
        st.markdown("""
<div style="background:#f9f6f0;border-radius:8px;padding:12px 16px;margin:8px 0;border-left:4px solid #b08d57;">
<b>殘值假設：</b>預設每年增值 3%。25 年後殘值 ≈ 在住人數 × 5,234 萬。這個假設對 IRR 影響很大——進階設定可調。
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 崩潰率：依信託等級分兩套邏輯")
        st.markdown("""
<div style="background:#f9f6f0;border:1px solid #e8e0d4;border-radius:8px;padding:16px;margin:8px 0;">
<table style="width:100%;border-collapse:collapse;font-size:0.9em;">
<tr style="border-bottom:2px solid #b08d57;"><th style="padding:6px;"></th><th style="padding:6px;">無信託</th><th style="padding:6px;">獨立信託（2+）</th></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>可動用資金</b></td><td style="padding:6px;">營運現金+準備金+押金池</td><td style="padding:6px;">營運現金+準備金（押金隔離）</td></tr>
<tr><td style="padding:6px;"><b>崩潰條件</b></td><td colspan="2" style="padding:6px;">可動用<0 即時崩潰；淨流動性<0 連續4季 = 流動性危機</td></tr>
</table></div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 蒙地卡羅：三級擾動 + 6 組壓力測試")
        st.markdown("每遍對 8 個參數加隨機擾動（**α穩定** ±15%：月費/人力/退費、**β中度** ±30%：轉化率/預算、**γ高度** ±50%：保險/H會館/資金成本）。約 7% 機率觸發宏觀衝擊連動。")
        st.markdown("另跑 6 組壓力測試：溫和衰退、嚴重衰退、信任危機、成本通膨、複合災難、無新血存活。存活率 >80% 為通過。")

    with tab_charts:
        st.markdown("### 圖表怎麼看")
        st.markdown("""
| 圖表 | 怎麼看 | 好的信號 | 壞的信號 |
|------|--------|---------|---------|
| **判斷框** | 一句話結論 | 良好（綠色） | 危險（紅色） |
| **三個大數字** | 報酬率/危機率/回本 | IRR>5%, 崩潰<10% | IRR<0, 崩潰>20% |
| **走勢圖** | 深色線=中位數，淺色帶=90%範圍 | 線穿過零線往上 | 帶子全在零以下 |
| **收支分解** | 綠柱=收入，紅柱=支出 | 月費>營運成本 | 退費≈押金收入 |
| **入住率** | 實線=整體，虛線=各期 | 穩定在 85% 以上 | 某期遲遲上不來 |
| **壓力測試** | 6 種壞事的存活率 | 6 組全>80% | 複合災難<50% |
| **健康檢查** | 12 項自動驗證 | 全 Pass | C02崩潰或C04未全啟動 |
""")
        st.markdown("""
<div style="background:#f9f6f0;border-radius:8px;padding:12px 16px;margin:8px 0;border-left:4px solid #b08d57;">
<b>走勢圖的帶子越寬 = 不確定性越大。</b>如果 P5（最壞 5%）掉到 -500 億，代表最壞情況下虧很多。看「帶子下緣有沒有掉到底」比看中位數更重要。
</div>
""", unsafe_allow_html=True)

    with tab_choose:
        st.markdown("### 策略怎麼選")
        st.markdown("#### 建議操作順序")
        st.markdown("""
<div style="background:#f9f6f0;border:1px solid #e8e0d4;border-radius:8px;padding:16px;margin:8px 0;">
<table style="width:100%;border-collapse:collapse;font-size:0.9em;">
<tr style="border-bottom:2px solid #b08d57;"><th style="padding:6px;">步驟</th><th style="padding:6px;">操作</th><th style="padding:6px;">預期效果</th><th style="padding:6px;">原理</th></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;">0</td><td style="padding:6px;">先看預設結果</td><td style="padding:6px;">了解裸配置</td><td style="padding:6px;">基準線</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>1</b></td><td style="padding:6px;">保險綁定</td><td style="padding:6px;">需求 1.0x→2.0x</td><td style="padding:6px;">最大單一推手</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>2</b></td><td style="padding:6px;">獨立信託</td><td style="padding:6px;">信任+3/季</td><td style="padding:6px;">品牌穩定+防擠兌</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>3</b></td><td style="padding:6px;">區域醫院合作</td><td style="padding:6px;">需求+15%</td><td style="padding:6px;">抵消距離劣勢</td></tr>
<tr style="border-bottom:1px solid #e8e0d4;"><td style="padding:6px;"><b>4</b></td><td style="padding:6px;">高規格溫泉</td><td style="padding:6px;">需求+20%+外收</td><td style="padding:6px;">蘇澳獨特優勢</td></tr>
<tr><td style="padding:6px;"><b>5</b></td><td style="padding:6px;">跑蒙地卡羅</td><td style="padding:6px;">看完整分布</td><td style="padding:6px;">確認尾部風險可控</td></tr>
</table></div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 飛輪效應：為什麼配套要一起開？")
        st.markdown("""
<div style="background:linear-gradient(135deg,#f9f6f0,#f0ebe4);border-radius:10px;
    padding:16px 20px;margin:8px 0;border-left:4px solid #b08d57;">
    <span style="color:#8b7355;">
    <b>正循環飛輪：</b>信託→信任高→更多人來→入住率破85%→口碑→信任更高→啟動下期→規模效應…<br><br>
    預設（什麼都沒開）每季只有 ~22 戶（44基礎×0.6信任×0.85距離）。<br>
    全開配套後可達 100+ 戶/季，<b>差距超過 4 倍</b>。效果不是相加而是相乘。
    </span>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 常見問題快速診斷")
        st.markdown("""
| 症狀 | 原因 | 建議 |
|------|------|------|
| IRR 為負，崩潰率卻很低 | 規模太小燒不完，但也賺不了 | 加保險/醫療推需求 |
| 入住率一直上不去 | 需求引擎不足＋冷啟動 | 先開保險（最大推手）|
| 後面幾期不啟動 | 入住率卡 80% 以下 | 先讓第一期破 85% |
| 開信託崩潰率反升 | 押金隔離後營運現金不夠 | 同時推需求讓月費覆蓋營運 |
| 壓力測試全掛 | 安全邊際太薄 | 提高現金儲備或縮小首期 |
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
    st.markdown('<p style="text-align:center;color:#86868b;font-size:13px;margin:4px 0 0;">已有模擬結果。調整參數後再次點擊可更新。</p>', unsafe_allow_html=True)

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
    from ui.tip_carousel import get_shuffled_tips, render_tip_to_container

    tips = get_shuffled_tips()
    tip_box = st.empty()
    progress_bar = st.progress(0, text=f"正在模擬 {mc_runs:,} 種不同情境...")
    _tip_state = [0, time.time()]  # [current_index, last_switch_time]
    # 混合模式：進度驅動 + 8 秒最低間隔
    _tips_to_show = min(len(tips), max(3, mc_runs // 200))
    _switch_every = max(1, mc_runs // _tips_to_show)
    TIP_MIN_INTERVAL = 8  # 每條至少顯示 8 秒

    def _show_tip(idx):
        tid, title, body = tips[idx % len(tips)]
        tip_box.empty()
        render_tip_to_container(tip_box, tid, title, body, idx % len(tips), len(tips), "模擬進行中")

    def _on_progress(done, total):
        pct = int(done / total * 70)
        progress_bar.progress(pct, text=f"已完成 {done:,} / {total:,} 次模擬...")
        # 進度驅動但加 8 秒最低間隔
        new_idx = done // _switch_every
        now = time.time()
        if new_idx != _tip_state[0] and (now - _tip_state[1]) >= TIP_MIN_INTERVAL:
            _tip_state[0] = new_idx
            _tip_state[1] = now
            _show_tip(new_idx)

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
tab_ai, tab_method = st.tabs(["AI 分析報告", "方法論"])

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
