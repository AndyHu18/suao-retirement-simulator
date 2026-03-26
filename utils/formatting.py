"""Number formatting and Chinese labels for the dashboard."""


def fmt_billion(val):
    """Format value in billions TWD."""
    if abs(val) >= 1e9:
        return f"{val / 1e9:.1f}B"
    if abs(val) >= 1e8:
        return f"{val / 1e8:.0f}億"
    if abs(val) >= 1e4:
        return f"{val / 1e4:.0f}萬"
    return f"{val:,.0f}"


def fmt_pct(val):
    """Format as percentage."""
    return f"{val:.1%}"


def fmt_years(quarters):
    """Convert quarters to years string."""
    if quarters < 0:
        return "未回本"
    y = quarters / 4
    return f"{y:.1f}年"


def quarter_to_year_label(q):
    """Convert quarter index to year label."""
    return f"第{q // 4 + 1}年Q{q % 4 + 1}"


RULE_NAMES = [
    "R01 押金擠兌螺旋",
    "R02 增長飛輪 ✦",
    "R03 品牌老化炸彈",
    "R04 信任資本飛輪 ✦",
    "R05 空城陷阱",
    "R06 規模×缺陷放大",
    "R07 醫療×品牌張力",
    "R08 蘇澳距離摩擦",
    "R09 營運能力缺口",
    "R10 保險飛輪缺失",
]

RULE_SEVERITY = [10, 9, 8, 8, 7, 9, 6, 5, 7, 8]
