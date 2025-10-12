// Beauty Tips Generator with Multilingual Support
// Ported from Shopify extension to Django project

const SKIN_TYPE_TIPS = {
  en: {
    Dry: [
      "Use a gentle, cream-based cleanser to avoid stripping natural oils.",
      "Apply a rich, hydrating moisturizer twice daily.",
      "Look for products with hyaluronic acid and ceramides.",
      "Use a humidifier in your bedroom to add moisture to the air.",
      "Avoid hot water when washing your face - use lukewarm instead.",
      "Consider using a facial oil as the last step in your nighttime routine.",
    ],
    Normal: [
      "Maintain your routine with a balanced cleanser and moisturizer.",
      "Use sunscreen daily to prevent premature aging.",
      "Incorporate antioxidants like vitamin C into your morning routine.",
      "Exfoliate 1-2 times per week to maintain smooth skin texture.",
      "Stay hydrated by drinking plenty of water throughout the day.",
      "Consider adding a weekly hydrating mask to your routine.",
    ],
    Oily: [
      "Use a foaming or gel-based cleanser to control excess oil.",
      "Look for non-comedogenic, oil-free moisturizers.",
      "Incorporate salicylic acid or niacinamide to regulate oil production.",
      "Use clay masks 1-2 times per week to absorb excess oil.",
      "Don't skip moisturizer - dehydrated skin can produce more oil.",
      "Consider using blotting papers throughout the day instead of over-washing.",
    ],
  },
  fr: {
    Dry: [
      "Utilisez un nettoyant doux à base de crème pour éviter d'éliminer les huiles naturelles.",
      "Appliquez une crème hydratante riche deux fois par jour.",
      "Recherchez des produits contenant de l'acide hyaluronique et des céramides.",
      "Utilisez un humidificateur dans votre chambre pour ajouter de l'humidité à l'air.",
      "Évitez l'eau chaude pour vous laver le visage - utilisez de l'eau tiède.",
      "Considérez l'utilisation d'une huile faciale comme dernière étape de votre routine nocturne.",
    ],
    Normal: [
      "Maintenez votre routine avec un nettoyant et une crème hydratante équilibrés.",
      "Utilisez un écran solaire quotidiennement pour prévenir le vieillissement prématuré.",
      "Incorporez des antioxydants comme la vitamine C dans votre routine matinale.",
      "Exfoliez 1 à 2 fois par semaine pour maintenir une texture de peau lisse.",
      "Restez hydraté en buvant beaucoup d'eau tout au long de la journée.",
      "Considérez l'ajout d'un masque hydratant hebdomadaire à votre routine.",
    ],
    Oily: [
      "Utilisez un nettoyant moussant ou à base de gel pour contrôler l'excès de sébum.",
      "Recherchez des crèmes hydratantes non comédogènes et sans huile.",
      "Incorporez de l'acide salicylique ou de la niacinamide pour réguler la production de sébum.",
      "Utilisez des masques d'argile 1 à 2 fois par semaine pour absorber l'excès de sébum.",
      "Ne sautez pas la crème hydratante - une peau déshydratée peut produire plus de sébum.",
      "Considérez l'utilisation de papiers buvards tout au long de la journée au lieu de trop laver.",
    ],
  },
  ar: {
    Dry: [
      "استخدم منظف لطيف كريمي لتجنب إزالة الزيوت الطبيعية.",
      "ضع مرطب غني ومرطب مرتين يومياً.",
      "ابحث عن منتجات تحتوي على حمض الهيالورونيك والسيراميد.",
      "استخدم جهاز ترطيب في غرفة نومك لإضافة الرطوبة للهواء.",
      "تجنب الماء الساخن عند غسل وجهك - استخدم الماء الفاتر بدلاً من ذلك.",
      "فكر في استخدام زيت الوجه كخطوة أخيرة في روتينك الليلي.",
    ],
    Normal: [
      "حافظ على روتينك بمنظف ومرطب متوازن.",
      "استخدم واقي الشمس يومياً لمنع الشيخوخة المبكرة.",
      "أدرج مضادات الأكسدة مثل فيتامين سي في روتينك الصباحي.",
      "قشر البشرة 1-2 مرات في الأسبوع للحفاظ على ملمس البشرة الناعم.",
      "ابق رطباً بشرب الكثير من الماء طوال اليوم.",
      "فكر في إضافة قناع مرطب أسبوعي لروتينك.",
    ],
    Oily: [
      "استخدم منظف رغوي أو جل للتحكم في الزيت الزائد.",
      "ابحث عن مرطبات غير كوميدوجينية وخالية من الزيت.",
      "أدرج حمض الساليسيليك أو النياسيناميد لتنظيم إنتاج الزيت.",
      "استخدم أقنعة الطين 1-2 مرات في الأسبوع لامتصاص الزيت الزائد.",
      "لا تتخط المرطب - البشرة المجففة يمكن أن تنتج المزيد من الزيت.",
      "فكر في استخدام أوراق التنشيف طوال اليوم بدلاً من الغسل المفرط.",
    ],
  },
}

