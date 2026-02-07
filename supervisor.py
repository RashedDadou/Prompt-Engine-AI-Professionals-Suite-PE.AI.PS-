# داخل ملف supervisor.py

# ──────────────────────────────────────────────
# المكتبات القياسية والـ typing
# ──────────────────────────────────────────────
import re
import time
import threading
import logging
from typing import Optional, Dict

# ──────────────────────────────────────────────
# المكتبات الخاصة بالمشروع (imports الداخلية)
# ──────────────────────────────────────────────
from ai_helper import AIHelper
from base_agent import BaseAgent
from text_assistant import AITextAssistant
from image_assistant import AIImageAssistant
from text_feedback import TextFeedbackLoop

# ──────────────────────────────────────────────
# الإعدادات والثوابت (constants)
# ──────────────────────────────────────────────
from constants import (
    IMAGE_POSITIVE_INDICATORS,          # لو لسة مستخدمة في مكان ما
    IMAGE_NEGATIVE_PATTERNS,            # لو موجودة
    normalize_text_for_image_check,
    is_likely_image_request,
)

# ──────────────────────────────────────────────
# إعداد logging مرة واحدة
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ──────────────────────────────────────────────
# تعريف القوائم المحلية (إذا كنت عايز تحتفظ بيها داخل الملف مؤقتاً)
# ──────────────────────────────────────────────

IMAGE_POSITIVE_INDICATORS = frozenset([
    "صورة", "صوره", "صور", "ارسم", "رسم", "توليد", "generate", "إنشاء",
    "prompt", "وصف الصورة", "imagine", "render", "drawing", "visual",
    # إضافات للطلبات الوصفية المباشرة
    "شكل", "مظهر", "يبدو", "تبدو", "منظر", "تصميم", "توهج", "glow",
])

IMAGE_NEGATIVE_PATTERNS = frozenset([
    "اكتب", "شرح", "ما هو", "تعريف", "قائمة", "كيف", "لماذا", "متى", "أين",
    "code", "برمج", "python", "javascript", "حساب", "معادلة", "نسبة",
    # أنماط نصية بحتة لا تحتاج صورة
    "ما معنى", "ما الفرق", "مقارنة", "مزايا", "عيوب", "تاريخ"
])

