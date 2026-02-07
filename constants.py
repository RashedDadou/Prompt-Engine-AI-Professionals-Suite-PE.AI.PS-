from typing import FrozenSet
import re

# ════════════════════════════════════════════════════════════════
#  مؤشرات تصنيف الطلب: صورة / رسم / prompt مقابل نص فقط
# ════════════════════════════════════════════════════════════════

IMAGE_POSITIVE_INDICATORS: FrozenSet[str] = frozenset({
    # طلب مباشر عالي الثقة
    "صورة", "صوره", "صور", "صورنا", "صورهم", "صورلي", "صور لي",
    "ارسم", "رسم", "ارسمه", "ارسمها", "ارسمي", "نرسم", "رسملي",
    "توليد", "توليد صورة", "ولد صورة", "ولّد صورة",
    "أنشئ", "انشئ", "أنشئي", "اصنع", "اصنعي", "صنع صورة",
    "generate", "gen image", "create image", "make image", "imagine",
    "prompt", "برومبت", "وصف صورة", "وصف للصور",

    # أدوات / نماذج شائعة (غالباً طلب صورة)
    "midjourney", "dalle", "stable diffusion", "sdxl", "flux", "imggen",

    # عبارات وصفية شائعة جدًا (تزيد الاحتمالية)
    "شكله", "شكلها", "مظهره", "يبدو", "تبدو", "منظر", "منظرها",
    "تخيل", "شوفلي", "وريني", "اي صورة", "صورة عن", "صورة لـ",
})

IMAGE_NEGATIVE_PATTERNS: tuple[str, ...] = (
    # نفي صريح للصورة
    r"(بدون|من غير|مش|ما|لا)\s*(صورة|صور|رسم|prompt|image|picture|صوره)",
    r"نص فقط|text only",
    r"لا اريد.*(صورة|رسم|prompt)",
    r"بدون.*(صور|صوره|رسم|صورة|image)",
    r"شرح فقط|وصف فقط|كتابة فقط|اكتب فقط",
)

def normalize_text_for_image_check(text: str) -> str:
    """
    تطبيع النص لفحص الكلمات المفتاحية بدقة:
    - تحويل لـ lowercase
    - إزالة علامات الترقيم
    - تقليص المسافات الزائدة
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)      # إزالة كل شيء غير حروف/أرقام/مسافات
    text = re.sub(r'\s+', ' ', text)         # مسافة واحدة فقط
    return text.strip()


def is_likely_image_request(text: str) -> bool:
    """
    هل الطلب يبدو أنه يطلب صورة / رسم / prompt لتوليد صورة؟
    ترتيب الفحص: نفي أولاً → إيجابيات → fallback
    """
    if not text or len(text.strip()) < 4:
        return False

    normalized = normalize_text_for_image_check(text)

    # 1. نفي قوي أولاً (حتى لو في كلمة إيجابية)
    for pattern in IMAGE_NEGATIVE_PATTERNS:
        if re.search(pattern, normalized):
            return False

    # 2. وجود أي مؤشر إيجابي مباشر → نعم صورة
    if any(indicator in normalized for indicator in IMAGE_POSITIVE_INDICATORS):
        return True

    # 3. fallback بسيط: وصف طويل بدون نفي → احتمال صورة
    words = normalized.split()
    if len(words) >= 9:  # وصف طويل نسبيًا
        return True

    return False