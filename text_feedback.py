# text_feedback.py

import json
import os
import time   # ← أضف هذا السطر هنا
from typing import Dict, Tuple, List, Optional

class TextFeedbackLoop:
    """
    حلقة تغذية راجعة نصية فقط (بدون رؤية)
    تحلل الـ prompt قبل التوليد وتقترح تحسينات
    وتحفظ الخبرة للاستفادة لاحقًا
    """

    def __init__(self, history_file: str = "text_feedback_history.json"):
        self.history_file = history_file
        self.history: Dict[str, List[Dict]] = self._load_history()
        self.rules = self._default_rules()

    def _load_history(self) -> Dict:
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def _default_rules(self) -> List[Dict]:
        """قواعد نصية بسيطة للكشف عن مشاكل شائعة"""
        return [
            {
                "name": "تكرار كلمات",
                "check": lambda p: len(p.split()) > 150 or p.count(",") > 40,
                "issue": "الـ prompt طويل جدًا أو فيه فواصل كثيرة → قد يفقد التركيز",
                "fix": "اختصر الوصف، ركز على أهم 3–5 عناصر"
            },
            {
                "name": "غياب كلمات بصرية قوية",
                "check": lambda p: all(word not in p.lower() for word in ["detailed", "intricate", "photorealistic", "sharp", "cinematic", "ultra", "8k", "masterpiece"]),
                "issue": "الـ prompt ناقص كلمات تعزز الجودة البصرية",
                "fix": "أضف: ultra detailed, photorealistic, sharp focus, cinematic lighting"
            },
            {
                "name": "تناقض محتمل",
                "check": lambda p: "realistic" in p.lower() and ("cartoon" in p.lower() or "anime" in p.lower()),
                "issue": "تناقض بين الواقعية والستايل الكرتوني",
                "fix": "احذف كلمات cartoon/anime أو استبدل realistic بـ semi-realistic"
            },
            # أضف قواعد أخرى حسب احتياجك (مثل: غياب negative prompt قوي، إلخ)
        ]

    def analyze_prompt(self, prompt: str, category: str = "general") -> Tuple[bool, str, Dict]:
        """
        تحليل الـ prompt نصيًا
        ترجع: (is_good, report, suggestions)
        """
        issues = []
        suggestions = {"prompt_add": [], "prompt_remove": [], "negative_add": []}

        for rule in self.rules:
            if rule["check"](prompt):
                issues.append(rule["issue"])
                if "fix" in rule:
                    suggestions["prompt_add"].append(rule["fix"])

        # تحقق من التاريخ السابق لنفس الفئة
        if category in self.history and self.history[category]:
            last_good = self.history[category][-1].get("good_prompt", "")
            if last_good and len(prompt) > len(last_good) * 1.5:
                issues.append("الـ prompt أطول بكثير من المحاولات الناجحة السابقة")
                suggestions["prompt_add"].append("اختصر الوصف إلى أهم التفاصيل")

        report = ""
        if issues:
            report = "مشاكل وجدت:\n" + "\n".join(f"- {i}" for i in issues)
        else:
            report = "الـ prompt جيد جدًا من الناحية النصية"

        is_good = len(issues) <= 1  # نسمح بمشكلة واحدة صغيرة

        return is_good, report, suggestions

    def update_history(self, category: str, prompt: str, was_good: bool):
        """حفظ الخبرة"""
        if category not in self.history:
            self.history[category] = []
        self.history[category].append({
            "prompt": prompt,
            "was_good": was_good,
            "timestamp": time.time()
        })
        # نحتفظ بآخر 20 محاولة فقط عشان ما يتضخمش الملف
        self.history[category] = self.history[category][-20:]
        self._save_history()