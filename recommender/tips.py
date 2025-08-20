# recommender/tips.py

# --- Skin Type Recommendations ---
SKIN_TYPE_TIPS = {
    "dry": (
        "Hydrate your skin with a rich moisturizer before makeup. "
        "Use dewy or luminous foundations, cream blush, and avoid heavy powders "
        "which can emphasize dry patches."
    ),
    "normal": (
        "Lucky you! Most products suit your skin. "
        "Lightweight or medium coverage foundation, natural finishes, "
        "and versatile looks work best."
    ),
    "oily": (
        "Prep with mattifying primer to control shine. "
        "Use oil-free matte foundation, set with a light powder, "
        "and carry blotting papers for touch-ups."
    )
}

# --- Eye Color Recommendations ---
EYE_COLOR_TIPS = {
    "Amber": (
        "Golden and copper shades highlight amber eyes beautifully. "
        "Warm smoky tones work best for both day and evening looks."
    ),
    "Blue": (
        "Bronze, peach, and warm browns enhance blue eyes. "
        "For a bold look, try navy or deep purple liners."
    ),
    "Brown": (
        "Almost any color suits brown eyes. "
        "Purples, greens, and metallic tones add extra contrast."
    ),
    "Green": (
        "Reddish and plum shades enhance green eyes. "
        "Earthy golds and browns also complement well."
    ),
    "Grey": (
        "Silver, smokey charcoal, and cool-toned palettes bring out grey eyes. "
        "Soft blues also create a striking effect."
    ),
    "Hazel": (
        "Hazel eyes pop with golden tones, greens, and warm browns. "
        "You can switch palettes depending on whether you want the green or brown to stand out."
    )
}

# --- Acne Severity Recommendations ---
ACNE_TIPS = {
    "clear": (
        "Your skin is clear — opt for breathable lightweight products. "
        "Tinted moisturizer or BB cream is enough for a natural glow."
    ),
    "mild": (
        "Use spot concealers with salicylic acid for small blemishes. "
        "Choose a lightweight, oil-free foundation for all-day comfort."
    ),
    "moderate": (
        "Go for medium-to-full coverage non-comedogenic foundation. "
        "Avoid heavy creams and finish with a setting spray instead of layers of powder."
    ),
    "severe": (
        "Choose dermatologist-approved breathable foundations. "
        "Stick to minimal layering — color correct where needed and avoid thick foundation stacks."
    )
}

# --- Segmentation Recommendations ---
SEGMENTATION_TIPS = {
    "darkcircle": (
        "Apply peach/orange corrector before concealer to neutralize blue/purple tones. "
        "Set lightly with powder to avoid creasing."
    ),
    "selasne": (
        "Soothe redness and irritation with calming primer. "
        "Use lightweight breathable coverage instead of heavy foundation."
    ),
    "skinredness": (
        "Use green-tinted primer to cancel redness before foundation. "
        "Stick with neutral, medium coverage products."
    ),
    "vascular": (
        "Choose full coverage foundation with gentle application (avoid rubbing). "
        "A soft sponge works better than brushes here."
    ),
    "wrinkle": (
        "Hydrate well before makeup. "
        "Use a smoothing primer, lightweight foundation, "
        "and avoid baking powders that settle into fine lines."
    )
}

# --- YOLO Skin Defect Recommendations ---
YOLO_TIPS = {
    "blackhead": (
        "Prep with a gentle exfoliating primer. "
        "Stick to oil-free matte foundation and avoid heavy cream products."
    ),
    "cystic": (
        "Opt for breathable, full-coverage formulas. "
        "Avoid piling on thick foundation — spot conceal instead."
    ),
    "folliculitis": (
        "Mineral makeup is best to avoid irritation. "
        "Choose lightweight powders over heavy liquids."
    ),
    "keloid": (
        "Keep makeup minimal around raised scars. "
        "A color corrector + lightweight foundation works better than heavy coverage."
    ),
    "milium": (
        "Avoid heavy creams and shimmery highlighters over texture. "
        "Stick to matte, lightweight products."
    ),
    "papular": (
        "Full-coverage, oil-free foundation conceals bumps without clogging pores. "
        "Apply with a sponge for smoother blending."
    ),
    "purulent": (
        "Choose breathable formulas and antibacterial concealers. "
        "Never try to cover with thick layers — let skin breathe."
    ),
    "acne_scars": (
        "A silicone-based primer helps smooth skin texture. "
        "Pair with buildable full-coverage foundation or concealer."
    ),
    "acne": (
        "Spot concealers with acne-fighting ingredients (like salicylic acid) "
        "cover while helping heal."
    ),
    "pimple": (
        "Apply color-corrector (green) under concealer for redness. "
        "Use antibacterial concealer if available."
    ),
    "spot": (
        "Correct discoloration before applying foundation for an even base. "
        "Avoid layering too much product directly on the spot."
    )
}
