# ai_helper.py
# ملف مساعد متخصص في المجالات العلمية والإبداعية
# يساعد AI.Supervisor في إثراء الطلبات وتحسين الـ prompts قبل التوليد

from typing import Dict, List, Optional

class DomainExpert:
    """
    متخصص في مجال معين، يقدم معلومات دقيقة، اقتراحات تحسين، وأسئلة توضيحية.
    """
    def __init__(self, domain_name: str, keywords: List[str], enrich_rules: Dict[str, str]):
        self.domain_name = domain_name
        self.keywords = [kw.lower() for kw in keywords]
        self.enrich_rules = enrich_rules  # كلمة مفتاحية → إضافة وصف/تفاصيل

    def matches(self, text: str) -> bool:
        lower_text = text.lower()
        return any(kw in lower_text for kw in self.keywords)

    def enrich(self, prompt: str) -> Dict[str, any]:
        enriched = prompt
        notes = []
        questions = []

        lower_prompt = prompt.lower()

        # تطبيق قواعد الإثراء التلقائية
        for key, addition in self.enrich_rules.items():
            if key.lower() in lower_prompt:
                if addition not in enriched:
                    enriched += f", {addition}"
                    notes.append(f"تم إضافة تفاصيل متخصصة: {addition}")

        # أسئلة توضيحية حسب المجال
        if self.domain_name == "Space Science":
            if "مائل" in lower_prompt or "tilt" in lower_prompt:
                questions.append("هل تريد ميلًا ديناميكيًا قويًا أم خفيفًا؟ (مثال: منظور منخفض درامي أو جانبي قوي)")
            if "محرك" in lower_prompt or "engine" in lower_prompt:
                questions.append("هل المحركات بلازما، أيونية، أم نووية؟ هل تريد توهجًا مرئيًا؟")

        elif self.domain_name == "Engineering & Vehicles":
            if "سيارة" in lower_prompt or "car" in lower_prompt:
                questions.append("ما الموديل أو السنة؟ هل تريد منظورًا معينًا (جانبي، أمامي، داخلي)؟ هل كلاسيكية أم حديثة؟")

        return {
            "enriched_prompt": enriched.strip(", "),
            "notes": notes,
            "questions": questions,
            "domain": self.domain_name
        }


