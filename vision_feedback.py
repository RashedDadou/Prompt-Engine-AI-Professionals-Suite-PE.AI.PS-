# vision_feedback.py

import os
import requests
import json
from typing import Dict, Optional, Tuple

class VisionFeedbackLoop:
    """
    حلقة تغذية راجعة بصرية تعتمد على نموذج رؤية خارجي (API)
    """

    def __init__(self, api_provider: str = "openai", api_key: Optional[str] = None):
        self.provider = api_provider.lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")  # أو ANTHROPIC_API_KEY أو GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError(f"API key مطلوب لـ {self.provider}")

        self.system_prompt = """
أنت ناقد بصري محترف متخصص في توليد الصور العلمية والفضائية.
مهمتك:
1. قارن بين الوصف الأصلي (prompt) والصورة الناتجة.
2. حدد التناقضات، النقص، الأخطاء البصرية، عدم الدقة الفيزيائية/الهندسية.
3. اقترح تعديلات دقيقة على الـ prompt و negative prompt لتحسين النتيجة في الجولة التالية.
4. أعطِ درجة رضا من 10.
5. رد بتنسيق JSON فقط.
"""

    def _call_openai_vision(self, prompt: str, image_url: str) -> Dict:
        """مثال باستخدام GPT-4o / o1"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"الوصف الأصلي:\n{prompt}\n\nقم بتقييم الصورة التالية:"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 1200,
            "temperature": 0.4
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except:
            return {"error": content}

    # يمكن إضافة دوال لـ Claude أو Gemini بنفس الطريقة

    def evaluate_and_suggest(
        self,
        original_prompt: str,
        generated_image_url: str,
        current_negative: str = ""
    ) -> Tuple[Dict, str, str]:
        """
        الدالة الرئيسية:
        ترجع (تقرير JSON, prompt_محسن, negative_محسن)
        """
        if self.provider == "openai":
            feedback = self._call_openai_vision(original_prompt, generated_image_url)
        else:
            raise NotImplementedError(f"Provider {self.provider} غير مدعوم بعد")

        if "error" in feedback:
            return feedback, original_prompt, current_negative

        # استخراج التعديلات (افتراض تنسيق JSON من النموذج)
        new_prompt = feedback.get("new_prompt", original_prompt)
        new_negative = feedback.get("new_negative", current_negative)
        score = feedback.get("score", 5)

        return feedback, new_prompt, new_negative


# مثال استخدام في النظام:
# feedback_loop = VisionFeedbackLoop(api_provider="openai")
# report, new_prompt, new_neg = feedback_loop.evaluate_and_suggest(
#     original_prompt=final_prompt,
#     generated_image_url="https://.../generated.jpg"
# )