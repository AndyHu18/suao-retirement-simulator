"""
Claude API integration for AI-powered analysis.
Triggered by button, runs comparison scenarios, streams analysis.
"""

import os
from pathlib import Path
import streamlit as st

# Load .env file if present
_env_path = Path(__file__).resolve().parent.parent / '.env'
if _env_path.exists():
    for _line in _env_path.read_text().strip().splitlines():
        _line = _line.strip()
        if '=' in _line and not _line.startswith('#'):
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip())

DOMAIN_KNOWLEDGE_PROMPT = """你是一位同時具備不動產開發、精算、養老產業經驗的資深顧問。

你的分析必須基於以下全球養老產業的驗證知識：

【成功標竿】
- 泰康之家：27社區、30萬保戶、「幸福有約」保險綁定、燕園一期99.7%入住率、毛利率12.3%、陳東升明說30年回收
- Kendal：A+評級、DCOH 759-1039天、全固定利率、禁止交叉擔保、等候719人、Enso Village 8.5週70%預售
- Acts：28社區、入住率95.6%、75%預售才動工
- 萬科隨園：595戶嵌入良渚文化村、接入醫保後每床收入+40%、三權分立
- The Villages：15萬+住戶、年營收20億+、CDD債券結構、40年有機增長
- 三井Park Wellstate：340自立+60介護(85:15)、入居金5628萬-5.4億日圓、開業前4000件諮詢

【失敗教訓】
- Erickson：同時開10個園區+債務融資→2009破產、入住費挪用蓋新社區
- Friendship Village：42年成功→COVID觸發擠兌→退費條件是「新住戶入住」→擠兌壓力自我加強→住戶回收率10%
- 綠城烏鎮：2000+戶全售罄但入住率<10%、35000㎡老年大學服務60人
- 中國愛晚系：132億龐氏、11萬受害者、壓制整個行業信任
- 日本未来設計：36億押金中26億挪用、首期還款率0.6%
- 北京太陽城：賣完房後醫院銀行超市全關
- 曜陽國際：距北京90公里、頂級背書、僅賣25套

【關鍵閾值】
- 入住率：>90%健康、85%警戒、80%嚴重、75%存亡線、70%高關閉風險
- DCOH：250天最低、400-500天BBB、750+天A+
- CCRC歷史違約率：11.2%（787家中88家）
- 75%違約發生在社區成熟前
- 入住費攤銷可佔年營運預算40%+
- 人力成本佔營運60-70%
- 溫泉維護成本1.8x
- 破產時入住費為無擔保債權（清償最底層）
- 品牌老化15-25年拐點、日經高爾夫指數跌94%
- 文化轉變耗時20-25年

【蘇澳特有條件】
- 距台北70-90分鐘（雪隧）、面對大台北35000高淨值客群
- 碳酸冷泉全球僅兩處（另一處意大利）
- 宜蘭為台北「後花園」、心理距離短於物理距離
- 醫療：區域醫院15-30分鐘、醫學中心70-90分鐘
- 勞動力：蘇澳4萬人口、全營運需約3000員工

你的分析風格：
- 直接給判斷，不說「需要進一步分析」
- 用具體案例佐證，不用泛泛的「業界認為」
- 數字必須跟全球標竿做比較才有意義
- 組合效應 > 個別因素。永遠分析因素之間的交互增強和抵銷
- 行動建議必須是配套方案，不是排名清單
- 語言用繁體中文"""


def _format_selections(params):
    """Format user parameter selections for the prompt."""
    lines = []
    lines.append(f"- 總預算: {params['total_budget']/1e8:.0f}億 TWD")
    lines.append(f"- 資金成本: {params['annual_cost_of_capital']:.1%}")
    lines.append(f"- 押金: {params['deposit_amount']/1e4:.0f}萬 TWD")
    lines.append(f"- 月費: {params['monthly_fee']/1e4:.0f}萬 TWD")
    lines.append(f"- 退費比例: {params['refund_percentage']:.0%}")
    lines.append(f"- 押金保護: Level {params['trust_mechanism_level']}")
    lines.append(f"- 保險因子: {params['insurance_factor']}")
    lines.append(f"- 醫療整合: Level {params['medical_integration']}")
    lines.append(f"- 溫泉規格: Level {params.get('onsen_level', 0)}")
    lines.append(f"- 體驗深度: {params['experience_level']}")
    lines.append(f"- 首期規模: {params['phase_units'][0]}戶")
    lines.append(f"- 去標籤化: Level {params['debranding_level']}")
    lines.append(f"- 多元收入: {', '.join(params.get('revenue_streams', [])) or '無'}")
    return '\n'.join(lines)