const EYE_COLOR_TIPS = {
  en: {
    Brown: [
      "Enhance brown eyes with warm eyeshadow tones like gold, bronze, and copper.",
      "Purple and plum shades create beautiful contrast with brown eyes.",
      "Try navy blue eyeliner instead of black for a softer look.",
      "Green eyeshadows can make brown eyes appear more vibrant.",
    ],
    Blue: [
      "Warm tones like peach, coral, and bronze complement blue eyes beautifully.",
      "Orange and copper eyeshadows make blue eyes pop.",
      "Brown eyeliner can be more flattering than black for everyday wear.",
      "Avoid blue eyeshadows that match your eye color exactly.",
    ],
    Green: [
      "Purple and plum shades are perfect for making green eyes stand out.",
      "Red and pink tones create stunning contrast with green eyes.",
      "Golden and bronze shades enhance the warmth in green eyes.",
      "Brown eyeliner often looks more natural than black with green eyes.",
    ],
    Hazel: [
      "Bring out golden flecks with warm browns and golds.",
      "Purple shades can emphasize green tones in hazel eyes.",
      "Experiment with both warm and cool tones to see what works best.",
      "Bronze and copper eyeshadows enhance the complexity of hazel eyes.",
    ],
    Gray: [
      "Silver and charcoal eyeshadows complement gray eyes naturally.",
      "Purple and plum shades can make gray eyes appear more blue.",
      "Warm browns can bring out any golden flecks in gray eyes.",
      "Black eyeliner creates striking definition with gray eyes.",
    ],
  },
  fr: {
    Brown: [
      "Rehaussez les yeux bruns avec des tons d'ombre à paupières chauds comme l'or, le bronze et le cuivre.",
      "Les nuances violettes et prune créent un beau contraste avec les yeux bruns.",
      "Essayez l'eye-liner bleu marine au lieu du noir pour un look plus doux.",
      "Les ombres à paupières vertes peuvent faire paraître les yeux bruns plus vibrants.",
    ],
    Blue: [
      "Les tons chauds comme la pêche, le corail et le bronze complètent magnifiquement les yeux bleus.",
      "Les ombres à paupières orange et cuivre font ressortir les yeux bleus.",
      "L'eye-liner brun peut être plus flatteur que le noir pour un usage quotidien.",
      "Évitez les ombres à paupières bleues qui correspondent exactement à votre couleur d'yeux.",
    ],
    Green: [
      "Les nuances violettes et prune sont parfaites pour faire ressortir les yeux verts.",
      "Les tons rouges et roses créent un contraste saisissant avec les yeux verts.",
      "Les nuances dorées et bronze rehaussent la chaleur des yeux verts.",
      "L'eye-liner brun paraît souvent plus naturel que le noir avec les yeux verts.",
    ],
    Hazel: [
      "Faites ressortir les paillettes dorées avec des bruns et des ors chauds.",
      "Les nuances violettes peuvent accentuer les tons verts des yeux noisette.",
      "Expérimentez avec des tons chauds et froids pour voir ce qui fonctionne le mieux.",
      "Les ombres à paupières bronze et cuivre rehaussent la complexité des yeux noisette.",
    ],
    Gray: [
      "Les ombres à paupières argentées et anthracite complètent naturellement les yeux gris.",
      "Les nuances violettes et prune peuvent faire paraître les yeux gris plus bleus.",
      "Les bruns chauds peuvent faire ressortir les paillettes dorées des yeux gris.",
      "L'eye-liner noir crée une définition frappante avec les yeux gris.",
    ],
  },
  ar: {
    Brown: [
      "عزز العيون البنية بألوان ظلال العيون الدافئة مثل الذهبي والبرونزي والنحاسي.",
      "الألوان البنفسجية والخوخية تخلق تباين جميل مع العيون البنية.",
      "جرب كحل العيون الأزرق الداكن بدلاً من الأسود للحصول على مظهر أنعم.",
      "ظلال العيون الخضراء يمكن أن تجعل العيون البنية تبدو أكثر حيوية.",
    ],
    Blue: [
      "الألوان الدافئة مثل الخوخي والمرجاني والبرونزي تكمل العيون الزرقاء بشكل جميل.",
      "ظلال العيون البرتقالية والنحاسية تجعل العيون الزرقاء تبرز.",
      "كحل العيون البني يمكن أن يكون أكثر إطراءً من الأسود للاستخدام اليومي.",
      "تجنب ظلال العيون الزرقاء التي تطابق لون عينيك تماماً.",
    ],
    Green: [
      "الألوان البنفسجية والخوخية مثالية لإبراز العيون الخضراء.",
      "الألوان الحمراء والوردية تخلق تباين مذهل مع العيون الخضراء.",
      "الألوان الذهبية والبرونزية تعزز الدفء في العيون الخضراء.",
      "كحل العيون البني غالباً ما يبدو أكثر طبيعية من الأسود مع العيون الخضراء.",
    ],
    Hazel: [
      "أبرز البقع الذهبية بالألوان البنية والذهبية الدافئة.",
      "الألوان البنفسجية يمكن أن تؤكد على الألوان الخضراء في العيون العسلية.",
      "جرب الألوان الدافئة والباردة لترى ما يناسبك أكثر.",
      "ظلال العيون البرونزية والنحاسية تعزز تعقيد العيون العسلية.",
    ],
    Gray: [
      "ظلال العيون الفضية والرمادية الداكنة تكمل العيون الرمادية بشكل طبيعي.",
      "الألوان البنفسجية والخوخية يمكن أن تجعل العيون الرمادية تبدو أكثر زرقة.",
      "الألوان البنية الدافئة يمكن أن تبرز أي بقع ذهبية في العيون الرمادية.",
      "كحل العيون الأسود يخلق تعريف مذهل مع العيون الرمادية.",
    ],
  },
}

