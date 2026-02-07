# text_assistant.py

import re
from typing import Dict, List, Optional, Tuple
import time
from typing import Optional

from base_agent import BaseAgent

class PromptBuilder:
    def __init__(self):
        # قاعدة المعرفة البصرية (نفس اللي كان عندك تقريباً، بس مركز أكثر)
        self.visual_knowledge = {
            "plasma engines": {
                "desc": "advanced plasma propulsion, glowing blue plasma exhaust, ionized gas plume, high-efficiency thrusters",
                "visual_tags": [
                    "blue plasma glow", "electric blue exhaust", "plasma flame", "ionized trail",
                    "futuristic thrusters", "high-tech engine nozzles"
                ],
                "weight": 1.3   # يعني بنزيد أهميته شوي في الـ prompt
            },
            "15 degrees tilt": {
                "desc": "angled at 15 degrees, inclined structure, 15° tilt for atmospheric entry or thrust vectoring",
                "visual_tags": [
                    "tilted 15 degrees", "angled rocket body", "inclined fuselage", "15 degree inclination"
                ],
                "weight": 1.2
            },
            "rocket": {
                "desc": "multi-stage orbital rocket, aerodynamic fuselage, heat-resistant materials, sci-fi realistic design",
                "visual_tags": [
                    "sleek rocket", "multi-stage spacecraft", "orbital launch vehicle",
                    "titanium carbon composite", "streamlined body"
                ],
                "weight": 1.1
            },
            # أضف لاحقاً: landing legs, fairing, grid fins, starship style, falcon style, إلخ
        }

        self.base_style = (
            "ultra realistic, cinematic lighting, dramatic atmosphere, "
            "volumetric god rays, sharp focus, 8k resolution, masterpiece, best quality"
        )

        self.default_negative = (
            "blurry, low quality, deformed, bad anatomy, extra limbs, "
            "watermark, text, logo, cartoon, unrealistic physics, bad proportions, "
            "low detail, overexposed, underexposed"
        )

        from text_feedback import TextFeedbackLoop
        self.feedback_loop = TextFeedbackLoop()
        
    def build(
        self,
        enhanced_text: str,
        iteration: int = 1,
        style: Optional[str] = None,
        aspect_ratio: str = "--ar 3:4"   # افتراضي رأسي مناسب للصواريخ
    ) -> Dict[str, str]:
        """
        يبني prompt + negative prompt جاهزين للاستخدام مباشرة
        
        Parameters:
            enhanced_text: النص المحسن القادم من المرحلة السابقة
            iteration: رقم المحاولة الحالية (يؤثر على مستوى التفاصيل)
            style: ستايل اختياري (إذا لم يُمرر يُستخدم الافتراضي)
            aspect_ratio: نسبة الأبعاد (مثال: --ar 3:4)
        
        Returns:
            Dict يحتوي على:
            - prompt
            - negative_prompt
            - parameters
            - found_elements
            - iteration
        """
        prompt_parts = []
        found_elements = []

        # ─── 0. تنظيف النص من كلمات الأوامر والاقتراحات السابقة ────────
        clean_text = enhanced_text.strip()
        clean_text = BaseAgent.clean_command_words(enhanced_text)
        clean_text = re.sub(r'(ارسم|draw|generate|توليد|صورة|image|prompt|create|make|رسم|صنع|أنشئ|paint|render|تصميم|design)\b\s*', '', clean_text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r'\(إجراء مقترح:.*?\)', '', clean_text, flags=re.DOTALL | re.IGNORECASE).strip()
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # إزالة كلمات الأوامر (ارسم، صورة، generate، prompt، إلخ)
        clean_text = re.sub(
            r'(ارسم|draw|generate|توليد|صورة|image|prompt|create|make|رسم|صنع|أنشئ|paint|render|تصميم|design)\b\s*',
            '',
            clean_text,
            flags=re.IGNORECASE
        ).strip()

        # إزالة أي اقتراحات سابقة من Supervisor (إجراء مقترح: ...)
        clean_text = re.sub(
            r'\(إجراء مقترح:.*?\)',
            '',
            clean_text,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()

        # تنظيف المسافات الزائدة والتكرار
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # ─── 1. تحديد الموضوع الرئيسي بشكل ذكي (مرة واحدة فقط) ────────────────
        lower_clean = clean_text.lower()

        # أ. تحديد الفئة أولاً (أولوية منطقية + كلمات أكثر شمولاً)
        category = "general"

        if any(w in lower_clean for w in [
            "صاروخ", "rocket", "صواريخ", "starship", "falcon", "falcon heavy",
            "new shepard", "launch vehicle", "booster", "orbital rocket"
        ]):
            category = "rocket"

        elif any(w in lower_clean for w in [
            "محطة", "station", "محطة فضائية", "space station", "orbital station",
            "iss", "orbital habitat", "space outpost"
        ]):
            category = "space_station"

        elif any(w in lower_clean for w in [
            "كبسولة", "capsule", "lander", "هبوط", "reentry", "عودة", "descent vehicle",
            "crew capsule", "apollo", "dragon", "soyuz"
        ]):
            category = "capsule"

        elif any(w in lower_clean for w in [
            "مركبة", "spacecraft", "مركبة فضائية", "سفينة فضاء", "spaceship",
            "interstellar", "probe", "satellite", "orbiter"
        ]):
            category = "spacecraft"

        # ب. اختيار main_subject حسب الفئة (وصف أطول وأدق + وزن خفيف)
        main_subject_map = {
            "rocket": "highly detailed sci-fi rocket, sleek multi-stage orbital vehicle",
            "space_station": "massive modular space station, futuristic orbital habitat",
            "capsule": "compact reentry capsule, crewed descent vehicle, glowing heat shield",
            "spacecraft": "futuristic advanced spacecraft, sleek metallic hull",
            "general": "highly detailed sci-fi spacecraft"
        }

        main_subject = main_subject_map.get(category, main_subject_map["general"])

        # ج. إضافة وزن خفيف للموضوع الرئيسي عشان الـ model يركز عليه أكتر
        main_subject = f"({main_subject}:1.15)"

        prompt_parts.append(main_subject)

        # ج. إضافة وصف الميل بشكل ذكي (بعد الموضوع الرئيسي عشان يرتبط بيه)
        has_tilt = any(kw in lower_clean for kw in ["مائل", "tilt", "angle", "inclined", "زاوية", "انحراف", "ميل"])
        wants_no_specific_angle = any(phrase in lower_clean for phrase in [
            "بدون تحديد", "غير محدد", "غير معروف", "غير ثابت", "unspecified", "arbitrary", "random angle"
        ])

        # داخل الـ if has_tilt:
        if has_tilt:
            if wants_no_specific_angle:
                prompt_parts.append(
                    "(dynamic tilt:1.45), (ambiguous viewing angle:1.35), "
                    "dramatic inclined perspective, cinematic angled shot, "
                    "strong perspective distortion, tilted composition, angled view"
                )
            else:
                # لو محدد زاوية عددية (اختياري، لو عندك شرط لاستخراج الرقم)
                angle_match = re.search(r'(\d+)\s*(درجة|degree|°)', lower_clean)
                if angle_match:
                    angle_val = angle_match.group(1)
                    prompt_parts.append(f"tilted at {angle_val} degrees, precise {angle_val}° inclination")
                else:
                    prompt_parts.append("noticeable tilt, angled composition")                # لو محدد زاوية معينة في النص → نحاول نستخرجها، وإلا نستخدم عام
                angle_match = re.search(r'(\d+)\s*(درجة|degree|°)', lower_clean)
                if angle_match:
                    angle_val = angle_match.group(1)
                    prompt_parts.append(f"tilted at {angle_val} degrees, precise {angle_val}° inclination")
                else:
                    prompt_parts.append("noticeable tilt, strongly angled body, dramatic inclination")

        # د. إضافة النص الأصلي المحسن (بعد الموضوع والميل عشان يبقى في سياق)
        prompt_parts.append(clean_text)

        # ─── 2. إضافة المعرفة البصرية التلقائية (بذكاء أكبر وتنظيف تكرار) ────────
        seen_descriptions = set()  # عشان نمنع تكرار نفس الوصف أو الـ tags

        for key, data in self.visual_knowledge.items():
            if re.search(re.escape(key), clean_text, re.IGNORECASE):
                found_elements.append(key)
                
                # الوصف الرئيسي مع الوزن إذا وجد
                desc = data["desc"]
                if data.get("weight"):
                    desc = f"({desc}:{data['weight']})"
                
                # نضيفه فقط لو مش موجود قبل كده
                if desc not in seen_descriptions:
                    prompt_parts.append(desc)
                    seen_descriptions.add(desc)
                
                # الـ visual_tags (كمان نضيفها لو مش موجودة)
                if data["visual_tags"]:
                    tags_str = ", ".join(data["visual_tags"])
                    if tags_str not in seen_descriptions:
                        prompt_parts.append(tags_str)
                        seen_descriptions.add(tags_str)

        # ─── 3. تحسين تدريجي حسب رقم المحاولة (أقصر وأكثر تركيزًا) ───────────────
        if iteration == 2:
            new_add = "intricate details, refined proportions, photorealistic textures"
            if new_add not in ", ".join(prompt_parts):
                prompt_parts.append(new_add)

        elif iteration >= 3:
            new_add = "extreme detail, hyper-realistic, cinematic depth of field, volumetric god rays, masterpiece quality"
            if new_add not in ", ".join(prompt_parts):
                prompt_parts.append(new_add)
        
        # ─── 4. إضافة الستايل العام (بدون فاصلة زائدة في البداية) ───────────
        final_style = style or self.base_style
        if final_style:
            prompt_parts.append(final_style)

        # ─── 5. تجميع الـ prompt الأولي ────────────────────────────────────────
        current_prompt = ", ".join(filter(None, prompt_parts)).strip(", ")

        # ─── 6. حلقة التغذية الراجعة النصية (TextFeedbackLoop) ────────────────
        category = "spacecraft"  # يمكن تحسينه لاحقًا بتحليل النص أو كلمات مفتاحية

        is_good, report, suggestions = self.feedback_loop.analyze_prompt(
            current_prompt, category
        )

        # تطبيق التعديلات التلقائية إذا لزم الأمر
        if not is_good:
            added = False
            if suggestions.get("prompt_add"):
                current_prompt += ", " + ", ".join(suggestions["prompt_add"])
                added = True

            if added:
                print("→ تم تحسين الـ prompt تلقائيًا بناءً على المراجعة النصية")
                print("النسخة الجديدة (مختصرة):", current_prompt[:200] + "..." if len(current_prompt) > 200 else current_prompt)

        # حفظ الخبرة (دائمًا، حتى لو لم يتم التعديل)
        self.feedback_loop.update_history(category, current_prompt, is_good)

        # ─── 7. إعداد Negative Prompt (يتطور مع الـ iteration) ────────────────
        negative = self.default_negative

        if "cartoon" in clean_text.lower() or "drawn" in clean_text.lower():
            negative += ", painting, sketch, illustration, comic style, anime style"

        if iteration >= 2:
            negative += ", low detail, plastic look, toy-like, oversaturated, jpeg artifacts, compressed"

        # إزالة التكرار في negative prompt
        negative_parts = set(negative.split(", "))
        negative = ", ".join(sorted(negative_parts)).strip(", ")

        # ─── 8. جمع النتيجة النهائية ──────────────────────────────────────────
        result = {
            "prompt": current_prompt.strip(", "),
            "negative_prompt": negative,
            "parameters": aspect_ratio,
            "found_elements": found_elements,
            "iteration": iteration
        }

        return result
    
class AITextAssistant(BaseAgent):
    def __init__(self):
        self.enricher = KnowledgeEnricher()
        self.builder  = PromptBuilder()
        self.checker  = ConsistencyChecker()
        self.refiner  = IterationRefiner()
        self.neg_manager = NegativePromptManager()
        
        # ← أضف هنا
        from text_feedback import TextFeedbackLoop
        self.feedback_loop = TextFeedbackLoop()

        # متغيرات إضافية قد تكون مفيدة (اختياري)
        self.current_iteration = 1
        self.last_report = None           # لتخزين آخر تقرير (اختياري)
        # self.knowledge_library = {}     # لو قررت نرجع نستخدم مكتبة لاحقاً            # عداد المحاولات (يزيد تلقائياً لو في loop)
        
        # قواعد فحص تناقض بسيطة (يمكن توسيعها)
        self.consistency_rules = {
            "plasma engines": ["blue", "plasma", "glow", "exhaust", "thrust"],
            "15 degrees": ["tilt", "angle", "inclined", "15°", "15 degree"],
            "مائل": ["tilt", "angle", "15", "درجة"],
        }

        super().__init__("AI Text Assistant")
        # قاموس تصحيحات عام (مصطلحات تقنية + إملاء شائعة)
        self.corrections = {
            r"\b(baluna|بالونا|بالونة)\b": "plasma engines",
            r"\b(mfshklh|مفشكله|مفشكلة)\b": "مشكلة",  # مثال تصحيح إملاء عام
            r"\b(ghmwz|غموض|غموظ)\b": "غموض",
            r"\b(twzyh|توضيح|توضيه)\b": "توضيح",
            # أضف هنا أي مصطلحات إضافية عامة أو تقنية
        }
        
        # قاموس إضافات تفاصيل شائعة (لإزالة الغموض)
        self.enrichments = {
            "محرك|engine": "، قوة دفع تقريبية 10 meganewtons إذا لم يُحدد",
            "مائل|angle|زاوية": "، مائل بزاوية 15 درجة إذا لم يُحدد",
            "غامض|غموض|مشكلة": "، يُفضل توضيح المصطلحات أو السياق",
            # أضف هنا أي قواعد إضافية
        }

       # قاموس تصحيحات عامة للأخطاء الإملائية والنحوية (محاكاة بسيطة)
        self.spelling_corrections = {
            "mfshklh": "مشكلة",  # مثال إملاء خاطئ
            "ghmwz": "غموض",
            "twzyh": "توضيح",
            "bluna": "plasma",  # تقني
            "baluna": "plasma engines",
            "mharakat": "محركات",  # نحوي/إملائي
            # أضف هنا مزيد من الأخطاء الشائعة
        }
        
        # قاموس لإزالة الغموض (كلمات غامضة وإعادة صياغتها)
        self.ambiguity_resolvers = {
            "غامض": "يرجى توضيح المزيد من التفاصيل حول [الكلمة الغامضة]",
            "غير واضح": "إعادة صياغة لتكون أكثر دقة: [صياغة محسنة]",
            "مشكلة محاذاة": "تصحيح محاذاة المحركات: تأكيد التطابق مع المعايير الفيزيائية (مثل 15 درجة)",
            # أضف هنا مزيد من الحالات
        }
        
    def supervise_and_generate(
        self,
        enhanced_text: str,
        iteration: int = 1,
        max_detail_level: str = "medium",
        custom_style: Optional[str] = None,
        custom_ar: str = "--ar 2:3",
        aggressive_negative: bool = False
    ) -> dict:
        """
        المسار الكامل لتحضير prompt + negative جاهزين للتوليد
        
        الخطوات بالترتيب:
        1. Enrich    → إثراء النص بمعلومات بصرية/تقنية
        2. Build     → بناء الـ prompt الأساسي
        3. Check     → فحص التناسق البصري
        4. Refine    → تحسين إضافي (غالباً يشتغل لو في مشاكل أو iteration > 1)
        5. Negative  → توليد negative prompt سياقي وقوي
        
        Returns:
            dict يحتوي على النتيجة النهائية + تقرير شفاف
        """
        report = {
            "original_text": enhanced_text,
            "iteration": iteration,
            "steps": [],
            "issues": [],
            "warnings": [],
            "summary": "",
            "ready": False,
            "prompt": "",
            "negative_prompt": "",
            "parameters": custom_ar,
            "detail_level_used": max_detail_level,
            "enriched_elements": [],
            "found_elements": [],
        }

        current_text = enhanced_text.strip()

        # ─── 1. Enrich ───────────────────────────────────────────────────────────────
        enrich_result = self.enricher.enrich(
            text=current_text,
            max_additions=4,
            include_visual=True,
            include_tech=(max_detail_level in ["high", "technical"])
        )

        current_text = enrich_result["enriched_text"]
        report["enriched_elements"] = enrich_result["additions"]
        report["steps"].append(f"Enrich → +{len(enrich_result['additions'])} تفصيلة")

        if enrich_result["additions"]:
            report["summary"] += f"تم إثراء النص بـ: {', '.join(enrich_result['additions'][:3])}\n"

        # ─── 2. Build ────────────────────────────────────────────────────────────────
        build_result = self.builder.build(
            enhanced_text=current_text,
            iteration=iteration,
            style=custom_style,
            aspect_ratio=custom_ar
        )

        current_prompt = build_result["prompt"]
        current_negative = build_result["negative_prompt"]  # نقطة بداية
        report["found_elements"] = build_result.get("found_elements", [])
        report["steps"].append("Build → prompt أساسي جاهز")

        # ─── 3. Check ────────────────────────────────────────────────────────────────
        check_result = self.checker.check(
            enhanced_text=current_text,
            generated_prompt=current_prompt
        )

        report["issues"].extend(check_result["issues"])
        report["steps"].append(f"Check → {'تناسق جيد' if check_result['is_consistent'] else f'{len(check_result['issues'])} مشكلة'}")

        if not check_result["is_consistent"]:
            report["warnings"].append("يوجد عناصر مهمة غير ممثلة بصريًا بشكل كافٍ")

        # ─── 4. Refine (غالباً يشتغل إذا في مشاكل أو iteration ≥ 2) ───────────────
        do_refine = (not check_result["is_consistent"]) or (iteration >= 2)

        if do_refine:
            refine_result = self.refiner.refine(
                iteration=iteration,
                current_prompt=current_prompt,
                current_negative=current_negative,
                current_params={"ar": custom_ar}
            )

            current_prompt = refine_result["refined_prompt"]
            current_negative = refine_result["refined_negative"]
            report["steps"].append(f"Refine → {len(refine_result['applied_changes'])} تغيير")
            report["summary"] += f"تم تحسين: {', '.join(refine_result['applied_changes'][:3])}\n"

        # ─── 5. Negative Prompt Management ───────────────────────────────────────────
        negative = self.neg_manager.build_negative(
            enhanced_text=current_text,
            style_keywords=[max_detail_level, custom_style] if custom_style else [max_detail_level],
            aggressive=aggressive_negative
        )

        current_negative = negative  # overwrite with the managed negative
        report["steps"].append("Negative → negative prompt محدث سياقيًا")

        # ─── 6. الحكم النهائي ───────────────────────────────────────────────────────
        report["prompt"] = current_prompt
        report["negative_prompt"] = current_negative
        report["ready"] = len(report["issues"]) == 0 and do_refine  # جاهز لو مفيش مشاكل بعد التحسين
        report["summary"] += f"الحالة النهائية: {'جاهز' if report['ready'] else 'يحتاج تحسين إضافي'}"

        return report

    def analyze_and_fix(self, text: str) -> dict:
        """دالة مؤقتة للتوافق حتى ننقل المنطق لمكانه الصحيح"""
        corrected = text.strip()
        # هنا ممكن تضيف أي تصحيحات بسيطة مؤقتة
        return {
            "corrected_text": corrected,
            "errors_found": [],
            "suggestions": [],
            "had_changes": False
        }
    
    def correct_text(self, text: str) -> dict:
        # نقل المنطق من الدالة القديمة هنا
        corrected = text
        errors = []
        suggestions = []

        # مثال: تصحيح baluna
        if re.search(r'\b(baluna|بالونا|بالونة)\b', corrected, re.IGNORECASE):
            corrected = re.sub(r'\b(baluna|بالونا|بالونة)\b', 'plasma engines', corrected, flags=re.IGNORECASE)
            errors.append("تصحيح 'baluna' إلى 'plasma engines'")

        # مثال: إضافة قوة دفع لو موجود محرك ومش مذكورة
        if "محرك" in corrected and "دفع" not in corrected:
            corrected += "، قوة دفع تقريبية 10 meganewtons إذا لم يُحدد"
            suggestions.append("إضافة قوة دفع افتراضية")

        return {
            "corrected_text": corrected,
            "errors_found": errors,
            "suggestions": suggestions,
            "had_changes": bool(errors or suggestions)
        }
    
class ConsistencyChecker:
    """
    يفحص التناسق بين النص المحسن والـ prompt النهائي
    يبحث عن عناصر مهمة مذكورة في النص وغير موجودة في الـ prompt
    """

    def __init__(self):
        # قائمة عناصر مهمة (يمكن توسيعها)
        self.key_elements = [
            r"plasma\s*engines?", r"بلازما", r"محركات\s*بلازما",
            r"15\s*درجة", r"15\s*degree", r"مائل", r"زاوية\s*15",
            r"multi\s*stage", r"مراحل", r"heat\s*shield", r"درع\s*حراري"
        ]

    def check(self, enhanced_text: str, generated_prompt: str) -> Dict:
        """
        يرجع تقريراً عن التناسق
        
        Returns:
            {
                "is_consistent": bool,
                "issues": List[str],
                "missing_elements": List[str],
                "checked_elements": List[str],
                "summary": str
            }
        """
        lower_text = enhanced_text.lower()
        lower_prompt = generated_prompt.lower()

        issues = []
        missing = []
        mentioned_elements = []

        for pattern in self.key_elements:
            if match := re.search(pattern, lower_text):
                element = match.group(0)
                mentioned_elements.append(element)
                if element.lower() not in lower_prompt:
                    issues.append(f"عنصر مهم '{element}' مذكور في النص لكن غير موجود في الـ prompt")
                    missing.append(element)

        is_consistent = len(issues) == 0

        summary = (
            f"تم فحص {len(mentioned_elements)} عنصر مهم. "
            f"التناسق: {'ممتاز' if is_consistent else f'فيه {len(issues)} مشكلة'}"
        )
        if issues:
            summary += f"\nمشاكل: {'؛ '.join(issues)}"

        return {
            "is_consistent": is_consistent,
            "issues": issues,
            "missing_elements": missing,
            "checked_elements": mentioned_elements,
            "summary": summary
        }
        
class KnowledgeEnricher:
    """
    يثري النص بمعلومات بصرية/تقنية معروفة مسبقاً
    يُستخدم قبل بناء الـ prompt لتحسين الدقة والتفاصيل
    """

    def __init__(self):
        # قاعدة المعرفة: كل مفتاح → (وصف تقني مختصر, وصف بصري, كلمات مفتاحية للبحث)
        self.enrichment_db = {
            "plasma engines": {
                "tech_desc": "محركات دفع بلازما كهربائية عالية الكفاءة، تستخدم غازاً مشحوناً",
                "visual_desc": "توهج أزرق-بنفسجي قوي، لهب بلازما متدفق، أثر أيوني طويل",
                "triggers": [r"plasma\s*engine", r"بلازما", r"plasma\s*propulsion", r"baluna"],
                "priority": "high"
            },
            "15 degrees": {
                "tech_desc": "ميل 15 درجة لتحسين التوجيه أو الدخول الجوي",
                "visual_desc": "انحراف واضح في جسم الصاروخ أو فوهات المحركات بزاوية 15°",
                "triggers": [r"15\s*درجة", r"15\s*degree", r"māʾil", r"tilt.*15", r"angle.*15"],
                "priority": "high"
            },
            "multi-stage": {
                "tech_desc": "صاروخ متعدد المراحل للوصول إلى المدار",
                "visual_desc": "هيكل طويل مقسم إلى مراحل، فواصل واضحة، محركات مختلفة الحجم",
                "triggers": [r"multi.*stage", r"مراحل", r"مرحلة\s*ثانية", r"two-stage", r"three-stage"],
                "priority": "medium"
            },
            "heat shield": {
                "tech_desc": "درع حراري لحماية المركبة أثناء العودة الجوية",
                "visual_desc": "طبقة سوداء أو بلاطات سيراميكية، احتراق برتقالي-أحمر أثناء الدخول",
                "triggers": [r"heat\s*shield", r"درع\s*حراري", r"ablation", r"reentry"],
                "priority": "medium"
            },
            # أضف المزيد تدريجياً: grid fins, landing legs, fairing, RCS thrusters, solar panels...
        }

    def enrich(
        self,
        text: str,
        max_additions: int = 3,
        include_tech: bool = True,
        include_visual: bool = True
    ) -> Dict:
        """
        يثري النص ويرجع تقريراً
        
        Returns:
            {
                "enriched_text": النص بعد الإثراء,
                "additions": قائمة بالإضافات التي تمت,
                "summary": ملخص ما حصل,
                "added_count": عدد الإضافات
            }
        """
        enriched = text.strip()
        additions: List[Tuple[str, str]] = []  # (نوع الإضافة, النص المضاف)

        for key, data in self.enrichment_db.items():
            if len(additions) >= max_additions:
                break

            for trigger in data["triggers"]:
                if re.search(trigger, enriched, re.IGNORECASE):
                    # نتحقق إذا الوصف موجود بالفعل (تجنب التكرار)
                    if include_visual and data["visual_desc"] not in enriched:
                        visual_part = f" ({data['visual_desc']})"
                        enriched += visual_part
                        additions.append(("visual", visual_part.strip(" ()")))

                    if include_tech and data["tech_desc"] not in enriched:
                        tech_part = f"، {data['tech_desc']}"
                        enriched += tech_part
                        additions.append(("tech", data['tech_desc']))

                    break  # نخرج من حلقة الـ triggers لهذا العنصر

        summary = f"تم إضافة {len(additions)} تفصيلة"
        if additions:
            summary += f": {', '.join([a[1][:40] + '...' if len(a[1]) > 40 else a[1] for a in additions])}"

        return {
            "enriched_text": enriched,
            "additions": [a[1] for a in additions],
            "addition_types": [a[0] for a in additions],
            "summary": summary,
            "added_count": len(additions),
            "original_length": len(text),
            "enriched_length": len(enriched)
        }
        
class NegativePromptManager:
    """
    يدير الـ negative prompt بطريقة ذكية:
    - قاعدة أساسية قوية
    - إضافات سياقية حسب الكلمات في النص أو الستايل
    - يمنع التكرار والإفراط في السلبيات
    """

    def __init__(self):
        # النواة الأساسية (دائمًا موجودة)
        self.core_negative = [
            "blurry", "low quality", "lowres", "worst quality",
            "bad anatomy", "extra limbs", "missing limbs", "deformed",
            "poorly drawn face", "poorly drawn hands", "extra fingers",
            "fused fingers", "too many fingers", "bad proportions",
            "watermark", "text", "signature", "logo", "username"
        ]

        # فئات سياقية (تُضاف حسب الطلب)
        self.context_additions = {
            "space": [
                "cartoon", "anime", "illustration", "drawing", "painting",
                "people", "human", "face", "person", "crowd",
                "indoor", "city", "building", "ground", "grass"
            ],
            "realistic": [
                "cartoon", "anime", "3d render", "cgi", "plastic",
                "toy", "figurine", "low poly", "pixel art"
            ],
            "technical": [
                "artistic", "stylized", "sketch", "pencil", "watercolor",
                "abstract", "surreal", "fantasy elements"
            ],
            "vehicle": [
                "human", "person", "animal", "creature",
                "food", "plant", "flower", "tree"
            ]
        }

        # سلبيات خطيرة جدًا (نادرًا ما نزيلها)
        self.hard_negative = [
            "mutation", "ugly", "disfigured", "morbid",
            "out of frame", "cropped", "duplicate"
        ]

    def build_negative(
        self,
        enhanced_text: str = "",
        style_keywords: Optional[List[str]] = None,
        extra_negatives: Optional[List[str]] = None,
        aggressive: bool = False
    ) -> str:
        negatives = set(self.core_negative + self.hard_negative)

        lower_text = enhanced_text.lower()

        # ─── 1. تحديد السياق الرئيسي (مرة واحدة فقط) ────────────────────────
        is_space_context = any(kw in lower_text for kw in [
            "صاروخ", "rocket", "مركبة فضائية", "spacecraft", "محطة فضائية",
            "plasma", "orbit", "space station", "reentry", "capsule", "lander"
        ])

        is_realistic_style = any(kw in lower_text for kw in [
            "realistic", "photoreal", "ultra detailed", "8k", "cinematic",
            "photorealistic", "hyper realistic", "ultra realistic"
        ])

        is_technical_diagram = any(kw in lower_text for kw in [
            "technical", "blueprint", "diagram", "schematic", "cross section",
            "engineering", "technical drawing"
        ])

        # ─── 2. إضافة السلبيات السياقية ───────────────────────────────────────
        if is_space_context:
            negatives.update(self.context_additions["space"])
            negatives.update(self.context_additions["vehicle"])

        if is_realistic_style:
            negatives.update(self.context_additions["realistic"])

        if is_technical_diagram:
            negatives.update(self.context_additions["technical"])

        # ─── 3. اختصار ذكي للسياق الفضائي (بعد الإضافة) ──────────────────────
        if is_space_context:
            # إزالة كل السلبيات اللي مش محتملة في سياق فضائي
            irrelevant = {
                "creature", "face", "person", "human", "people", "crowd",
                "poorly drawn face", "poorly drawn hands", "fused fingers", "extra fingers",
                "too many fingers", "food", "plant", "flower", "tree", "grass", "ground",
                "indoor", "city", "building"
            }
            negatives.difference_update(irrelevant)
        
        # ─── 4. إضافات خارجية و aggressive mode ────────────────────────────────
        if extra_negatives:
            negatives.update(extra_negatives)

        if aggressive:
            extras = ["oversaturated", "underexposed", "overexposed",
                    "jpeg artifacts", "compressed", "pixelated"]
            negatives.update(extras)

        # ─── 5. تنظيف نهائي وترتيب ──────────────────────────────────────────────
        final_list = sorted(list(negatives))  # ترتيب أبجدي للقراءة
        return ", ".join(final_list).strip(", ")

class IterationRefiner:
    """
    يدير التحسين التدريجي عبر المحاولات (iterations)
    يقترح تعديلات متزايدة الدقة / التفاصيل / التركيز
    """

    def __init__(self):
        # مراحل التحسين الافتراضية (يمكن تخصيصها لاحقاً)
        self.refinement_stages = {
            1: {  # المحاولة الأولى: أساسيات + توازن
                "prompt_add": [
                    "highly detailed", "cinematic lighting", "sharp focus"
                ],
                "prompt_weight_boost": [],  # لا نزيد وزن كثير في البداية
                "negative_add": ["jpeg artifacts", "compressed"],
                "parameters": {
                    "stylize": 150,    # متوسط
                    "chaos": 15,       # شوية تنويع
                    "quality": 1.0
                },
                "description": "المحاولة الأولى: توازن جيد بين التفاصيل والإبداع"
            },
            2: {  # المحاولة الثانية: زيادة التفاصيل + تصحيح
                "prompt_add": [
                    "ultra intricate details", "refined proportions",
                    "improved lighting and shadows", "photorealistic textures"
                ],
                "prompt_weight_boost": [  # نزيد وزن العناصر المهمة شوي
                    ("plasma", 1.2),
                    ("blue glow", 1.15),
                    ("tilt", 1.1)
                ],
                "negative_add": ["over-simplified", "low-poly", "flat colors"],
                "parameters": {
                    "stylize": 250,    # أكثر فنية / دقة
                    "chaos": 10,       # أقل عشوائية
                    "quality": 1.5
                },
                "description": "المحاولة الثانية: تركيز أكبر على الدقة والتناسق"
            },
            3: {  # المحاولة الثالثة فما فوق: hyper-detailed + تصحيح نهائي
                "prompt_add": [
                    "hyper detailed", "insane intricate mechanical parts",
                    "16k resolution", "extreme realism", "masterpiece quality"
                ],
                "prompt_weight_boost": [
                    ("plasma engines", 1.35),
                    ("blue plasma exhaust", 1.3),
                    ("15 degrees tilt", 1.25)
                ],
                "negative_add": [
                    "cartoonish", "simplistic", "bad perspective",
                    "distorted proportions", "artifacts"
                ],
                "parameters": {
                    "stylize": 400,    # قوي جداً على الستايل
                    "chaos": 5,        # قليل جداً من العشوائية
                    "quality": 2.0
                },
                "description": "المحاولة الثالثة+: أقصى دقة وواقعية ممكنة"
            }
        }

        # القيم الافتراضية إذا تجاوزنا المراحل المعرفة
        self.fallback_stage = 3

    def refine(
        self,
        iteration: int,
        current_prompt: str,
        current_negative: str,
        current_params: Optional[Dict] = None
    ) -> Dict:
        """
        يطبّق التحسينات على المحاولة الحالية
        
        Returns:
            {
                "refined_prompt": ...,
                "refined_negative": ...,
                "refined_parameters": ...,
                "applied_changes": List[str],
                "stage_description": str
            }
        """
        stage = self.refinement_stages.get(iteration, self.refinement_stages[self.fallback_stage])
        changes = []

        # 1. إضافة نصوص للـ prompt
        refined_prompt = current_prompt
        for add in stage["prompt_add"]:
            if add.lower() not in refined_prompt.lower():
                refined_prompt += f", {add}"
                changes.append(f"+ prompt: {add}")

        # 2. تعزيز أوزان (weight boost) لعناصر معينة
        for elem, weight in stage.get("prompt_weight_boost", []):
            # نتحقق إذا العنصر موجود، ونضيف وزن إذا لم يكن موجود
            if elem.lower() in refined_prompt.lower() and f":{weight}" not in refined_prompt:
                refined_prompt = refined_prompt.replace(
                    elem, f"({elem}:{weight})", 1
                )
                changes.append(f"↑ weight {elem} → {weight}")

        # 3. إضافة للـ negative
        refined_negative = current_negative
        for add in stage["negative_add"]:
            if add.lower() not in refined_negative.lower():
                refined_negative += f", {add}"
                changes.append(f"+ negative: {add}")

        # 4. تحديث الـ parameters (مثل Midjourney / Flux style)
        refined_params = current_params.copy() if current_params else {}
        refined_params.update(stage["parameters"])

        return {
            "refined_prompt": refined_prompt.strip(", "),
            "refined_negative": refined_negative.strip(", "),
            "refined_parameters": refined_params,
            "applied_changes": changes,
            "stage_description": stage["description"],
            "iteration_used": iteration
        }

if __name__ == "__main__":
    assistant = AITextAssistant()   # هنا داخلياً بيستخدم builder + checker + enricher + manager + refiner

    test_cases = [
        "صاروخ مع محركات plasma engines مائل 15 درجة",
        "مركبة فضائية متعددة المراحل مع درع حراري",
        "صاروخ عادي بدون تفاصيل خاصة",
    ]

    print("=" * 80)
    print("اختبار النظام الكامل لتوليد وصف الصورة\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n=== اختبار {i}: {text} ===\n")
        
        # المسار الكامل داخل supervise_and_generate
        result = assistant.supervise_and_generate(
            enhanced_text=text,
            max_detail_level="high",
            iteration=2,               # مثلاً نبدأ من المحاولة الثانية
            custom_ar="--ar 2:3"
        )
        
        print("النص الأصلي          :", text)
        print("الـ Prompt النهائي    :")
        print(result["prompt"])
        print("\nNegative Prompt       :")
        print(result["negative_prompt"])
        print("\nParameters            :", result.get("parameters", {}))
        print("\nIssues / تناقضات      :", result["issues"])
        print("Found elements        :", result["found_elements"])
        print("Supervision summary   :")
        print(result["supervision_summary"])
        print("-" * 80)