class AISupervisor:
    def __init__(self):
        self.name = "AI Supervisor"
        self.text_assistant = AITextAssistant()
        self.feedback_loop = TextFeedbackLoop()

    def is_image_request(self, text: str) -> bool:
        """
        الدالة الرئيسية الوحيدة لتحديد ما إذا كان الطلب يتعلق بتوليد صورة
        """
        if not text or len(text.strip()) < 4:
            return False

        normalized = text.lower().strip()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        # override سلبي قوي
        has_strong_negative = any(neg in normalized for neg in IMAGE_REQUEST_NEGATIVE_INDICATORS)
        has_strong_positive = any(pos in normalized for pos in ["صورة", "ارسم", "رسم", "prompt", "توليد", "إنشاء"])

        if has_strong_negative and not has_strong_positive:
            return False

        has_visual = any(obj in normalized for obj in VISUAL_OBJECTS)
        if has_visual and len(normalized.split()) >= 4:
            return True
    
        # وجود أي مؤشر إيجابي → نعم
        if any(ind in normalized for ind in IMAGE_REQUEST_POSITIVE_INDICATORS):
            return True

        # regex أذكى
        patterns = [
            r"كيف.*(يبدو|شكله|تبدو|منظر|مظهر)",
            r"ارسم.*(لي|لنا|يا|مع|ب)",
            r"(وصف|صف).*(صورة|شكل|مظهر|منظر)",
            r"(تخيل|imagine).*(صورة|scene|view|شكل)",
            r"(generate|توليد|إنشاء|أنشئ).*(صورة|image)",
        ]
        if any(re.search(pat, normalized) for pat in patterns):
            return True

        # fallback: وصف طويل ووصفي
        words = normalized.split()
        if len(words) < 5:
            return False

        descriptive_words = sum(1 for w in words if len(w) > 5 and w not in {"في", "من", "على", "ال", "و", "ب", "ل"})
        return descriptive_words / len(words) > 0.35
        
    def _requires_image(self, text: str) -> bool:
        """فحص بسيط جدًا"""
        keywords = ["صورة", "ارسم", "رسم", "image", "prompt", "صور", "توليد صورة", "شكل", "مظهر", "visual"]
        return any(word in text.lower() for word in keywords)
    
    def _needs_image(self, text: str) -> bool:
        """فحص بسيط جدًا لمعرفة إذا الطلب يحتاج صورة أم لا"""
        keywords = ["صورة", "ارسم", "رسم", "prompt", "image", "صور", "توليد صورة", "شكل", "مظهر"]
        return any(kw in text.lower() for kw in keywords)

    def decide_task_type(self, request: str) -> str:
        """
        الاسم أوضح: ليس مجرد next step، بل نوع المهمة الرئيسي
        يمكن توسيعه لاحقًا (text, image, mixed, search, code, ...)
        """
        return "image" if self.is_image_related(request) else "text"

    # ──────────────────────────────────────────────
    # إما: احتفظ بهذه الدالة للتوافق الخلفي (backward compat)
    # أو احذفها نهائيًا واستخدم is_image_related مباشرة
    def requires_image(self, request: str) -> bool:
        """للتوافق مع الكود القديم – يُفضل استبدال كل استدعاءاتها بـ is_image_related"""
        return self.is_image_related(request)
    
    def comprehensive_review(
        self,
        text_report: dict,
        image_report: dict | None = None,
        original: str = "",           # اختياري – لو كنت تحتاجه لعرض الطلب الأصلي
        text_result: str = "",        # اختياري – لو كنت تريد عرض النص المحسن
        image_result: str | None = None
    ) -> tuple[bool, str, str | None]:
        """
        المراجعة الشاملة الرئيسية – تجمع وظائف review + comprehensive_review
        """
        issues = []
        notes  = []
        critical_count = 0

        # ─── معالجة تقرير النص ───
        errors = text_report.get("errors_found", [])
        suggestions = text_report.get("suggestions", [])

        for item in errors + suggestions:
            lower = item.lower()
            if any(kw in lower for kw in ["تناقض", "تعارض", "خطأ جسيم", "غير متسق", "متناقض"]):
                issues.append(item)
                critical_count += 1
            elif any(kw in lower for kw in ["خطأ", "مشكلة", "ناقص", "مفقود", "غامض", "غير دقيق"]):
                issues.append(item)
            elif any(kw in lower for kw in ["تحسين", "إضافة", "اقتراح", "تصحيح", "أفضل", "أوضح"]):
                notes.append(item)

        # ─── معالجة تقرير الصورة ───
        if image_report:
            if not image_report.get("ready", False):
                issues.append("وصف الصورة غير جاهز – يوجد مشاكل في التناسق أو نقص تفاصيل")
                critical_count += 1
            if img_issues := image_report.get("issues", []):
                issues.extend(img_issues)
                if any("تناقض" in i.lower() or "تعارض" in i.lower() for i in img_issues):
                    critical_count += 1

        # ─── قرار نهائي أكثر ذكاءً ───
        if critical_count > 0 or len(issues) >= 3:
            msg = (
                f"[{self.name}] وجدت مشاكل مهمة:\n"
                f"• {'\n• '.join(issues[:5])}\n"
                f"{'    ... و{len(issues)-5} مشكلة أخرى' if len(issues) > 5 else ''}\n"
                "→ يُوصى بإعادة المعالجة مع التركيز على النقاط أعلاه."
            )
            return False, msg, "reprocess_with_feedback"

        # نجاح
        msg = f"[{self.name}] المحتوى مقبول وجاهز للاستخدام النهائي."
        if notes:
            msg += "\nملاحظات وتحسينات:\n" + "• " + "\n• ".join(notes[:4])
            if len(notes) > 4:
                msg += f"\n    ... و{len(notes)-4} ملاحظة أخرى"

        # إضافة عرض النتيجة النهائية (بديل لـ review و summarize_final_result)
        if text_result or image_result:
            msg += "\n\nالنتيجة النهائية:\n"
            if original:
                msg += f"الطلب الأصلي: {original}\n\n"
            if text_result:
                msg += f"النص المحسن:\n{text_result.strip()}\n"
            if image_result:
                msg += f"\nوصف الصورة الجاهز:\n{image_result.strip()}"

        return True, msg, None

    def summarize_final_result(self, text_result: str, image_result: Optional[str] = None) -> str:
        """تلخيص أنيق للنتيجة النهائية"""
        summary = f"[{self.name}] النتيجة النهائية بعد المراجعة:\n\n"
        summary += f"الوصف النصي المحسن:\n{text_result.strip()}\n"
        if image_result:
            summary += f"\nوصف الصورة الجاهز:\n{image_result.strip()}"
        summary += "\n\nإذا كنت تريد تعديل أي جزء، أخبرني مباشرة."
        return summary

    def generate(self, prompt: str, **kwargs) -> str:
        task_type = self.decide_task_type(prompt)
        return f"[{self.name}] تم تحليل الطلب. نوع المهمة: {task_type.upper()}. سأوجهها للمتخصص المناسب."

    def review(self, original: str, text_result: str, image_result: Optional[str] = None) -> tuple[bool, str, Optional[str]]:
        """
        ترجع ثلاثة أشياء:
        - success: True إذا النتيجة مقبولة، False إذا تحتاج تعديل
        - message: الرسالة النهائية أو الملاحظات
        - issue: وصف المشكلة إذا وجدت (لتمريرها للمحاولة التالية)
        """
        issues = []

        # فحص بسيط لكن أكثر موثوقية من مجرد كلمات
        if "غير موجود" in text_result or "ناقص" in text_result or "تناقض" in text_result:
            issues.append("مشكلة في النص المحسن: بعض التفاصيل ناقصة أو متناقضة")

        if image_result:
            if "تناقض" in image_result or "غير مذكور" in image_result or "ناقص" in image_result:
                issues.append("مشكلة في وصف الصورة: عدم تناسق مع النص")

        final_text = f"الطلب: {original}\n\nالنص المحسن:\n{text_result}"
        if image_result:
            final_text += f"\n\nوصف الصورة:\n{image_result}"

        if issues:
            issue_desc = "؛ ".join(issues)
            msg = f"[{self.name}] وجدت مشاكل:\n{issue_desc}\n→ أطلب تعديل"
            return False, msg, issue_desc
        else:
            return True, f"[{self.name}] النتيجة النهائية:\n\n{final_text}", None

    def is_image_related(self, text: str) -> bool:
        """
        السؤال الرئيسي: هل الطلب يبدو أنه يطلب صورة / وصف صورة / رسم / prompt؟
        تستخدم هذه الدالة في كل مكان بدل التكرار.
        """
        if not text or len(text.strip()) < 3:
            return False
            
        normalized = normalize_text_for_image_check(text)
        
        # أسرع طريقة: أي كلمة واحدة من القائمة موجودة؟
        return any(ind in normalized for ind in IMAGE_POSITIVE_INDICATORS)