class AIHelper:
    """
    المساعد المتخصص الذي يختار الخبير المناسب بناءً على الطلب.
    """
    def __init__(self):
        self.experts = [
            # تخصص الفضاء والمركبات الفضائية
            DomainExpert(
                domain_name="Space Science",
                keywords=["صاروخ", "rocket", "مركبة فضائية", "spacecraft", "قمر صناعي", "satellite", "محطة فضائية", "space station", "orbit", "plasma", "ion thruster"],
                enrich_rules={
                    "مائل": "dynamic tilt, strong perspective distortion, cinematic angled view",
                    "plasma": "glowing blue plasma exhaust, ionized gas plume, futuristic thrusters",
                    "محرك": "visible engine nozzles, heat distortion, powerful thrust glow"
                }
            ),

            # تخصص الهندسة والمركبات
            DomainExpert(
                domain_name="Engineering & Vehicles",
                keywords=["سيارة", "car", "camaro", "طائرة", "plane", "سفينة", "ship", "قاطرة", "train", "باص", "bus", "محرك", "engine", "توربو", "turbo"],
                enrich_rules={
                    "camaro": "classic American muscle car, aggressive front fascia, wide stance, chrome accents, muscular body lines",
                    "محرك": "detailed engine bay, chrome valve covers, turbocharger piping, heat-wrapped exhaust"
                }
            ),

            # تخصص الطبيعة والبيئة
            DomainExpert(
                domain_name="Natural World",
                keywords=["شجرة", "tree", "نبات", "plant", "غابة", "forest", "بحر", "ocean", "محيط", "coral", "شعاب مرجانية", "صحراء", "desert"],
                enrich_rules={
                    "شجرة بلوط": "oak tree, broad canopy, textured bark, autumn red-orange leaves, golden hour light through branches",
                    "غابة": "dense forest floor, moss-covered rocks, mist, dappled sunlight, fallen leaves"
                }
            ),

            # تخصص البشر والفنون الإنسانية
            DomainExpert(
                domain_name="Human Anatomy & Arts",
                keywords=["إنسان", "person", "وجه", "face", "رسم بشري", "portrait", "وضعية", "pose", "تعبير", "expression"],
                enrich_rules={
                    "وجه": "detailed facial features, realistic skin texture, subtle rim lighting on cheekbones, expressive eyes",
                    "وضعية": "contrapposto pose, natural weight shift, dynamic gesture"
                }
            ),

            # تخصص التاريخ والثقافة
            DomainExpert(
                domain_name="History & Culture",
                keywords=["تاريخ", "history", "فرعون", "pharaoh", "روماني", "roman", "فايكنج", "viking", "معركة", "battle", "قلعة", "castle"],
                enrich_rules={
                    "روماني": "Roman legionary, lorica segmentata armor, red plume helmet, gladius sword, late afternoon sun"
                }
            ),

            # تخصص الفلسفة والمفاهيم المجردة
            DomainExpert(
                domain_name="Philosophy & Abstract Concepts",
                keywords=["فلسفة", "philosophy", "سيسفوس", "sisyphus", "وجود", "existence", "حرية", "freedom", "عدالة", "justice"],
                enrich_rules={
                    "سيسفوس": "Sisyphean struggle, eternal boulder, desolate rocky landscape, chiaroscuro lighting, symbolic despair"
                }
            ),

            # تخصص الإبداع الفني (رسم، موسيقى، شعر)
            DomainExpert(
                domain_name="Creative Expression",
                keywords=["رسم", "draw", "شعر", "poetry", "موسيقى", "music", "أسلوب", "style", "سريالي", "surreal", "انطباعي", "impressionism"],
                enrich_rules={
                    "سريالي": "in the style of Salvador Dalí, melting clocks, dreamlike landscape, impossible architecture",
                    "انطباعي": "impressionist brush strokes, soft lighting, vibrant colors, plein air atmosphere"
                }
            ),

            DomainExpert(
                "Biology & Life Sciences",
                ["نبات", "شجرة", "حيوان", "خلية", "جين", "DNA", "فيروس", "بكتيريا"],
                {
                    "شجرة بلوط": "Quercus robur, broad deciduous canopy, rough textured bark, acorns, mycorrhizal roots",
                    "غابة مطيرة": "tropical rainforest, dense canopy layer, epiphytes, buttress roots, high humidity mist"
                }
            ),

            DomainExpert(
                "Materials Science",
                ["مادة", "معدن", "سبيكة", "كربون", "تيتانيوم", "سيراميك", "مركب", "composite"],
                {
                    "تيتانيوم": "Ti-6Al-4V alloy, high strength-to-weight ratio, corrosion resistant, aerospace grade",
                    "كربون فايبر": "carbon fiber reinforced polymer, anisotropic strength, lightweight, visible weave pattern"
                }
            ),

            DomainExpert(
                "Philosophy & Critical Thinking",
                ["فلسفة", "وجود", "أخلاق", "حرية", "عدالة", "نسبية", "واقعية", "مثالية"],
                {
                    "سيسفوس": "absurdism, eternal recurrence, futile labor, existential struggle, boulder on incline",
                    "نسبية": "Einsteinian relativity, spacetime curvature, twin paradox visualization"
                }
            ),

            # يمكن إضافة المزيد: تاريخ، اقتصاد، علم نفس، موسيقى، أدب...
        ]

    def consult(self, user_prompt: str) -> Dict[str, any]:
        matched_expert = None
        for expert in self.experts:
            if expert.matches(user_prompt):
                matched_expert = expert
                break

        if matched_expert:
            return matched_expert.enrich(user_prompt)

        # رد عام لو ما لقيناش متخصص
        return {
            "enriched_prompt": user_prompt,
            "priority_keywords": [],
            "forbidden_keywords": [],
            "suggested_category": "general",
            "confidence": 0.5,
            "notes": ["لم يتم التعرف على مجال متخصص واضح"],
            "questions": ["ما المجال الرئيسي للطلب؟ (فضاء، هندسة، طبيعة، إلخ)"],
            "recommended_detail_level": "medium",
            "should_reprocess": False
        }

class SpaceScienceSpecialist(DomainExpert):
    def __init__(self):
        super().__init__(
            "Space Science",
            ["صاروخ", "rocket", "مركبة فضائية", "spacecraft", "قمر صناعي", "محطة فضائية"],
            {
                "محرك": "glowing blue plasma exhaust, visible ionization trail, high-temperature nozzle glow",
                "مائل": "dynamic tilt with strong foreshortening, dramatic low-angle perspective, visible thrust vectoring"
            }
        )
        self.facts = {
            "plasma engine": "electric propulsion using ionized gas, high specific impulse, low thrust but efficient for long missions"
        }

    def enrich(self, prompt):
        result = super().enrich(prompt)
        # إضافة حقائق إذا وُجدت كلمة مفتاحية
        for key, fact in self.facts.items():
            if key in prompt.lower():
                result["notes"].append(f"حقيقة تقنية: {fact}")
        return result
    
# ─── اختبار سريع ────────────────────────────────────────────────────────
if __name__ == "__main__":
    helper = AIHelper()

    test_prompts = [
        "ارسم صاروخ مع محركات بلازما",
        "سيارة Camaro كلاسيكية",
        "غابة خريفية مع أشجار بلوط",
        "وجه إنسان حزين في الظلام",
        "معركة رومانية قديمة",
        "سيسفوس يدحرج الصخرة",
        "رسم سريالي لساعة ذائبة",
    ]

    for p in test_prompts:
        result = helper.consult(p)
        print(f"الطلب: {p}")
        print(f"المجال: {result['domain']}")
        print(f"الـ prompt المحسن: {result['enriched_prompt']}")
        if result["notes"]:
            print("ملاحظات:", "\n".join(result["notes"]))
        if result["questions"]:
            print("أسئلة توضيحية:", "\n".join(result["questions"]))
        print("-" * 80)