const ACNE_SEVERITY_TIPS = {
  en: {
    0: [
      "Maintain your current skincare routine to keep skin clear.",
      "Use a gentle cleanser and non-comedogenic moisturizer.",
      "Don't forget daily sunscreen to prevent post-inflammatory hyperpigmentation.",
      "Consider incorporating antioxidants like vitamin C for overall skin health.",
    ],
    1: [
      "Use a gentle salicylic acid cleanser to prevent clogged pores.",
      "Spot treat blemishes with benzoyl peroxide or tea tree oil.",
      "Avoid over-cleansing, which can irritate skin and worsen breakouts.",
      "Use non-comedogenic products to prevent further clogging.",
    ],
    2: [
      "Consider adding a retinoid to your nighttime routine (start slowly).",
      "Use salicylic acid or benzoyl peroxide products consistently.",
      "Don't pick at blemishes - this can lead to scarring.",
      "Consider seeing a dermatologist for personalized treatment options.",
    ],
    3: [
      "Consult with a dermatologist for prescription treatment options.",
      "Be gentle with your skin - avoid harsh scrubbing or over-treatment.",
      "Consider professional treatments like chemical peels or light therapy.",
      "Maintain a consistent, gentle routine while seeking professional help.",
    ],
  },
  fr: {
    0: [
      "Maintenez votre routine de soins actuelle pour garder une peau claire.",
      "Utilisez un nettoyant doux et une crème hydratante non comédogène.",
      "N'oubliez pas l'écran solaire quotidien pour prévenir l'hyperpigmentation post-inflammatoire.",
      "Considérez l'incorporation d'antioxydants comme la vitamine C pour la santé globale de la peau.",
    ],
    1: [
      "Utilisez un nettoyant doux à l'acide salicylique pour prévenir les pores obstrués.",
      "Traitez localement les imperfections avec du peroxyde de benzoyle ou de l'huile d'arbre à thé.",
      "Évitez le nettoyage excessif, qui peut irriter la peau et aggraver les éruptions.",
      "Utilisez des produits non comédogènes pour éviter d'autres obstructions.",
    ],
    2: [
      "Considérez l'ajout d'un rétinoïde à votre routine nocturne (commencez lentement).",
      "Utilisez des produits à l'acide salicylique ou au peroxyde de benzoyle de manière cohérente.",
      "Ne touchez pas aux imperfections - cela peut conduire à des cicatrices.",
      "Considérez consulter un dermatologue pour des options de traitement personnalisées.",
    ],
    3: [
      "Consultez un dermatologue pour des options de traitement sur ordonnance.",
      "Soyez doux avec votre peau - évitez le gommage dur ou le sur-traitement.",
      "Considérez des traitements professionnels comme les peelings chimiques ou la thérapie par la lumière.",
      "Maintenez une routine cohérente et douce tout en cherchant une aide professionnelle.",
    ],
  },
  ar: {
    0: [
      "حافظ على روتين العناية بالبشرة الحالي للحفاظ على بشرة صافية.",
      "استخدم منظف لطيف ومرطب غير كوميدوجيني.",
      "لا تنس واقي الشمس اليومي لمنع فرط التصبغ بعد الالتهاب.",
      "فكر في دمج مضادات الأكسدة مثل فيتامين سي لصحة البشرة العامة.",
    ],
    1: [
      "استخدم منظف لطيف بحمض الساليسيليك لمنع انسداد المسام.",
      "عالج البقع موضعياً ببيروكسيد البنزويل أو زيت شجرة الشاي.",
      "تجنب التنظيف المفرط، الذي يمكن أن يهيج البشرة ويزيد من البثور.",
      "استخدم منتجات غير كوميدوجينية لمنع المزيد من الانسداد.",
    ],
    2: [
      "فكر في إضافة ريتينويد لروتينك الليلي (ابدأ ببطء).",
      "استخدم منتجات حمض الساليسيليك أو بيروكسيد البنزويل بانتظام.",
      "لا تلمس البثور - هذا يمكن أن يؤدي إلى ندبات.",
      "فكر في رؤية طبيب الجلدية لخيارات العلاج الشخصية.",
    ],
    3: [
      "استشر طبيب الجلدية لخيارات العلاج بوصفة طبية.",
      "كن لطيفاً مع بشرتك - تجنب الفرك القاسي أو الإفراط في العلاج.",
      "فكر في العلاجات المهنية مثل التقشير الكيميائي أو العلاج بالضوء.",
      "حافظ على روتين ثابت ولطيف أثناء طلب المساعدة المهنية.",
    ],
  },
}