# ────────────────────────────────────────────────
#  النظام الرئيسي
# ────────────────────────────────────────────────

class AISupervisorSystem:
    def __init__(self):
        self.supervisor = AISupervisor()
        self.text_assistant = AITextAssistant()
        self.feedback_loop = TextFeedbackLoop()
        self.image_assistant = AIImageAssistant(api_provider="replicate", api_key="r8_xxxxxxxxxx")  # ضع مفتاحك

        # ← أضف هنا (السطرين دول)
        from ai_helper import AIHelper
        self.helper = AIHelper()
            
    def process(self, user_input: str, max_attempts: int = 3):
        print("\n" + "═" * 70)
        print(f"الطلب: {user_input}\n")

        # ─── النص الذي سنعمل عليه دائماً (single source of truth) ───
        working_text = user_input.strip()
        attempt = 0
        final_result = None
        image_report = None

        while attempt < max_attempts:
            attempt += 1
            print(f"محاولة {attempt}/{max_attempts}")

            # تنظيف الاقتراحات السابقة من المحاولات السابقة
            working_text = re.sub(r'\(إجراء مقترح:.*?\)', '', working_text, flags=re.DOTALL).strip()
            working_text = re.sub(r'\s+', ' ', working_text)

            # 1. تحسين النص الأساسي (تصحيح نحوي ولغوي)
            text_report = self.text_assistant.correct_text(working_text)
            improved_text = text_report.get("corrected_text", working_text)

            # نحدث working_text بالنسخة المصححة
            working_text = improved_text

            print("النص بعد التصحيح والتحسين:")
            print(working_text)
            print()

            # 2. استشارة AIHelper على النسخة المحسنة بالفعل
            helper_response = self.helper.consult(working_text)
            enriched_text = helper_response.get("enriched_prompt", working_text)

            # إذا كان الإثراء مفيداً (غير فارغ ومختلف)، نعتمده
            if enriched_text.strip() and enriched_text != working_text:
                working_text = enriched_text
                print("→ تم إثراء النص من AIHelper")

            # طباعة الأسئلة والملاحظات مرة واحدة فقط
            if attempt == 1:
                if helper_response.get("questions"):
                    print("أسئلة للتوضيح من AI Helper:")
                    for q in helper_response["questions"]:
                        print(f"  • {q}")
                if helper_response.get("notes"):
                    print("ملاحظات من AI Helper:")
                    for note in helper_response["notes"]:
                        print(f"  • {note}")

            # تحديد نوع المهمة بناءً على النص الأصلي (أو يمكن تغييره لاحقاً إلى working_text)
            is_image_task = self.supervisor.requires_image(user_input)   # ← يمكن مناقشة تغييره إلى working_text

            if is_image_task:
                print("→ يبدو أن الطلب يحتاج صورة، جاري الإشراف وتوليد الوصف...\n")

                detail_level = helper_response.get("recommended_detail_level", "medium")
                if attempt >= 2:
                    detail_level = "high"

                # نستخدم أحدث نسخة (المحسنة + المثراة)
                image_report = self.text_assistant.supervise_and_generate(
                    enhanced_text=working_text,          # ← التعديل المهم
                    iteration=attempt,
                    max_detail_level=detail_level
                )

                # تحسين الـ prompt بـ priority/forbidden
                if prompt := image_report.get("prompt"):
                    for kw in helper_response.get("priority_keywords", []):
                        if kw not in prompt:
                            prompt += f", {kw}"
                    for kw in helper_response.get("forbidden_keywords", []):
                        prompt = re.sub(rf'\b{re.escape(kw)}\b', '', prompt, flags=re.IGNORECASE).strip()
                    image_report["prompt"] = prompt

                print("الـ Prompt النهائي للصورة:")
                print(image_report.get("prompt", "غير متوفر"))
                print("\nNegative prompt:")
                print(image_report.get("negative_prompt", "غير متوفر"))
                print("\nالحالة:", "جاهز" if image_report.get("ready", False) else "فيه مشاكل")
                if issues := image_report.get("issues"):
                    print("المشاكل:", " | ".join(issues))

            else:
                print("→ الطلب نصي فقط، لا حاجة لتوليد صورة.")

            print("-" * 70)

            # 3. مراجعة شاملة
            ok, review_msg, action = self.supervisor.comprehensive_review(
                text_report=text_report,
                image_report=image_report,
                original=user_input,
                text_result=working_text,           # أو last_improved_text أو enriched_text
                image_result=image_report.get("prompt") if image_report else None
            )
            print("─" * 50)
            print(review_msg)

            # 4. تحسين prompt إذا كان موجوداً
            if is_image_task and image_report and (prompt := image_report.get("prompt")):
                category = helper_response.get("suggested_category", "spacecraft")
                is_good, report, suggestions = self.feedback_loop.analyze_prompt(prompt, category)

                print("تقرير نصي سريع من TextFeedbackLoop:")
                print(report)

                if not is_good and (additions := suggestions.get("prompt_add")):
                    extra = ", " + ", ".join(additions).strip(", ")
                    prompt += ", " + extra
                    print(f"→ تم تحسين الـ prompt تلقائيًا: {extra}")
                    image_report["prompt"] = prompt

                self.feedback_loop.update_history(category, prompt, is_good)

            # 5. قرار الخروج
            if helper_response.get("should_reprocess", False) or ok or (image_report and image_report.get("ready", False)):
                print("→ النتيجة جيدة، بننهي هنا.")
                final_result = review_msg
                break

            # 6. إعداد المحاولة التالية
            if attempt < max_attempts:
                suggestion = action or "حاول تحسين الوصف أكثر وضوحًا ودقة"
                working_text += f" (إجراء مقترح: {suggestion})"
                print(f"→ جاري محاولة تعديل فوري: {suggestion}\n")

        # ─── التلخيص النهائي ───────────────────────────────────────────────
        print("\n" + "═" * 70)
        print("=== انتهت المعالجة ===\n")

        if final_result:
            print("═" * 50)
            print("      النتيجة النهائية المقبولة      ")
            print("═" * 50)

            # نستخدم آخر نسخة من working_text
            cleaned_text = BaseAgent.clean_command_words(working_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

            # تنسيق أفضل: فصل التفاصيل إلى نقاط
            if ", " in cleaned_text:
                parts = [p.strip() for p in cleaned_text.split(", ") if p.strip()]
                if parts:
                    formatted_text = parts[0].capitalize()  # الجملة الرئيسية أول حرف كبير
                    if len(parts) > 1:
                        formatted_text += "\n\nالتفاصيل المضافة:\n• " + "\n• ".join(parts[1:])
                    else:
                        formatted_text = parts[0]
                else:
                    formatted_text = "[لا يوجد نص محسن]"
            else:
                formatted_text = cleaned_text or "[لا يوجد نص محسن]"

            print("النص المحسن:")
            print(formatted_text)
            print()

            if image_report and image_report.get("ready", False):
                print("وصف الصورة الجاهز:")
                print("Prompt:")
                print(image_report.get("prompt", "غير متوفر"))
                print()
                print("Negative Prompt:")
                print(image_report.get("negative_prompt", "غير متوفر"))
                print()

            print("═" * 60)
        else:
            print("لم نتمكن من الوصول إلى نتيجة مقبولة بعد المحاولات المتاحة.")
            print("يرجى مراجعة الطلب يدويًا أو توضيحه أكثر.")

    def is_image_request(self, text: str) -> bool:
        if not text:
            return False

        t = text.lower().strip()
        t = re.sub(r'[^\w\s]', ' ', t)
        t = re.sub(r'\s+', ' ', t)

        words = t.split()

        # 1. المؤشرات الصريحة (كما هي)
        explicit_indicators = ["صورة", "ارسم", "رسم", "توليد", "generate", "prompt", "imagine"]
        if any(ind in t for ind in explicit_indicators):
            return True

        # 2. شرط جديد: وجود موضوع مرئي + إثراء بصري أو طول وصفي
        visual_nouns = ["صاروخ", "rocket", "مركبة", "spacecraft", "محرك", "engine", "plasma", "توهج", "glow", "exhaust", "plume", "nozzles", "distortion"]
        visual_enrich = ["glowing", "plasma", "ionized", "futuristic", "thrust", "tilt", "perspective", "angled", "cinematic"]

        has_visual_noun = any(n in t for n in visual_nouns)
        has_visual_enrich = any(e in t for e in visual_enrich)

        if has_visual_noun and (has_visual_enrich or len(words) >= 6):
            return True

        # 3. fallback للوصف الطويل
        if len(words) >= 8:
            return True

        return False
          
# ────────────────────────────────────────────────
# تشغيل التجربة
# ────────────────────────────────────────────────
if __name__ == "__main__":
    system = AISupervisorSystem()

    examples = [
        "صاروخ مع محركات baluna",
        "ارسم مركبة فضائية مائلة بدون تحديد الزاوية",
    ]

    for ex in examples:
        print("\n" + "═" * 70)
        system.process(ex)