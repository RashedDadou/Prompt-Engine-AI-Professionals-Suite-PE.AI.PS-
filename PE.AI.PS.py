import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from io import BytesIO
import requests
import threading
from datetime import datetime
import sqlite3
import re
import shutil
from datetime import datetime
from typing import Dict, Any, List
import base64
import random  # للعناصر الديناميكية في fallback
import numpy as np  # للـ gradients في fallback

# ====================== Knowledge Library ======================
class KnowledgeLibrary:
    def __init__(self):
        # ده اللي هيخلي كل thread عنده متغيراته الخاصة
        self.local = threading.local()

    # دالة جديدة عشان نجيب الـ connection والـ cursor الخاص بالـ thread الحالي
    def get_connection(self):
        # لو الـ thread ده أول مرة يستخدم الـ database
        if not hasattr(self.local, "conn"):
            # نفتح connection جديد خاص بيه
            self.local.conn = sqlite3.connect('stellar_knowledge.db', check_same_thread=False)
            self.local.cursor = self.local.conn.cursor()
            
            # نعمل الجداول لو مش موجودة (مهم جدًا نعمل ده هنا مش في __init__)
            self._create_tables()
            
            # نضيف الـ defaults والـ style biases الأولية
            self._setup_defaults()

        return self.local.conn, self.local.cursor

    # دالة داخلية عشان تعمل الجداول
    def _create_tables(self):
        conn, cursor = self.get_connection()
        cursor.execute('''CREATE TABLE IF NOT EXISTS knowledge 
                          (category TEXT, subcategory TEXT, key TEXT, value TEXT, 
                           PRIMARY KEY(category, subcategory, key))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rl_policy 
                          (key TEXT PRIMARY KEY, value REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS style_bias 
                          (style TEXT PRIMARY KEY, score REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS favorites 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, prompt TEXT, timestamp TEXT)''')
        conn.commit()

    # دالة داخلية عشان تضيف الـ defaults الأولية
    def _setup_defaults(self):
        conn, cursor = self.get_connection()

        # Defaults للـ knowledge
        self.set_default("spacecraft", "engines", "thrust", "10.0")
        self.set_default("spacecraft", "engines", "angle", "15.0")
        self.set_default("spacecraft", "engines", "type", "plasma")
        self.set_default("spacecraft", "shields", "material", "titanium-alloy")

        # Defaults للـ rl_policy
        self.set_rl_default("preferred_thrust", 10.0)
        self.set_rl_default("preferred_angle", 15.0)

        # Style biases الأولية
        styles = ["cyberpunk", "retro_scifi", "nasa_realistic", "cinematic_epic"]
        for s in styles:
            if self.query_style(s) is None:
                self.update_style(s, 0.0)

    # =============================================================================
    # كل الدوال الباقية لازم نعدلها عشان تستخدم get_connection() بدل self.conn
    # =============================================================================

    def set_default(self, category, subcategory, key, value):
        if self.query(category, subcategory, key) is None:
            self.update(category, subcategory, key, value)

    def set_rl_default(self, key, value):
        if self.query_rl(key) is None:
            self.update_rl(key, value)

    def update(self, category, subcategory, key, value):
        conn, cursor = self.get_connection()
        cursor.execute('''INSERT OR REPLACE INTO knowledge VALUES (?, ?, ?, ?)''',
                       (category, subcategory, key, str(value)))
        conn.commit()

    def query(self, category, subcategory, key):
        conn, cursor = self.get_connection()
        cursor.execute('''SELECT value FROM knowledge WHERE category=? AND subcategory=? AND key=?''',
                       (category, subcategory, key))
        result = cursor.fetchone()
        return result[0] if result else None

    def update_rl(self, key, value):
        conn, cursor = self.get_connection()
        cursor.execute('''INSERT OR REPLACE INTO rl_policy (key, value) VALUES (?, ?)''', (key, value))
        conn.commit()

    def query_rl(self, key):
        conn, cursor = self.get_connection()
        cursor.execute('''SELECT value FROM rl_policy WHERE key=?''', (key,))
        result = cursor.fetchone()
        return float(result[0]) if result else None

    def update_style(self, style, score):
        conn, cursor = self.get_connection()
        cursor.execute('''INSERT OR REPLACE INTO style_bias (style, score) VALUES (?, ?)''', (style, score))
        conn.commit()

    def query_style(self, style):
        conn, cursor = self.get_connection()
        cursor.execute('''SELECT score FROM style_bias WHERE style=?''', (style,))
        result = cursor.fetchone()
        return float(result[0]) if result else None

    def get_preferred_style(self):
        conn, cursor = self.get_connection()
        cursor.execute('''SELECT style FROM style_bias ORDER BY score DESC LIMIT 1''')
        result = cursor.fetchone()
        return result[0] if result else "cinematic_epic"

    def add_favorite(self, path, prompt):
        conn, cursor = self.get_connection()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO favorites (path, prompt, timestamp) VALUES (?, ?, ?)''', (path, prompt, timestamp))
        conn.commit()
        
        import os
        import shutil
        os.makedirs("favorites", exist_ok=True)
        fav_path = os.path.join("favorites", os.path.basename(path))
        shutil.copy(path, fav_path)

    def get_favorites(self):
        conn, cursor = self.get_connection()
        cursor.execute('''SELECT path, prompt, timestamp FROM favorites ORDER BY timestamp DESC''')
        return cursor.fetchall()
        
# ====================== AI Text Assistant ======================
class AITextAssistant:
    """مساعد نصي ذكي يحسن الـ prompt بناءً على الذاكرة، المعرفة، وسياسة RLHF"""
    def __init__(self):
        self.patterns = {
            "engines": r"\b(engine|thruster|propulsion|baluna|jet)\b",
            "angle": r"\b(angle|tilt|alignment|direction|orientation)\b",
            "thrust": r"\b(thrust|power|force|meganewtons?)\b",
            "shields": r"\b(shield|armor|protection|defense)\b",
            "length": r"\b(\d+)\s*meter\b",  # \b عشان ما يمسكش كلام زيادة
            "distribution": r"\b(distribution|symmetric|cluster|layout)\b",
            "colors": r"\b(color|hue|tone|palette|red|blue|green|neon)\b",  # جديد للتحسين
            "materials": r"\b(material|alloy|metal|composite|carbon)\b"  # جديد
        }

    def analyze_text(self, text: str, memory: List[str], knowledge_lib: KnowledgeLibrary) -> str:
        improved = text.strip()
        
        # 1. استبدال مصطلحات قديمة
        improved = re.sub(r"\bbaluna\b", "plasma", improved, flags=re.IGNORECASE)
        
        # 2. جلب البيانات الحالية والسياسة
        spacecraft = knowledge_lib.get_knowledge("spacecraft")
        policy = knowledge_lib.get_policy()  # ←←←←←←←←←←←←←←←←← جديد!
        
        preferred_angle = policy.get("preferred_angle", 15.0)
        preferred_thrust = policy.get("preferred_thrust", 10.0)
        style_bias = policy.get("style_bias", "cinematic")

        added_details = []

        # 3. إضافة تفاصيل المحركات بناءً على السياسة (RLHF)
        if re.search(self.patterns["engines"], improved, re.IGNORECASE):
            thrust_val = spacecraft["engines"]["thrust"] if spacecraft else preferred_thrust
            angle_val = spacecraft["engines"]["angle"] if spacecraft else preferred_angle
            eng_type = spacecraft["engines"]["type"] if spacecraft else "plasma"
            
            if f"{thrust_val} meganewtons" not in improved.lower():
                added_details.append(f"main engines delivering {thrust_val:.1f} meganewtons each with variable thrust vectors")
            if f"{angle_val} degrees" not in improved.lower():
                added_details.append(f"auxiliary engines angled at {angle_val:.1f} degrees for hyper-maneuverability in zero-gravity")
            if eng_type not in improved.lower():
                added_details.append(f"powered by next-gen {eng_type} propulsion with quantum efficiency")

        # 4. الدروع مع تحسين
        if re.search(self.patterns["shields"], improved, re.IGNORECASE) and spacecraft:
            shield_mat = spacecraft["shields"]["material"]
            added_details.append(f"equipped with adaptive multi-layered {shield_mat} shielding that regenerates under fire")

        # 5. الطول + تحديث المعرفة مع dimensions متقدمة
        length_match = re.search(self.patterns["length"], improved)
        if length_match:
            length = int(length_match.group(1))
            knowledge_lib.update_knowledge("spacecraft", "dimensions", {"length": length, "width": max(10, length // 2.5), "height": length // 3})
            added_details.append(f"{length}-meter aerodynamic fuselage with modular sections for customization")

        # 6. توزيع المحركات من الذاكرة مع variations
        if any("better engine distribution" in prev.lower() or re.search(self.patterns["distribution"], prev, re.IGNORECASE) for prev in memory[-3:]):
            if "distribution" not in improved.lower():
                added_details.append("engines symmetrically distributed in adaptive triangular clusters for optimal balance, stability, and warp-speed transitions")

        # 7. إضافة colors و materials من regex جديد
        if re.search(self.patterns["colors"], improved, re.IGNORECASE):
            added_details.append("vibrant color palette with dynamic gradients, metallic sheen, and bioluminescent accents")
        if re.search(self.patterns["materials"], improved, re.IGNORECASE):
            added_details.append("constructed from advanced nanocomposites, self-healing alloys, and energy-absorbing metamaterials")

        # 8. إضافة اللمسة الفنية من الـ RL style bias مع variations
        style_phrases = {
            "cinematic": "dramatic volumetric lighting, deep space nebula backdrop, lens flare effects, cinematic depth of field",
            "realistic": "photorealistic materials, accurate physics-based rendering, NASA-style detail, high-fidelity textures",
            "futuristic": "glowing neon accents, holographic interfaces, cyberpunk aesthetic, futuristic particle effects",
            "epic": "massive scale, intense energy trails, epic wide-angle composition, god rays from distant stars"
        }
        style_add = style_phrases.get(style_bias, style_phrases["cinematic"]) + ", generate variations for diversity"
        added_details.append(style_add)

        # 9. إضافة quality boosters نهائية مع upscaling hint
        quality_boosters = "masterpiece, ultra-detailed, 8K resolution, sharp focus, professional rendering, ray-traced shadows, post-process upscaling"
        added_details.append(quality_boosters)

        # جمع الكل مع separator للـ API
        if added_details:
            improved += ", " + ", ".join(added_details)

        return improved

# ====================== AI Image Assistant ======================
class AIImageAssistant:
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.api_url = "https://api.x.ai/v1/images/generations"  # للصور
        self.video_url = "https://api.x.ai/v1/video/generations"  # جديد للـ video في 2025+

        if not self.api_key:
            print("⚠️ XAI_API_KEY not set → Running in FALLBACK mode")
        else:
            print("✅ Real Grok Imagine API activated with 2026 features!")

    def generate_with_grok(self, prompt: str, size: str = "1792x1024", base_image_path: str = None, style_transfer: bool = False) -> dict:
        if not self.api_key:
            return {"status": "fallback", "message": "No API key"}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "model": "grok-imagine-aurora",
            "n": 1,  # يمكن نضيف n=3 لـ multiple generations
            "size": size
        }

        # تحسين هائل: إضافة img2img أو style transfer لو موجود base_image
        if base_image_path:
            with open(base_image_path, "rb") as img_file:
                base_image = base64.b64encode(img_file.read()).decode('utf-8')
            payload["base_image"] = base_image  # افتراضي بناءً على تحديثات 2025 (image editing/style transfer)
            if style_transfer:
                payload["mode"] = "style_transfer"  # جديد للـ style transfer

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=90)
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                img_response = requests.get(image_url, timeout=30)
                img = Image.open(BytesIO(img_response.content))

                # تحسين هائل: auto upscale to 4K
                img = self.auto_upscale(img)

                filename = f"stellar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                img.save(filename)
                return {"status": "success", "path": filename, "url": image_url, "prompt": prompt}
            else:
                return {"status": "error", "message": f"API Error: {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_video(self, image_path: str, prompt: str) -> dict:
        # تحسين هائل جديد: image-to-video (6-15 ثانية)
        if not self.api_key:
            return {"status": "fallback", "message": "No API key"}

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with open(image_path, "rb") as img_file:
            base_image = base64.b64encode(img_file.read()).decode('utf-8')
        payload = {
            "base_image": base_image,
            "prompt": prompt + ", animate smoothly for 10 seconds, dynamic camera movement",
            "model": "grok-imagine-aurora-video",
            "duration": 10  # ثواني
        }

        try:
            response = requests.post(self.video_url, json=payload, headers=headers, timeout=120)
            if response.status_code == 200:
                data = response.json()
                video_url = data["data"][0]["url"]
                vid_response = requests.get(video_url, timeout=60)
                filename = f"stellar_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(filename, "wb") as f:
                    f.write(vid_response.content)
                return {"status": "success", "path": filename, "url": video_url, "prompt": prompt}
            else:
                return {"status": "error", "message": f"API Error: {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def fallback_drawing(self, prompt: str):
        print("🎨 Falling back to manual drawing...")
        img = Image.new('RGB', (1024, 1024), color='#000011')
        draw = ImageDraw.Draw(img)
        draw.ellipse((200, 300, 824, 724), outline='#00ffff', width=20)
        draw.rectangle((400, 200, 624, 300), fill='#0066ff')
        draw.polygon([(512, 100), (462, 300), (562, 300)], fill='#ff00ff')
        draw.ellipse((300, 700, 400, 800), fill='#ff6600')
        draw.ellipse((624, 700, 724, 800), fill='#ff6600')

        filename = f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(filename)
        return {"status": "fallback", "path": filename, "prompt": prompt}

    def enhanced_fallback(self, prompt: str, base_image_path=None):
        print("🎨 رسم احتياطي محسن دلع هائل...")
        width, height = 2048, 2048  # تحسين: حجم أكبر للجودة
        img = Image.new('RGBA', (width, height), color=(10, 0, 31, 255))  # خلفية شفافة مع gradient
        draw = ImageDraw.Draw(img, 'RGBA')

        # تحسين هائل: gradient خلفية nebula بـ numpy
        gradient = np.linspace((32, 0, 64), (0, 0, 32), height, dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                img.putpixel((x, y), (gradient[y][0], gradient[y][1], gradient[y][2], 255))

        # نجوم ديناميكية مع sparkle
        for _ in range(500):  # أكتر نجوم
            x, y = random.randint(0, width), random.randint(0, height)
            size = random.randint(1, 3)
            draw.ellipse((x-size, y-size, x+size, y+size), fill=(255, 255, 255, random.randint(128, 255)))

        # كواكب جديدة
        draw.ellipse((100, 100, 300, 300), fill=(128, 0, 255, 200), outline='#ff00ff', width=20)
        draw.ellipse((1500, 500, 1800, 800), fill=(0, 255, 128, 150), outline='#00ffff', width=15)

        # سفينة متقدمة مع تفاصيل بناءً على prompt
        if "cyberpunk" in prompt.lower():
            draw.rectangle((600, 400, 1400, 1600), fill=(51, 0, 102, 255), outline='#bb86fc', width=30)
            draw.polygon([(1000, 300), (600, 400), (1400, 400)], fill='#6600cc')
            # neon accents
            for i in range(10):
                draw.line((600 + i*80, 400, 600 + i*80, 1600), fill='#ff00ff', width=5)
        else:
            draw.rectangle((600, 400, 1400, 1600), fill='#330066', outline='#bb86fc', width=30)
            draw.polygon([(1000, 300), (600, 400), (1400, 400)], fill='#6600cc')

        draw.ellipse((900, 1400, 1100, 1800), fill='#00ffff', outline='#ffffff', width=10)  # درع متوهج مع glow
        img = img.filter(ImageFilter.GaussianBlur(2))  # glow effect

        # محركات لهب ديناميكي مع flames
        colors = ['#00ffaa', '#ff6600', '#ff00ff'] if "epic" in prompt.lower() else ['#ff6600']
        for col in colors:
            draw.ellipse((500, 1700, 700, 2000), fill=col)
            draw.ellipse((1300, 1700, 1500, 2000), fill=col)
            for i in range(8):
                draw.ellipse((520 + i*20, 1800, 680 + i*20, 2000), fill=col, outline='#ffffff', width=2)

        # auto upscale داخلي
        img = self.auto_upscale(img.resize((1024, 1024), Image.Resampling.LANCZOS))

        filename = f"enhanced_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(filename)
        return {"status": "fallback", "path": filename, "prompt": prompt}

    def auto_upscale(self, img: Image) -> Image:
        # تحسين هائل: upscale to 4K مع sharpen
        new_size = (img.width * 2, img.height * 2)
        img = img.resize(new_size, Image.Resampling.BICUBIC)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)  # sharpen
        return img

    def quality_check(self, img_path: str) -> int:
        # تحسين: check sharpness آلي
        img = Image.open(img_path).convert('L')
        array = np.asarray(img)
        gx, gy = np.gradient(array)
        gnorm = np.sqrt(gx**2 + gy**2)
        sharpness = np.average(gnorm)
        return min(int(sharpness * 10), 100)  # score 0-100

# ====================== Main Supervisor ======================
class StellarDesigner:
    def __init__(self):
        self.knowledge = KnowledgeLibrary()
        self.image_assistant = AIImageAssistant()
        self.last_style_used = None

    def enhance_prompt(self, user_input: str, selected_style: str = None) -> str:
        prompt = user_input.strip()
        enhancements = []

        # RL values
        thrust = self.knowledge.query_rl("preferred_thrust") or 10.0
        angle = self.knowledge.query_rl("preferred_angle") or 15.0

        if re.search(r"\b(engine|thruster|propulsion)\b", prompt, re.IGNORECASE):
            enhancements.append(f"main engines delivering {thrust:.1f} meganewtons with adaptive thrust modulation")
            enhancements.append(f"auxiliary engines angled at {angle:.1f} degrees for quantum leap maneuvers")
            enhancements.append("advanced plasma propulsion with energy recycling")

        if "shield" in prompt.lower():
            mat = self.knowledge.query("spacecraft", "shields", "material") or "titanium-alloy"
            enhancements.append(f"multi-layered {mat} shields with phase-shifting technology")

        # Style bias مع تحسين هائل: إضافة variations
        if selected_style:
            style_prompt = {
                "cyberpunk": "cyberpunk aesthetic, neon lights, rainy streets reflection, high tech low life, blade runner vibes, generate 3 variations",
                "retro_scifi": "retro sci-fi 1950s style, chrome details, ray guns, atomic age design, pulp magazine cover, vintage filter variations",
                "nasa_realistic": "realistic NASA concept art, photorealistic, accurate engineering, white and orange colors, technical blueprint style, high-res variants",
                "cinematic_epic": "epic cinematic composition, dramatic volumetric lighting, deep space nebula, lens flare, interstellar movie style, epic scale variations"
            }.get(selected_style, "")
            if style_prompt:
                enhancements.append(style_prompt)
            self.last_style_used = selected_style
        else:
            preferred = self.knowledge.get_preferred_style()
            if preferred != "cinematic_epic":
                enhancements.append({
                    "cyberpunk": "cyberpunk neon atmosphere with dynamic lighting variations",
                    "retro_scifi": "retro sci-fi chrome aesthetic with color scheme options",
                    "nasa_realistic": "photorealistic NASA engineering style with detail levels",
                    "cinematic_epic": "epic cinematic lighting with composition variants"
                }[preferred])
            self.last_style_used = preferred

        # Quality مع تحسين للـ video hint
        enhancements += [
            "masterpiece, ultra detailed, 8K, sharp focus, professional rendering, dramatic lighting, ready for video animation"
        ]

        if enhancements:
            prompt += ", " + ", ".join(enhancements)

        return prompt

    def learn_from_rating(self, rating: int):
        if self.last_style_used is None:
            return

        boost = -1.0 if rating < 50 else (0.0 if rating < 80 else 1.5)

        old_score = self.knowledge.query_style(self.last_style_used) or 0.0
        new_score = old_score + boost
        self.knowledge.update_style(self.last_style_used, new_score)

        # Also update thrust/angle as before
        if rating < 50:
            thrust_boost = -0.5
            angle_boost = -0.5
        elif rating < 80:
            thrust_boost = 0.0
            angle_boost = 0.0
        else:
            thrust_boost = 0.7
            angle_boost = 0.7

        old_thrust = self.knowledge.query_rl("preferred_thrust") or 10.0
        new_thrust = max(5, min(20, old_thrust + thrust_boost * 0.5))
        self.knowledge.update_rl("preferred_thrust", new_thrust)

        old_angle = self.knowledge.query_rl("preferred_angle") or 15.0
        new_angle = max(5, min(45, old_angle + angle_boost))
        self.knowledge.update_rl("preferred_angle", new_angle)

        print(f"🧠 RLHF Update | Style: {self.last_style_used} → {new_score:.1f} | Thrust: {new_thrust:.1f}MN | Angle: {new_angle:.1f}°")

# ====================== GUI ======================
class StellarDesignerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌌 Stellar Designer Pro v9.0 - تحسينات هائلة في التوليد 💜🐥")
        self.root.geometry("1600x1200")
        self.root.configure(bg="#0f0020")

        self.designer = StellarDesigner()
        self.last_result = None
        self.current_photo = None
        self.selected_size = tk.StringVar(value="1792x1024")

        self.setup_ui()

    def setup_ui(self):
        # ثيم دلع بنفسجي ووردي ناعم 💕
        style = ttk.Style()
        style.theme_use('clam')  # عشان نتحكم في الألوان أحسن
        style.configure("TButton", font=("Arial", 12, "bold"), padding=10)
        style.map("TButton",
                  background=[("active", "#bb86fc"), ("disabled", "#555555")],
                  foreground=[("disabled", "#aaaaaa")])
        style.configure("TCombobox", font=("Arial", 12))

        top = tk.Frame(self.root, bg="#0f0020")
        top.pack(fill="x", padx=30, pady=30)

        # العنوان الدلوع
        tk.Label(top, text="اكتب وصفك يا قمري ✨💕", font=("Arial", 20, "bold"), 
                 fg="#ff99ff", bg="#0f0020").pack(anchor="w", pady=(0, 10))

        # مربع الوصف
        self.entry = scrolledtext.ScrolledText(top, height=8, font=("Arial", 13), 
                                               bg="#200040", fg="#ffffff", 
                                               insertbackground="#ff99ff", 
                                               relief="flat", bd=5)
        self.entry.pack(fill="x", pady=15)

        # إطار الأنماط الجاهزة
        style_frame = tk.LabelFrame(top, text="🚀 الأنماط الجاهزة 🚀", 
                                    font=("Arial", 14, "bold"), fg="#03dac6", 
                                    bg="#0f0020", labelanchor="n")
        style_frame.pack(fill="x", pady=15)

        styles = [
            ("Cyberpunk 💜", "cyberpunk"),
            ("Retro Sci-Fi 🛸", "retro_scifi"),
            ("NASA Realistic 🛰️", "nasa_realistic"),
            ("Cinematic Epic 🌟", "cinematic_epic"),
            ("🗑️ مسح الوصف", "clear")
        ]

        for text, style_key in styles:
            color = "#d32f2f" if style_key == "clear" else "#6200ea"
            btn = tk.Button(style_frame, text=text, font=("Arial", 12, "bold"),
                            bg=color, fg="white", relief="raised", bd=4,
                            command=lambda s=style_key: self.apply_style(s))
            btn.pack(side="left", padx=8, pady=5)

        # التحكم الرئيسي
        controls = tk.Frame(top, bg="#0f0020")
        controls.pack(fill="x", pady=20)

        # اختيار الحجم
        tk.Label(controls, text="حجم الصورة:", fg="#ffaa00", bg="#0f0020", 
                 font=("Arial", 13, "bold")).pack(side="left", padx=(0, 10))
        size_menu = ttk.Combobox(controls, textvariable=self.selected_size, 
                                 values=[
                                     "1792x1024 (Landscape)",
                                     "1024x1024 (Square)", 
                                     "1024x1792 (Portrait)"
                                 ], state="readonly", width=25)
        size_menu.pack(side="left", padx=10)

        # زر التوليد الكبير الدلوع
        self.generate_btn = tk.Button(controls, text="🚀 توليد بالـ Grok Imagine 🚀", 
                                      font=("Arial", 16, "bold"),
                                      bg="#00c853", fg="white", relief="raised", bd=6,
                                      command=self.start_generation)
        self.generate_btn.pack(side="left", padx=30)

        # التقييم
        tk.Label(controls, text="تقييم التصميم السابق:", fg="#03dac6", bg="#0f0020", 
                 font=("Arial", 13, "bold")).pack(side="left", padx=(40, 10))
        self.rating = ttk.Scale(controls, from_=0, to=100, orient="horizontal", length=350)
        self.rating.set(85)
        self.rating.pack(side="left", padx=10)

        self.rating_label = tk.Label(controls, text="85", fg="#ff99ff", bg="#0f0020", 
                                     font=("Arial", 14, "bold"))
        self.rating_label.pack(side="left", padx=5)
        self.rating.config(command=lambda v: self.rating_label.config(text=f"{int(float(v))}"))

        # الأزرار الإضافية (مفضلة وتعديل مع video جديد)
        extra_controls = tk.Frame(top, bg="#0f0020")
        extra_controls.pack(fill="x", pady=20)

        self.fav_btn = tk.Button(extra_controls, text="❤️ أضف للمفضلة ❤️", 
                                 font=("Arial", 14, "bold"),
                                 bg="#ff3399", fg="white", relief="raised", bd=5,
                                 command=self.add_to_favorites, state="disabled")
        self.fav_btn.pack(side="left", padx=20)

        self.edit_btn = tk.Button(extra_controls, text="✏️ تعديل الصورة السابقة (img2img) ✏️", 
                                  font=("Arial", 14, "bold"),
                                  bg="#9966ff", fg="white", relief="raised", bd=5,
                                  command=self.manual_edit_img2img, state="disabled")
        self.edit_btn.pack(side="left", padx=20)

        self.video_btn = tk.Button(extra_controls, text="🎥 توليد فيديو من الصورة 🎥", 
                                   font=("Arial", 14, "bold"),
                                   bg="#ff6600", fg="white", relief="raised", bd=5,
                                   command=self.generate_video_from_image, state="disabled")
        self.video_btn.pack(side="left", padx=20)

        # عرض الصورة
        self.img_label = tk.Label(self.root, text="الصورة هتظهر هنا بعد التوليد... يا قمري ✨💜", 
                                  fg="#8888ff", bg="#0f0020", font=("Arial", 18))
        self.img_label.pack(expand=True, fill="both", padx=30, pady=20)

        # شريط الحالة السفلي
        self.status = tk.Label(self.root, text="جاهز للإقلاع يا كتكوتي 🐥🚀💕", 
                               fg="#00ffaa", bg="#1a0033", font=("Arial", 13, "bold"),
                               relief="sunken", bd=4, pady=10)
        self.status.pack(side="bottom", fill="x")
        
    def add_to_favorites(self):
        if self.last_result:
            path = self.last_result["path"]
            prompt = self.last_result["prompt"]
            self.designer.knowledge.add_favorite(path, prompt)
            messagebox.showinfo("💜", "تم إضافة الصورة للمفضلة يا كتكوتي! 🐥")

    def manual_edit_img2img(self):
        if self.last_result and os.path.exists(self.last_result["path"]):
            new_prompt = self.entry.get("1.0", tk.END).strip() or self.last_result["prompt"]
            result = self.designer.image_assistant.generate_with_grok(new_prompt, base_image_path=self.last_result["path"], style_transfer=True)
            if result["status"] != "success":
                result = self.designer.image_assistant.enhanced_fallback(new_prompt, self.last_result["path"])
            self.last_result = result
            self.display_image(result["path"])
            quality = self.designer.image_assistant.quality_check(result["path"])
            self.status.config(text=f"تم التعديل! جودة: {quality}/100 💜")
            self.fav_btn.config(state="normal")
            self.edit_btn.config(state="normal")
            self.video_btn.config(state="normal")

    def generate_video_from_image(self):
        if self.last_result and os.path.exists(self.last_result["path"]):
            prompt = self.entry.get("1.0", tk.END).strip() or self.last_result["prompt"]
            result = self.designer.image_assistant.generate_video(self.last_result["path"], prompt)
            if result["status"] == "success":
                messagebox.showinfo("🎥", f"تم توليد الفيديو! محفوظ في: {result['path']}")
            else:
                messagebox.showerror("خطأ", result["message"])

    def apply_style(self, style):
        if style == "clear":
            self.entry.delete("1.0", tk.END)
            return
        style_text = {
            "cyberpunk": "futuristic cyberpunk spacecraft flying over neon city at night, rain reflections",
            "retro_scifi": "1950s retro sci-fi rocket ship with chrome fins and atomic details",
            "nasa_realistic": "highly detailed realistic NASA spacecraft concept, white hull with orange accents, solar panels",
            "cinematic_epic": "epic cinematic interstellar cruiser emerging from nebula, dramatic lighting"
        }[style]
        self.entry.delete("1.0", tk.END)
        self.entry.insert("1.0", style_text)

    def start_generation(self):
        prompt = self.entry.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("تحذير", "اكتب وصف أولاً يا كتكوتي 🥺")
            return

        selected_size = self.selected_size.get().split()[0]

        self.generate_btn.config(state="disabled")
        self.status.config(text="جاري تحسين الوصف وتوليد الصورة... ⏳✨")

        threading.Thread(target=self.generate_thread, args=(prompt, selected_size), daemon=True).start()

    def generate_thread(self, user_prompt, size):
        try:
            # Learn from previous
            if self.last_result:
                rating = int(self.rating.get())
                self.designer.learn_from_rating(rating)

            # Enhance
            enhanced = self.designer.enhance_prompt(user_prompt)

            # Generate مع تحسين: لو في last_result، استخدم img2img
            base_path = self.last_result["path"] if self.last_result else None
            result = self.designer.image_assistant.generate_with_grok(enhanced, size, base_image_path=base_path)
            if result["status"] != "success":
                self.root.after(0, self.status.config, {"text": "فشل الـ API → رسم يدوي احتياطي...", "fg": "orange"})
                result = self.designer.image_assistant.enhanced_fallback(enhanced)

            self.last_result = result
            self.root.after(0, self.display_image, result["path"])
            quality = self.designer.image_assistant.quality_check(result["path"])
            msg = f"تم بنجاح! 💜 محفوظة: {result['path']} | جودة: {quality}/100"
            if result.get("url"):
                msg += f" | رابط: {result['url']}"
            self.root.after(0, self.status.config, {"text": msg, "fg": "#00ffaa"})

            # تفعيل الأزرار
            self.root.after(0, self.fav_btn.config, {"state": "normal"})
            self.root.after(0, self.edit_btn.config, {"state": "normal"})
            self.root.after(0, self.video_btn.config, {"state": "normal"})

        except Exception as e:
            self.root.after(0, self.status.config, {"text": f"خطأ: {str(e)}", "fg": "red"})
        finally:
            self.root.after(0, self.generate_btn.config, {"state": "normal"})
                        
    def display_image(self, path):
        if not os.path.exists(path):
            self.img_label.config(text="الصورة مش موجودة 😢")
            return
        img = Image.open(path)
        # Resize to fit
        base_width = 1200  # تحسين: عرض أكبر
        w_percent = base_width / float(img.width)
        h_size = int(float(img.height) * float(w_percent))
        img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
        self.current_photo = ImageTk.PhotoImage(img)
        self.img_label.config(image=self.current_photo, text="")

# ================ AI Supervisor ===================
class AISupervisor:
    """المدير التنفيذي - يدير التدفق، التعلم، والتوليد مع RLHF"""
    def __init__(self):
        self.text_assistant = AITextAssistant()
        self.image_assistant = AIImageAssistant()
        self.knowledge_lib = KnowledgeLibrary()
        self.memory: List[Dict] = []
        self.iteration_count = 0  # ←←←←←←←←←←←←←←←←← أضفناه

    def process_request_with_rl(self, user_input: str, user_score: int = None) -> Dict[str, Any]:
        self.iteration_count += 1
        print(f"\n{'='*70}")
        print(f"REQUEST #{self.iteration_count} + RLHF CYCLE")
        print(f"{'='*70}")
        
        # 1. تطبيق التقييم السابق (RLHF)
        if user_score is not None and self.memory:
            last_prompt = self.memory[-1].get("final_prompt", user_input)
            self.knowledge_lib.update_from_feedback(user_score, last_prompt)
        
        # 2. تحسين الـ prompt
        enhanced = self.text_assistant.analyze_text(
            user_input,
            [m["input"] for m in self.memory[-5:]],  # آخر 5 طلبات
            self.knowledge_lib
        )
        
        # 3. إضافة لمسات نهائية من الـ RL policy
        policy = self.knowledge_lib.get_policy()
        style = policy.get("style_bias", "cinematic")
        enhanced += f", {style} masterpiece, dramatic volumetric lighting, deep space nebula, ultra sharp, 8K resolution, professional render"
        
        print(f"FINAL OPTIMIZED PROMPT:\n{enhanced}\n")
        
        # 4. توليد الصورة الحقيقية
        result = self.image_assistant.generate_image_real(enhanced)  # ←←←←←←←←←←←←←←←←← صح: enhanced مش enhanced_prompt
        
        # 5. تقييم الجودة الآلي (اختياري للـ logging)
        auto_quality = self.evaluate_quality(result, enhanced)
        print(f"AUTO QUALITY SCORE: {auto_quality}/100")
        
        # 6. حفظ في الذاكرة
        self.memory.append({
            "iteration": self.iteration_count,
            "input": user_input,
            "final_prompt": enhanced,
            "result": result,
            "auto_quality": auto_quality,
            "timestamp": datetime.now().isoformat()
        })
        
        # 7. رسائل للمستخدم
        if result["status"] == "success":
            print(f"🚀 SUCCESS! Spacecraft design generated:")
            print(f"   File: {result['image_path']}")
            if result.get("url"):
                print(f"   URL: {result['url']}")
            print("\nRate this design (0-100) to make me smarter next time:")
            print("   (Higher score = I learn to keep this style, lower = I adjust)")
        else:
            print(f"❌ Generation failed: {result.get('message', 'Unknown error')}")
        
        return result

    def evaluate_quality(self, result: Dict, prompt: str) -> int:
        """تقييم آلي للنتيجة"""
        score = 50
        
        if result["status"] == "success":
            score += 40
        
        policy = self.knowledge_lib.get_policy()
        if f"{policy['preferred_angle']:.1f} degrees" in prompt.lower():
            score += 15
        if f"{policy['preferred_thrust']:.1f} meganewtons" in prompt.lower():
            score += 15
        if "plasma" in prompt.lower():
            score += 10
        if "titanium" in prompt.lower():
            score += 10
            
        return min(score, 100)

    def show_memory_summary(self):
        print("\nMEMORY SUMMARY:")
        for i, entry in enumerate(self.memory[-5:], 1):
            print(f"{i}. [{entry['timestamp'][:19]}] Score: {entry.get('auto_quality', 'N/A')} | Input: {entry['input'][:50]}...")
            
if __name__ == "__main__":
    root = tk.Tk()
    app = StellarDesignerGUI(root)
    root.mainloop()