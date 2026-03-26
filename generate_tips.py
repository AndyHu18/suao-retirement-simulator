"""
Generate 12 tip illustration images using Gemini API.
Run once locally, commit the images. Not needed at runtime.
"""

import os
import base64
from google import genai

client = genai.Client(api_key="AIzaSyCTKsiKRWtOk8xNo7xmUDH1m1eZVoFM1nw")

TIPS_PROMPTS = [
    # (filename, english prompt for illustration)
    ("tip_flywheel",
     "Minimal flat illustration of a golden flywheel mechanism with arrows showing a virtuous cycle: insurance -> trust -> people -> occupancy -> reputation. "
     "Warm beige background, gold and brown tones, clean vector style, no text, soft shadows, modern infographic aesthetic."),

    ("tip_default_loss",
     "Minimal flat illustration of a dashboard showing a red downward chart with a hand adjusting sliders upward, symbolizing improvement. "
     "Warm beige background, gold accent color, clean vector style, no text, modern UI mockup aesthetic."),

    ("tip_chart_reading",
     "Minimal flat illustration of a line chart with a blue thick line in the middle and a light blue confidence band around it, crossing a horizontal zero line. "
     "Green area above zero, red area below. Warm beige background, clean vector style, no text."),

    ("tip_insurance",
     "Minimal flat illustration of a golden shield with an insurance symbol merging with a house icon, representing insurance-linked retirement living. "
     "Warm beige background, gold and brown tones, clean vector style, no text, soft glow effect."),

    ("tip_stress_test",
     "Minimal flat illustration of 6 storm cloud icons each with different symbols (economy crash, exit wave, trust crisis, cost spike, compound disaster, empty demand). "
     "Arranged in a 2x3 grid. Warm beige background, muted red and gold tones, clean vector style, no text."),

    ("tip_cold_spring",
     "Minimal flat illustration of a serene natural hot spring scene with bubbles rising from crystal clear water, surrounded by green mountains. "
     "A small elegant building nearby. Warm golden light, beige and teal tones, clean vector style, no text, peaceful mood."),

    ("tip_brand_aging",
     "Minimal flat illustration showing two contrasting communities: left side with elderly residents and fading colors, right side with mixed-age residents and vibrant colors. "
     "An arrow from left to right showing rejuvenation. Warm beige background, clean vector style, no text."),

    ("tip_advanced_mode",
     "Minimal flat illustration of a control panel with many sliders and knobs, some highlighted in gold showing fine-tuning capability. "
     "A magnifying glass over one slider. Warm beige background, gold accents, clean vector style, no text."),

    ("tip_ai_advisor",
     "Minimal flat illustration of an AI brain icon next to a multi-section report document with charts and bullet points. "
     "A speech bubble with insight symbols. Warm beige background, gold and purple accents, clean vector style, no text."),

    ("tip_industry_numbers",
     "Minimal flat illustration of key metrics displayed as large numbers on cards: 85% with a green checkmark, 250 with a calendar icon, 60-70% with a people icon. "
     "Warm beige background, gold tones, clean vector infographic style, no text labels."),

    ("tip_waterfall",
     "Minimal flat illustration of a waterfall chart with green bars going up (income) and red bars going down (costs), with a final blue bar showing net result. "
     "Warm beige background, clean vector style, no text, modern financial chart aesthetic."),

    ("tip_h_hotel",
     "Minimal flat illustration of a luxury boutique hotel building with golden light, connected by a dotted arrow to a retirement community. "
     "Small people figures walking from hotel to community. Warm beige background, gold tones, clean vector style, no text."),
]


def generate_image(prompt, filename):
    """Generate a single image using Gemini."""
    full_prompt = (
        f"{prompt} "
        "Square format 1:1 aspect ratio. "
        "All text must be perfectly clear, accurate, and free of any garbled characters. "
        "Style: Apple-inspired minimalist design with warm golden tones."
    )

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",  # Nano Banana Pro — 唯一允許的生圖模型
        contents=full_prompt,
        config=genai.types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img_data = part.inline_data.data
            filepath = f"assets/tips/{filename}.png"
            with open(filepath, "wb") as f:
                f.write(img_data)
            print(f"  Saved: {filepath} ({len(img_data)} bytes)")
            return True

    print(f"  FAILED: {filename} - no image in response")
    return False


if __name__ == "__main__":
    print(f"Generating {len(TIPS_PROMPTS)} tip images...")
    success = 0
    for i, (filename, prompt) in enumerate(TIPS_PROMPTS):
        print(f"[{i+1}/{len(TIPS_PROMPTS)}] {filename}")
        try:
            if generate_image(prompt, filename):
                success += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDone: {success}/{len(TIPS_PROMPTS)} images generated.")
