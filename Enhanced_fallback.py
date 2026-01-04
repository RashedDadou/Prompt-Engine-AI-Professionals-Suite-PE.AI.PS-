# enhanced_fallback.py
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def generate_enhanced_fallback(prompt: str, resolution=(1920, 1080), export="both"):
    """
    export: "image", "video", or "both"
    """
    print(f"🎨 توليد fallback محسن دلع يا كتكوتي - {resolution} - {export}")

    width, height = resolution
    frames = []
    asteroid_x = 100
    light_phase = 0

    font_path = None  # لو عايز خط عربي، حط مسار TTF هنا
    try:
        font = ImageFont.truetype("arial.ttf", 60) if not font_path else ImageFont.truetype(font_path, 60)
    except:
        font = ImageFont.load_default()

    for frame_num in range(120):  # 5 ثواني @ 24 fps
        # خلفية فضائية غامقة
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (10, 0, 30)  # بنفسجي غامق

        # نجوم عشوائية
        for _ in range(200):
            x, y = np.random.randint(0, width), np.random.randint(0, height)
            brightness = np.random.randint(100, 255)
            cv2.circle(img, (x, y), 1, (brightness, brightness, brightness), -1)

        # كوكب في الخلفية (زي المريخ)
        cv2.circle(img, (width - 400, height - 300), 200, (50, 80, 180), -1)
        cv2.circle(img, (width - 420, height - 320), 200, (30, 50, 120), 20)

        # المركبة الفضائية (جسم بيضاوي + محركات)
        center_x, center_y = width // 3, height // 2
        cv2.ellipse(img, (center_x, center_y), (400, 200), 0, 0, 360, (100, 100, 255), 30)

        # نافذة القائد
        cv2.rectangle(img, (center_x + 200, center_y - 100), (center_x + 350, center_y + 50), (200, 200, 200), -1)
        cv2.circle(img, (center_x + 280, center_y - 25), 40, (255, 255, 255), -1)  # راس القائد

        # محركات بلازما متوهجة
        glow_color = (255, 100, 0) if frame_num % 10 < 5 else (100, 200, 255)
        cv2.ellipse(img, (center_x - 350, center_y - 80), (80, 150), -15, 0, 360, glow_color, -1)
        cv2.ellipse(img, (center_x - 350, center_y + 80), (80, 150), 15, 0, 360, glow_color, -1)

        # كويكب يتحرك
        asteroid_x += 12
        if asteroid_x > width + 200:
            asteroid_x = -200
        cv2.circle(img, (asteroid_x, height // 4), 80, (100, 100, 100), -1)
        # ذيل غبار
        cv2.line(img, (asteroid_x - 100, height // 4), (asteroid_x - 300, height // 4 + 50), (150, 120, 80), 20)

        # إضاءة ديناميكية (lens flare بسيط)
        light_phase += 0.1
        flare_x = int(center_x - 350 + 50 * np.sin(light_phase))
        cv2.circle(img, (flare_x, center_y), 60, (255, 200, 100), -1)

        frames.append(img.copy())

    # تصدير
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export in ["image", "both"]:
        cv2.imwrite(f"enhanced_fallback_{timestamp}.png", frames[0])
        print(f"🖼️ صورة محسنة: enhanced_fallback_{timestamp}.png")

    if export in ["video", "both"]:
        out = cv2.VideoWriter(f"enhanced_fallback_{timestamp}.mp4", 
                              cv2.VideoWriter_fourcc(*'mp4v'), 24, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"🎬 فيديو متحرك: enhanced_fallback_{timestamp}.mp4")

    return {
        "image": f"enhanced_fallback_{timestamp}.png" if export in ["image", "both"] else None,
        "video": f"enhanced_fallback_{timestamp}.mp4" if export in ["video", "both"] else None,
        "prompt": prompt
    }