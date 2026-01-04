# ultimate_fallback_animation.py
import cv2
import numpy as np
from datetime import datetime

def generate_ultimate_spacecraft_scene(
    prompt: str = "combat spacecraft from commander's view",
    resolution=(1920, 1080),
    duration_sec=6,
    fps=24,
    export="both"
):
    width, height = resolution
    total_frames = duration_sec * fps
    frames = []

    # حركة الكويكب والإضاءة
    asteroid_x = -300
    light_phase = 0
    engine_pulse = 0

    print(f"🚀 جاري توليد مشهد فضائي دلع 3D بتقنية واقعية - {resolution}p - {duration_sec} ثواني 💜")

    for frame_num in range(total_frames):
        # خلفية فضاء عميقة
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (5, 0, 25)  # بنفسجي غامق

        # نجوم متلألئة (ثابتة المكان، متغيرة السطوع)
        if frame_num == 0:
            global stars
            stars = [(np.random.randint(0, width), np.random.randint(0, height), np.random.uniform(0.5, 1.0))
                     for _ in range(300)]

        for sx, sy, base_bright in stars:
            twinkle = base_bright + 0.5 * np.sin(frame_num / 5 + sx)
            brightness = int(100 + 155 * twinkle)
            cv2.circle(frame, (sx, sy), 1, (brightness, brightness, brightness), -1)

        # كوكب (مريخي) في الخلفية مع إضاءة
        planet_x, planet_y = width // 5, height // 4
        cv2.circle(frame, (planet_x, planet_y), 180, (30, 10, 80), -1)
        # إضاءة جانبية
        light_offset = int(40 * np.sin(light_phase))
        cv2.circle(frame, (planet_x + light_offset, planet_y - 30), 180, (80, 40, 120), 30)

        # المركبة الفضائية (منظور 3D بسيط)
        ship_center_x = width // 2 + 100
        ship_center_y = height // 2

        # الهيكل الرئيسي (بيضاوي منحرف لإحساس 3D)
        cv2.ellipse(frame, (ship_center_x, ship_center_y), (600, 220), -10, 0, 360, (70, 70, 180), 45)

        # نافذة القائد (مستطيل منحرف)
        pts = np.array([
            [ship_center_x + 200, ship_center_y - 100],
            [ship_center_x + 400, ship_center_y - 80],
            [ship_center_x + 380, ship_center_y + 80],
            [ship_center_x + 180, ship_center_y + 100]
        ], np.int32)
        cv2.fillPoly(frame, [pts], (180, 200, 255))
        # رأس القائد
        cv2.circle(frame, (ship_center_x + 290, ship_center_y), 60, (255, 240, 200), -1)

        # محركات بلازما (توهج يتنفس)
        pulse = int(100 + 155 * (np.sin(engine_pulse) + 1) / 2)
        glow_color = (255, 150 - pulse//3, pulse)
        cv2.ellipse(frame, (ship_center_x - 500, ship_center_y - 90), (120, 220), -20, 0, 360, glow_color, -1)
        cv2.ellipse(frame, (ship_center_x - 500, ship_center_y + 90), (120, 220), 20, 0, 360, glow_color, -1)
        engine_pulse += 0.25

        # كويكب يعبر المشهد
        asteroid_x += 18
        if asteroid_x > width + 400:
            asteroid_x = -400
        ast_y = height // 4 + int(50 * np.sin(asteroid_x / 100))
        cv2.circle(frame, (asteroid_x, ast_y), 100, (90, 80, 70), -1)
        # ذيل غبار متدرج
        for i in range(10):
            alpha = 1 - i/10
            trail_x = asteroid_x - 100 - i*50
            cv2.line(frame, (asteroid_x - 80, ast_y), (trail_x, ast_y + 60), 
                     (int(140*alpha), int(120*alpha), int(90*alpha)), int(40*alpha))

        # lens flare من المحركات
        flare_x = ship_center_x - 500 + int(80 * np.sin(frame_num / 10))
        cv2.circle(frame, (flare_x, ship_center_y), 100, (255, 220, 180), -1)

        frames.append(frame)
        light_phase += 0.08

    # تصدير
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"ultimate_spacecraft_{timestamp}"

    if export in ["image", "both"]:
        cv2.imwrite(f"{base}.png", frames[30])  # فريم حلو من النص
        print(f"🖼️  صورة عالية الجودة: {base}.png")

    if export in ["video", "both"]:
        video_path = f"{base}.mp4"
        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
        for f in frames:
            out.write(f)
        out.release()
        print(f"🎬 فيديو سينمائي دلع: {video_path} ({duration_sec} ثواني)")

    return {"image": f"{base}.png" if export in ["image", "both"] else None,
            "video": f"{base}.mp4" if export in ["video", "both"] else None}

# تشغيل مباشر للتجربة
if __name__ == "__main__":
    generate_ultimate_spacecraft_scene(export="both")