// Main function to generate tips based on analysis results and current language
function generateTips(analysisData, language = "en") {
  const tips = []

  // Add skin type tips
  if (analysisData.skin_type && SKIN_TYPE_TIPS[language] && SKIN_TYPE_TIPS[language][analysisData.skin_type]) {
    tips.push(...SKIN_TYPE_TIPS[language][analysisData.skin_type].slice(0, 2))
  }

  // Add eye color tips
  if (
    analysisData.left_eye_color &&
    EYE_COLOR_TIPS[language] &&
    EYE_COLOR_TIPS[language][analysisData.left_eye_color]
  ) {
    tips.push(...EYE_COLOR_TIPS[language][analysisData.left_eye_color].slice(0, 1))
  }
  if (
    analysisData.right_eye_color &&
    EYE_COLOR_TIPS[language] &&
    EYE_COLOR_TIPS[language][analysisData.right_eye_color] &&
    analysisData.right_eye_color !== analysisData.left_eye_color
  ) {
    tips.push(...EYE_COLOR_TIPS[language][analysisData.right_eye_color].slice(0, 1))
  }

  // Add acne severity tips
  if (analysisData.acne_pred !== undefined) {
    const acneLevel = Number.parseInt(analysisData.acne_pred) || 0
    if (ACNE_SEVERITY_TIPS[language] && ACNE_SEVERITY_TIPS[language][acneLevel]) {
      tips.push(...ACNE_SEVERITY_TIPS[language][acneLevel].slice(0, 2))
    }
  }

  // Remove duplicates and limit total tips
  const uniqueTips = [...new Set(tips)]
  return uniqueTips.slice(0, 8) // Limit to 8 tips maximum
}

// Function to regenerate tips when language changes
function regenerateTipsForLanguage(analysisData, newLanguage) {
  return generateTips(analysisData, newLanguage)
}

// Export for use in other files (if using modules)
if (typeof module !== "undefined" && module.exports) {
  module.exports = { generateTips, regenerateTipsForLanguage, SKIN_TYPE_TIPS, EYE_COLOR_TIPS, ACNE_SEVERITY_TIPS }
}