def _format_results(metrics):
    """Format MC results for the prompt."""
    lines = []
    lines.append(f"- IRR 中位數: {metrics['irr_median']:.2%}")
    lines.append(f"- IRR P25-P75: {metrics['irr_p25']:.2%} ~ {metrics['irr_p75']:.2%}")
    lines.append(f"- 崩潰機率: {metrics['collapse_prob']:.1%}")
    pb = metrics['payback_median']
    lines.append(f"- 回本時間中位數: {pb:.1f}年" if pb > 0 else "- 回本時間: 25年內未回本")
    lines.append(f"- 最大資金需求: {metrics['max_funding_need']/1e9:.1f}B TWD")
    lines.append(f"- 25年末累計現金流中位數: {metrics['final_cf_median']/1e9:.1f}B TWD")
    return '\n'.join(lines)


def _format_comparison(comparison):
    """Format comparison scenario results."""
    lines = []
    for name, m in comparison.items():
        lines.append(f"\n**{name}**")
        lines.append(f"  IRR: {m['irr_median']:.2%} | 崩潰: {m['collapse_prob']:.1%} | "
                      f"回本: {m['payback_median']:.1f}年")
    return '\n'.join(lines)


def _format_rules(rules_status):
    """Format triggered rules."""
    from utils.formatting import RULE_NAMES
    lines = []
    final = rules_status[-1]
    for i, name in enumerate(RULE_NAMES):
        status = final[i]
        if status == 2:
            lines.append(f"- 🔴 {name} — 已觸發")
        elif status == 1:
            lines.append(f"- 🟡 {name} — 接近觸發")
    return '\n'.join(lines) if lines else "- 無規則觸發"


def render_ai_analysis(params, current_metrics, mc_result):
    """Render AI analysis section with button trigger."""

    st.markdown("---")
    st.subheader("🤖 AI 深度分析報告")

    col1, col2 = st.columns([1, 4])
    with col1:
        run_analysis = st.button("生成 AI 分析報告", type="primary",
                                  width='stretch')

    if not run_analysis:
        st.info("點擊按鈕生成 AI 分析報告（會自動跑 4 組對比模擬）")
        return

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        st.error("未設定 ANTHROPIC_API_KEY 環境變數，無法使用 AI 分析")
        return

    # Run comparison scenarios
    with st.spinner("正在跑 4 組對比模擬..."):
        from engine.monte_carlo import run_comparison_scenarios
        comparison = run_comparison_scenarios(params, n_runs=500)

    # Get triggered rules from median run
    import numpy as np
    median_idx = np.argsort(mc_result['cf_curves'][:, -1])[len(mc_result['cf_curves']) // 2]
    median_run = mc_result['results'][median_idx]

    # Build prompt
    user_prompt = f"""## 使用者的策略選擇
{_format_selections(params)}

## 當前配置的模擬結果
{_format_results(current_metrics)}

## 對比配置的模擬結果
{_format_comparison(comparison)}

## 被觸發的交互規則
{_format_rules(median_run.rules_status)}

請提供以下分析：

### 一、系統診斷（300字）
目前策略配置形成了什麼系統狀態？
- 哪些正面飛輪已具備啟動條件？缺什麼就能啟動？
- 哪些負面迴路已觸發或接近觸發？
- 有沒有「同時踩油門和埋地雷」的矛盾配置？

### 二、數字解讀（每個指標200字）
把每個數字翻譯成商業語言，跟全球標竿比較。
- IRR在行業什麼水平？跟泰康(醫養毛利12.3%)、Kendal(A+評級)、Acts(95.6%入住率)比？
- 崩潰機率意味什麼？哪些歷史案例跟這個水平類似？
- 回本時間合不合理？泰康說30年回收，Kendal的DCOH 759-1039天是什麼概念？
- 市場容量會在第幾年出現壓力？

### 三、組合效應分析（500字，最核心）
基於對比配置的結果：
- 核心配套（信託+保險+醫療）的組合效果 vs 各自單獨效果
- 哪些因素有超線性組合增強？（A+B > A的效果+B的效果）
- 哪些有抵銷效應？
- 目前配置最大的「缺失配套」是什麼？

### 四、行動路徑（配套方案，不是排名清單）

**第一層：必須同步推進的核心配套**
哪幾件事互相依賴？為什麼需要同步？
全部到位的組合效果是什麼？（引用對比模擬的具體數字）
各自時間線和並行啟動計畫。

**第二層：核心配套就緒後的增強動作**
在核心基礎上有增量價值的動作，優先序和預期效果。

**第三層：條件性選擇題**
取決於風險偏好的決策，每個選項的trade-off。
不替決策者選，給判斷框架。

每一層都必須引用模型的具體數字來支撐建議。"""

    # Stream the response
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        with st.container():
            response_placeholder = st.empty()
            full_response = ""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=5000,
                system=DOMAIN_KNOWLEDGE_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    response_placeholder.markdown(full_response)

    except ImportError:
        st.error("請安裝 anthropic 套件: `pip install anthropic`")
    except Exception as e:
        st.error(f"AI 分析失敗: {str(e)}")
