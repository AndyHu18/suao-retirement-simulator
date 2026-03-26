"""
Generate all images using Gemini gemini-3-pro-image-preview (Nano Banana Pro).
Includes: 1 hero banner + 12 tip illustrations.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("請在 .env 檔案中設定 GEMINI_API_KEY=你的key")
client = genai.Client(api_key=api_key)
MODEL = "gemini-3-pro-image-preview"  # Nano Banana Pro — 唯一允許的生圖模型

# Premium style directive shared by all prompts
STYLE = (
    "Ultra-premium minimalist illustration. "
    "Color palette: warm ivory (#F9F6F0) background, deep gold (#B08D57) accents, "
    "charcoal (#2C2C2C) details, sage green (#4A7C59) highlights. "
    "Style: elegant vector art with subtle gradients and soft shadows, "
    "inspired by luxury real estate brochures and Apple keynote slides. "
    "No text, no watermarks. Clean composition with plenty of negative space. "
    "Professional, sophisticated, trustworthy. "
    "All text must be perfectly clear, accurate, and free of any garbled characters."
)

HERO = (
    "hero",
    "assets/hero_banner.png",
    "Wide panoramic illustration (16:9 aspect ratio) of a premium retirement community "
    "nestled in lush green mountains with a serene turquoise natural cold spring pool in the foreground. "
    "Modern elegant low-rise buildings with traditional Asian architectural accents blend into the landscape. "
    "Golden morning light filtering through the mountains. A few senior residents walking on garden paths. "
    "The scene conveys luxury, serenity, nature, and wellbeing. " + STYLE
)

TIPS = [
    ("tip_flywheel",
     "assets/tips/tip_flywheel.png",
     "Elegant circular diagram showing a golden flywheel mechanism with 5 nodes connected by flowing arrows: "
     "Insurance shield icon -> Trust badge icon -> People silhouettes -> Building with high occupancy -> "
     "Reputation star icon -> back to Insurance. Each node is a refined gold icon on ivory. " + STYLE),

    ("tip_default_loss",
     "assets/tips/tip_default_loss.png",
     "Split-screen illustration: left side shows a muted, faded dashboard with a declining red line chart. "
     "Right side shows the same dashboard glowing with warm gold light, line chart rising upward, "
     "with a hand adjusting golden slider controls. Transformation concept. " + STYLE),

    ("tip_chart_reading",
     "assets/tips/tip_chart_reading.png",
     "Elegant financial chart illustration: a bold dark line with a soft blue-gold gradient confidence band. "
     "Horizontal zero line divides the chart — above is tinted warm sage green, below is tinted soft rose. "
     "An arrow points to where the line crosses zero (breakeven). " + STYLE),

    ("tip_insurance",
     "assets/tips/tip_insurance.png",
     "A refined golden shield icon merging with an umbrella symbol and a house silhouette. "
     "The shield has a subtle warm glow. Represents insurance-linked retirement protection. "
     "Floating golden particles suggest value creation. " + STYLE),

    ("tip_stress_test",
     "assets/tips/tip_stress_test.png",
     "Six elegant icon tiles arranged in a 2x3 grid, each representing a stress scenario: "
     "economic downturn (declining bar chart), exit wave (outward arrows), trust crisis (cracked shield), "
     "cost spike (upward arrow on coins), compound disaster (overlapping storm symbols), "
     "zero demand (empty building). Muted warm tones on ivory background. " + STYLE),

    ("tip_cold_spring",
     "assets/tips/tip_cold_spring.png",
     "Premium illustration of Suao cold spring: crystal clear turquoise water in a natural stone pool, "
     "surrounded by verdant mountains. Small elegant wooden pavilion with warm golden light. "
     "Bubbles rising from the spring surface. Serene, luxurious spa atmosphere. " + STYLE),

    ("tip_brand_aging",
     "assets/tips/tip_brand_aging.png",
     "Elegant before/after concept: left portion shows a community with muted sepia tones and aging symbols. "
     "Right portion shows the same community vibrant with mixed-generation residents, warm golden light, "
     "green plants, and activity. A flowing golden arrow connects left to right showing transformation. " + STYLE),

    ("tip_advanced_mode",
     "assets/tips/tip_advanced_mode.png",
     "Refined control panel illustration with multiple precision sliders, dials, and toggle switches, "
     "all in gold and ivory color scheme. One slider is highlighted with a warm glow and a magnifying glass "
     "hovering over it, suggesting fine-tuning capability. Dashboard aesthetic. " + STYLE),

    ("tip_ai_advisor",
     "assets/tips/tip_ai_advisor.png",
     "Elegant AI analysis concept: a sleek brain-circuit icon in gold next to a multi-section document "
     "with miniature charts, bullet points, and highlighted insights. A speech bubble with a lightbulb "
     "symbol emerges from the brain. Professional advisory aesthetic. " + STYLE),

    ("tip_industry_numbers",
     "assets/tips/tip_industry_numbers.png",
     "Three elegant metric cards floating on ivory background: "
     "first card shows '85%' with a gauge icon (occupancy), "
     "second shows '250' with a calendar icon (cash reserve days), "
     "third shows '60-70%' with a people icon (staffing ratio). "
     "Gold accent borders, refined typography feel. " + STYLE),

    ("tip_waterfall",
     "assets/tips/tip_waterfall.png",
     "Premium waterfall chart illustration: elegant green bars rising (income sources) and "
     "muted rose bars descending (cost items), with a final gold bar showing net result. "
     "Clean gridlines, sophisticated financial report aesthetic. " + STYLE),

    ("tip_h_hotel",
     "assets/tips/tip_h_hotel.png",
     "Elegant illustration of a boutique luxury hotel with warm golden lighting, connected by "
     "a flowing dotted golden path to a retirement community campus. Small sophisticated figures "
     "walking from hotel toward community. Premium hospitality-to-residential pipeline concept. " + STYLE),
]


def generate_image(name, filepath, prompt):
    """Generate a single image using Nano Banana Pro."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(part.inline_data.data)
            size_kb = len(part.inline_data.data) // 1024
            print(f"  Saved: {filepath} ({size_kb}KB)")
            return True

    print(f"  FAILED: {name} - no image in response")
    return False


def compress_image(filepath, max_size=240):
    """Compress to max_size x max_size for tips, keep hero larger."""
    from PIL import Image
    img = Image.open(filepath)
    if "hero" in filepath:
        # Hero: resize to 800px wide, keep aspect ratio
        w, h = img.size
        new_w = 800
        new_h = int(h * new_w / w)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    else:
        img = img.resize((max_size, max_size), Image.LANCZOS)
    img.save(filepath, 'PNG', optimize=True)
    new_size = os.path.getsize(filepath)
    print(f"  Compressed: {new_size // 1024}KB")


if __name__ == "__main__":
    all_items = [HERO] + TIPS
    print(f"Generating {len(all_items)} images with {MODEL}...")

    success = 0
    for i, (name, filepath, prompt) in enumerate(all_items):
        print(f"[{i+1}/{len(all_items)}] {name}")
        try:
            if generate_image(name, filepath, prompt):
                compress_image(filepath)
                success += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDone: {success}/{len(all_items)} images generated.")
