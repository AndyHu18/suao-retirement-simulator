"""
Shared tip carousel component for loading screens.
Used during MC simulation and AI analysis waiting periods.
Shows tips with illustrations, rotating at reading speed.
"""

import os
import base64
import random
import streamlit as st

# Tip content: (id, title, body)
TIPS = [
    ("flywheel",
     "這個模擬器最重要的發現",
     "單獨開一個配套效果有限，但**保險＋信託＋醫療**同時開會產生「飛輪效應」——"
     "信任高 → 人多 → 入住率高 → 口碑好 → 信任更高。試著同時開啟三個看看。"),
    ("default_loss",
     "為什麼預設配置是虧損的？",
     "預設故意什麼都沒開，讓你看到「不做任何事」的後果。"
     "這不是 bug，是設計——方便你一步步加上配套，看每個改善多少。"),
    ("chart_reading",
     "怎麼看懂走勢圖",
     "藍色粗線是「最可能的走勢」，淺藍區域是「運氣好壞的範圍」。"
     "線在零線上方 = 賺錢，下方 = 賠錢。箭頭標示回本的年份。"),
    ("insurance",
     "保險綁定是最大槓桿",
     "跟壽險公司合作，讓保戶優先入住。在左邊「需求引擎」區勾選「保險綁定通路」，"
     "通常能讓報酬率改善 10 個百分點以上。"),
    ("stress_test",
     "壓力測試在測什麼？",
     "模擬器會故意模擬 6 種壞事：經濟崩盤、退費潮、信任危機、成本暴漲、複合災難、完全沒新人。"
     "看你的策略能不能撐過這些考驗。"),
    ("cold_spring",
     "蘇澳冷泉是全球稀缺資源",
     "全球只有兩處碳酸冷泉（義大利+蘇澳）。開啟溫泉選項不只增加收入，"
     "還能提升品牌差異化 20%，是蘇澳專案最獨特的優勢。"),
    ("brand_aging",
     "什麼是「品牌老化」？",
     "社區住戶會老。如果沒有新年輕住戶加入，社區平均年齡越來越高，"
     "對新客群的吸引力會下降。「品牌老化對抗」就是解決這個問題的策略。"),
    ("advanced_mode",
     "進階模式能做什麼？",
     "打開左上的「進階模式」，可以微調每一個底層參數、自訂每期蓋幾戶、"
     "查看每個參數的可信度標記（紅色 = 建議用真實數據替換）。"),
    ("ai_advisor",
     "AI 顧問分析怎麼用？",
     "模擬跑完後，底部會出現「啟動深度顧問分析」按鈕。"
     "AI 會生成完整的七部分報告，包含因果分析、行動方案、風險地圖，還能追問。"),
    ("industry_numbers",
     "全球養老地產的關鍵數字",
     "入住率 85% 以上才算健康，75% 以下就有存亡風險。"
     "現金儲備至少 250 天。人事成本佔營運的 60-70%。品牌老化週期約 15-25 年。"),
    ("waterfall",
     "收支分解圖（瀑布圖）怎麼看",
     "綠色柱子是收入來源（押金、月費、其他），紅色是支出（建設、營運、退費、利息）。"
     "最右邊藍色柱是淨結果。看哪根最大，就知道問題在哪。"),
    ("h_hotel",
     "H 會館的導客效果",
     "如果有 H 會館，每年 6,000 位高淨值客人中，約 3% 會主動諮詢、12% 會成交。"
     "這等於每年多 20+ 戶的穩定來源，不靠廣告。"),
]

# Image cache
_IMG_CACHE = {}


def _get_tip_image_b64(tip_id):
    """Load tip image as base64 data URI, with caching."""
    if tip_id in _IMG_CACHE:
        return _IMG_CACHE[tip_id]

    img_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tips', f'tip_{tip_id}.png')
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        uri = f"data:image/png;base64,{b64}"
        _IMG_CACHE[tip_id] = uri
        return uri
    return None


def render_tip_card(tip_id, title, body, index, total, context="模擬進行中"):
    """Render a single tip card with optional image."""
    img_uri = _get_tip_image_b64(tip_id)

    if img_uri:
        img_html = f"""
        <div style="flex:0 0 120px;margin-right:20px;">
            <img src="{img_uri}" style="width:120px;height:120px;border-radius:10px;object-fit:cover;" />
        </div>"""
        layout = "display:flex;align-items:center;"
    else:
        img_html = ""
        layout = ""

    # Bold markdown
    import re
    body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#b08d57;">\1</strong>', body)

    return f"""
    <div style="background:white;border:1.5px solid #e0ddd7;border-radius:14px;
        padding:24px 28px;margin:16px 0;max-width:750px;
        box-shadow:0 2px 12px rgba(176,141,87,0.08);
        transition:all 0.3s ease;">
        <div style="color:#b08d57;font-weight:600;font-size:0.8em;
            letter-spacing:0.08em;margin-bottom:12px;text-transform:uppercase;">
            {context} · 小知識 {index + 1}/{total}</div>
        <div style="{layout}">
            {img_html}
            <div>
                <div style="color:#1a1a1a;font-size:1.1em;font-weight:700;margin-bottom:8px;
                    line-height:1.4;">{title}</div>
                <div style="color:#4a4a4a;font-size:0.95em;line-height:1.8;">{body_html}</div>
            </div>
        </div>
    </div>
    """


def get_shuffled_tips():
    """Return a shuffled copy of tips."""
    tips = list(TIPS)
    random.shuffle(tips)
    return tips
