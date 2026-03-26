"""Inline SVG icons for the dashboard. Replace all emoji usage."""


def _svg(path_d, size=18, color="#374151", vbox="0 0 24 24"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{vbox}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'style="display:inline-block;vertical-align:middle;margin-right:6px;">'
            f'{path_d}</svg>')


# --- Section headers ---
HOUSE = _svg('<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
             '<polyline points="9 22 9 12 15 12 15 22"/>', size=22, color="#2563EB")

MONEY = _svg('<line x1="12" y1="1" x2="12" y2="23"/>'
             '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
             size=20, color="#059669")

ROCKET = _svg('<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>'
              '<path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
              '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>'
              '<path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
              size=20, color="#7C3AED")

HOSPITAL = _svg('<path d="M3 3h18v18H3z"/><path d="M12 8v8"/><path d="M8 12h8"/>',
                size=20, color="#DC2626")

CALENDAR = _svg('<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
                '<line x1="16" y1="2" x2="16" y2="6"/>'
                '<line x1="8" y1="2" x2="8" y2="6"/>'
                '<line x1="3" y1="10" x2="21" y2="10"/>',
                size=20, color="#2563EB")

GLOBE = _svg('<circle cx="12" cy="12" r="10"/>'
             '<line x1="2" y1="12" x2="22" y2="12"/>'
             '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
             size=20, color="#6B7280")

# --- Dashboard icons ---
CHART = _svg('<line x1="18" y1="20" x2="18" y2="10"/>'
             '<line x1="12" y1="20" x2="12" y2="4"/>'
             '<line x1="6" y1="20" x2="6" y2="14"/>',
             size=18, color="#2563EB")

FIRE = _svg('<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 '
            '.5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
            size=18, color="#EF4444")

TRENDING = _svg('<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
                '<polyline points="17 6 23 6 23 12"/>',
                size=18, color="#059669")

DOLLAR = _svg('<line x1="12" y1="1" x2="12" y2="23"/>'
              '<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
              size=18, color="#D97706")

ACTIVITY = _svg('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
                size=18, color="#7C3AED")

CHECK_CIRCLE = _svg('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
                    '<polyline points="22 4 12 14.01 9 11.01"/>',
                    size=18, color="#059669")

TARGET = _svg('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/>'
              '<circle cx="12" cy="12" r="2"/>',
              size=18, color="#DC2626")

DICE = _svg('<rect x="2" y="2" width="20" height="20" rx="3"/>'
            '<circle cx="8" cy="8" r="1.5" fill="#374151" stroke="none"/>'
            '<circle cx="16" cy="8" r="1.5" fill="#374151" stroke="none"/>'
            '<circle cx="8" cy="16" r="1.5" fill="#374151" stroke="none"/>'
            '<circle cx="16" cy="16" r="1.5" fill="#374151" stroke="none"/>'
            '<circle cx="12" cy="12" r="1.5" fill="#374151" stroke="none"/>',
            size=20, color="#374151")

AI_BRAIN = _svg('<path d="M12 2a8 8 0 0 0-8 8c0 3.4 2.1 6.3 5 7.5V20h6v-2.5c2.9-1.2 5-4.1 5-7.5a8 8 0 0 0-8-8z"/>'
                '<line x1="10" y1="20" x2="10" y2="22"/>'
                '<line x1="14" y1="20" x2="14" y2="22"/>',
                size=20, color="#7C3AED")

BOOK = _svg('<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
            '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
            size=18, color="#6B7280")


# --- Status dots (for use in HTML, not emoji) ---
def dot(color):
    """Colored status dot as inline HTML."""
    return f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:4px;"></span>'

DOT_GREEN = dot("#22C55E")
DOT_YELLOW = dot("#F59E0B")
DOT_RED = dot("#EF4444")
DOT_BLUE = dot("#3B82F6")
DOT_GRAY = dot("#9CA3AF")


def header(icon_svg, text, level=3):
    """Return an HTML header with inline SVG icon."""
    tag = f"h{level}"
    return f'<{tag} style="display:flex;align-items:center;gap:8px;margin:16px 0 8px;">{icon_svg}{text}</{tag}>'
