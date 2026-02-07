Description :


How the AI ​​Supervisor Works:
Manages the process, sends the request to assistants, and oversees it.

If there is an error, it requests a correction.
AI Text Assistant: Checks the text, corrects errors (such as "baluna" to "plasma engines"), and adds missing details (such as "10 meganewtons").
AI Image Assistant: Generates an image based on the enhanced text.
If it detects a flaw (such as the absence of "15 degrees"), it returns a note about the error.

- **Intelligent Request Type Classification**

Automatically determines whether the request is text-only or requires an image/visual description (even without explicit words like "draw" or "picture" in some cases after enhancements).
- **Multi-Stage Text Enhancement and Correction**
- Basic grammar and spelling correction
- Intelligent enrichment using AI Helper (add specialized details, prioritize words, block words, suggested level of detail)

- **Iterative Image Prompt Generation and Improvement**

- Generate a high-quality initial prompt
- Automatic improvement using TextFeedbackLoop (add details, remove duplicates, avoid negative words)
- Robust negative prompt support
- Retry up to 3 times with increased detail in advanced attempts

- **Comprehensive Multi-Level Review**

- Check text-image consistency
- Detect critical, intermediate, and minor errors and suggestions
- Display the final result with the original request + enhanced text + image description

- **Feedback Loop**

- Analyze the prompt after each generation
- Update the results history by category for future performance improvement
  
- **Multi-Try Support with Automatic Suggestions**

- Retry up to 3 times if problems are found
- Add Text Improvement Suggestions for the Next Attempt

- **Modeled and Scalable Design**

- Clear separation of components: Supervisor, TextAssistant, ImageAssistant, AIHelper, FeedbackLoop
- Easy addition of new templates or image providers (Replicate, Flux, Midjourney, etc.)

## 📋 Project Structure (Basic)

How AITextAssistant Works:

It specializes in text errors in general. For example, if the AI ​​Supervisor reads a user request and finds it misspelled or unclear in a word or phrase, it sends this report to AITextAssistant to help it analyze the ambiguity and errors in the text. The report is then processed (without ambiguity or errors). The AI ​​Supervisor will review it and take the necessary actions to facilitate user requests.
This includes AITextAssistant's duties in resolving problems and errors that occur in various generation processes.
This includes overseeing the complete accuracy of the information that reaches the engine. Image Generation.
This involves periodically checking the generation engine to learn the details of responses and non-responses, understanding the limitations and obstacles, and providing automatic solutions as reports.
This also involves conducting a comprehensive review with the generation engine to evaluate the work and creating a large library divided into dedicated generation sections, for example:
Images of people, plants and trees for all different environments (terrestrial/marine), engineering images (various engines/systems/cars/locomotives/buses/ships/aircraft/spacecraft), etc.
Current Status and Future Improvements: Initial Request Classification (text vs. image), Automatic Enrichment + Multi-Attempt Review, Displaying the final result within the review report, Improving classification accuracy for descriptive requests without "drawing", Supporting multiple image providers (Flux, SD3, etc.) via a unified interface, Actual image generation (currently only prompts are generated), Simple interface (CLI or Gradio/Streamlit are preferable).

## 🚀 How to Operate (Quick)

```bash
# 1. Requirements
pip install -r requirements.txt # (Add torch or other as needed)

# 2. Key Setup
# In the .env file
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Run the test
python supervisor.py

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

How AI Helper Works

- **AI Helper Specialized by Domain**

Contains domain experts for space, vehicles, nature, history, art, biology, materials, philosophy, etc.

Adds detailed information, suggests clarifying questions, and provides technical feedback

- **Iterative Prompt Generation and Improvement**

Generates an initial prompt → Analyzes it → Adds details or improves lighting/composition → Makes up to 3 attempts

Supports a robust negative prompt

Uses a feedback loop to improve results over time

- **Comprehensive Review**

Reveals inconsistencies, omissions, and critical issues

Displays the original request + improved text + image description in a single report

- **Smart Retry Loop**

Adds an automatic improvement suggestion at the end of each failed attempt

Increases the detail level in advanced attempts

- **Modeled Design**

Clear separation between:

• Supervisor • Text Assistant

• Image Assistant

• AI Helper (Specialized Enrichment)

• Feedback Loop

Suggested Next Steps: Improve metadata request categorization (use stronger regex or more visible keywords)
Add a duplicate cleanup step in the prompt
Actual image generation connection (return image link or save)
Simplified interface (Gradio or Streamlit)
Support for multiple models (Flux, SD3, etc.) via a unified interface

## Current File Structure (Basic)

## Quick Startup

```bash
# 1. Install Requirements
pip install replicate python-dotenv

# 2. Set the key (in .env)
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Run
python supervisor.py

----------------------------------------------------------------------------------------------------------------------------------------------

# text_assistant.py – AI Text Assistant for Optimizing and Generating Prompts

## General Description

This file contains the main class `AITextAssistant` for managing text permissions and preparing it for image deployment (especially in space and technical fields). It relies on the following helper classes for music separation: Prompt Builder, Knowledge Enricher, Negative Manager, and Recording.

## Key Features

- **PromptBuilder**: Builds a complete prompt with visual cleaning knowledge, iterative optimization, and feedback loop integration.

- **KnowledgeEnricher**: Loads technical and visual details from a knowledge base (e.g., plasma engines → glowing blue exhaust).

- **NegativePromptManager**: Constructs a negative prompt harmonic (principal + context + solid negatives) with recording removal. - **IterationRefiner**: Visibly improves the face (adding details, boosting weights, and adjusting parameters like style).

- **Main Class AITextAssistant**: Manages the entire path via `supervise_and_generate` (Enrich → Build → Muscle Inspection → Refine).

## How to Use It

Python
Import AITextAssistant from text_assistant

Assistant = AITextAssistant()
Result = assistant.supervise_and_generate(
Enhanced_text="Rocket with plasma engines inclined at 15 degrees"
Iteration = 2
max_detail_level="High"
)

print(result["prompt"]) # Ready-made prompt
print(result["negative_prompt"]) # Negative
print(result["issues"]) # Any inconsistencies

(In beta) Suggested to expand visual_knowledge and enrich_rules for more domains.

Added priority/blocked keywords for integration with admin.py.

Separated classes into main prompt files.

Added logging and robust error handling.

Improved class classification with a wide dictionary or regex.

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# image_assistant.py – Image Generation Implementation Layer

**A lightweight and flexible layer** responsible for **actually generating images** from a ready-made prompt, without any additional text modification. It acts as a bridge between the prompt engineering system (supervisor + text_assistant) and the image generation providers.

## Main Purpose

- Retrieve ready-made prompts and negative prompts from the overhead system
- Execute requests via an external provider (currently Replicate only)
- Wait for the result + save the image locally + return links and information
- Maintain separation of responsibilities: does not modify the prompt, only executes it

## Current Features

- **Replicate** support (Flux-schnell by default)
- Use of **os.getenv** for the key → secure and does not contain hard-coded keys
- Smart **Polling** for waiting for the result with a timeout
- Automatically save the image to the `generated_images` folder
- Neat and beautiful output via `print_result()`
- Support for customizable **parameters** (aspect_ratio, steps, guidance, seed, ...)

## How to Use

```python
from image_assistant import AIImageAssistant

# Initialization
assistant = AIImageAssistant(
api_provider="replicate",

# api_key="r8_..." ← Preferably use .env

)
# Generate Image
result = assistant.generate_image(
prompt="futuristic spacecraft with glowing plasma engines, dynamic tilt, cinematic lighting",
negative_prompt="blurry, low quality, cartoon, deformed",
aspect_ratio="16:9",
num_inference_steps=30,
guidance_scale=4.0,
seed=42
)

# Display Result
assistant.print_result(result)

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# constants.py – Smart Request Classification Definitions and Constants

A simple, central file containing the **basic rules** for determining the request type:

Is it an **image/draw/prompt** request or **pure text**?

Used everywhere fast and accurate classification is needed (such as `supervisor.py` and `text_assistant.py`).

## Main Components

### 1. `IMAGE_POSITIVE_INDICATORS`
A list of words and phrases that strongly indicate a request for an image, drawing, or visualization.

- Includes: direct requests (image, draw, generate), tool names (midjourney, dalle, flux), common descriptive phrases (looks, appears, imagine, show me, display).

- Data type: `frozenset` → fast search, immutable, secure.

### 2. `IMAGE_NEGATIVE_PATTERNS`
Regex patterns that negate image requests even if a positive word is present.

- Examples: "No image," "Text only," "I don't want a drawing," "Explanation without images."

- Applied first → Prevents incorrect classification in cases like "Explanation without image" or "Text only."

### 3. `normalize_text_for_image_check(text)`

A central cleaning function that prepares text for checking:

- Converts to lowercase
- Removes punctuation
- Reduces extra spaces
- Used in every check to ensure high accuracy (especially with mixed Arabic)

### 4. `is_likely_image_request(text)`

The main classification function (called directly by supervisor):

- Check order: Negative first → Positives immediately → Fallback (long description ≥ 9 words)
- Smart logic that handles colloquialisms and long phrases

## Why this design?

- **High Speed**: `frozenset` + Direct Search (O(1) on average)
- **Improved Accuracy**: Strong regex negation prevents common errors
- **Easy Maintenance**: All rules in one place → Adding a new word takes seconds
- **Good Arabic Support**: Understands both colloquial and formal Arabic (e.g., "Show me," "Show me," "Show me...")

## Usage Example

```python
from constants import is_likely_image_request

print(is_likely_image_request("Draw a rocket with plasma engines")) # True

print(is_likely_image_request("Explanation of rockets without a picture")) # False

print(is_likely_image_request("A rocket with plasma engines glowing blue exhaust")) # True (Thanks to fallback + enrichment)

print(is_likely_image_request("Write an article about space")) # False

Suggested Future Improvements: Add weight/confidence score to each word (instead of (bool only)
Supports more colloquial Arabic (Egyptian, Gulf, Levantine)
Integration with a local micromodel for more accurate classification (optional)
Dynamic AIHelper pros list (automatically updated)

Essential part of the AI ​​Supervisor project – a multi-agent system for improving prompts and image generation

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# vision_feedback.py – حلقة تغذية راجعة بصرية (Vision Feedback Loop)

ملف متخصص في **تقييم الصور الناتجة** مقارنة بالـ prompt الأصلي، باستخدام نموذج رؤية خارجي (مثل GPT-4o أو نماذج مشابهة).  
يهدف إلى إغلاق الحلقة التكرارية: توليد → تقييم → تحسين → إعادة توليد.

## الغرض الرئيسي

- أخذ prompt أصلي + رابط صورة ناتجة
- إرسال الاثنين إلى نموذج رؤية (vision model)
- استخراج:
  - تناقضات وأخطاء بصرية/فيزيائية/هندسية
  - اقتراحات تحسين للـ prompt و negative prompt
  - درجة رضا (0–10)
- إرجاع تعديلات جاهزة للجولة التالية

## الميزات الحالية

- دعم **OpenAI GPT-4o** (أو o1) كمزود رئيسي
- **system prompt** محترف ومتخصص في الصور العلمية/الفضائية
- رد بتنسيق **JSON** فقط (سهل التحليل)
- دعم **negative prompt** الحالي لتحسينه أيضًا
- Error handling أساسي + fallback إذا فشل الـ JSON parsing

## كيفية الاستخدام

```python
from vision_feedback import VisionFeedbackLoop

# تهيئة (يفضل استخدام .env)
feedback_loop = VisionFeedbackLoop(
    api_provider="openai",
    # api_key="sk-..."  ← أو من OPENAI_API_KEY في .env
)

# تقييم صورة ناتجة
report, new_prompt, new_negative = feedback_loop.evaluate_and_suggest(
    original_prompt="futuristic spacecraft with glowing plasma engines, dynamic tilt",
    generated_image_url="https://replicate.delivery/.../img.png",
    current_negative="blurry, low quality, cartoon"
)

print("تقرير التقييم:", report)
print("\nالـ prompt المحسن:", new_prompt)
print("الـ negative المحسن:", new_negative)Saves fallback images with unique filenames.

Offline-First Reliability
Ensures the app always produces a result, making it perfect for testing, demos, or restricted environments.

BenefitsLeverages xAI's state-of-the-art Aurora model for photorealistic, creative spacecraft designs.
Guarantees usability even without internet or API access.
Keeps the focus on creativity — users get stunning visuals every time.

This class is the reliable powerhouse that brings your spacecraft visions to life, powered by Grok when possible and pure creativity when needed.




StellarDesigner Class :

The Core Logic ControllerThe StellarDesigner class serves as the main supervisor and logic hub for the application's intelligent features, bridging the knowledge system, prompt enhancement, and image generation components.PurposeOrchestrate the smart behavior of Stellar Designer Pro by managing prompt enhancement, RLHF-based learning from user ratings, and style preference tracking — ensuring consistently improving and personalized spacecraft designs.Key FeaturesCentralized Knowledge & Image Access
Initializes and holds instances of KnowledgeLibrary and AIImageAssistant for seamless interaction across the app.
Advanced Prompt Enhancement
Takes raw user input and dynamically enriches it with:Learned technical values (thrust in meganewtons, engine angles in degrees).
Shield material preferences.
High-quality rendering boosters (volumetric lighting, 8K, sharp focus, masterpiece).
Artistic style details based on current bias.

Style Bias Integration  Applies selected style (from UI buttons) or automatically uses the highest-scoring learned style.
Injects rich, style-specific descriptors (e.g., neon lights for cyberpunk, chrome details for retro sci-fi).
Tracks the last used style for accurate feedback learning.

Reinforcement Learning from Human Feedback (RLHF)
When a user rates a design:Adjusts style preference score (+1.5 for high ratings, -1.0 for low).
Fine-tunes numerical preferences:Increases/decreases preferred thrust (5–20 MN range).
Adjusts preferred engine angle (5–45° range).

Logs updates for transparency and debugging.

Safe & Bounded Learning
All RLHF adjustments are clamped within realistic ranges to prevent extreme or unstable values.

BenefitsEnables true personalization: the more you use and rate designs, the better the app understands your engineering and aesthetic preferences.
Ensures consistency across sessions via persistent knowledge storage.
Combines technical accuracy with artistic vision in every generated prompt.
Provides the foundation for the app's "learning over time" magic.

The StellarDesigner class is the heart of the system's intelligence — quietly evolving with every rating to become your perfect spacecraft design co-pilot.




AISupervisor Class :

The Intelligent OrchestratorThe AISupervisor class acts as the central "brain" of Stellar Designer Pro, managing the full generation pipeline, long-term memory, and Reinforcement Learning from Human Feedback (RLHF) cycles.PurposeCoordinates all components (text enhancement, image generation, knowledge storage, and user feedback) to create a truly adaptive, learning AI design assistant that improves with every interaction.Key FeaturesFull Pipeline Management
Handles the complete workflow from user input → prompt optimization → image generation → quality evaluation → memory storage.
Iteration Tracking
Maintains a global iteration counter and timestamps for every design session, enabling long-term progress tracking.
RLHF Feedback Loop
When the user provides a rating (0-100):  Analyzes the previous prompt.  
Updates the KnowledgeLibrary with adjusted preferences (thrust, angle, style bias).  
Reinforces successful elements and reduces unwanted ones over time.

Advanced Prompt Optimization
Uses AITextAssistant to enrich prompts with context from recent memory (last 5 inputs).
Detects recurring themes (e.g., repeated requests for better symmetry) and proactively improves them.
Final Polish Layer
Adds consistent high-quality boosters based on learned style bias (e.g., cinematic lighting, nebula backdrop, 8K masterpiece hints).
Memory & History System
Stores full session history including:Original user input
Final optimized prompt
Generated result (path/URL)
Auto-evaluated quality score
Timestamp

Automatic Quality Evaluation
Provides an internal quality score (0-100) based on alignment with learned preferences (thrust, angle, materials, style).
Debug & Insight Tools
Includes show_memory_summary() to print recent design history — perfect for understanding how the AI evolves.

BenefitsTurns one-off generations into a personalized, evolving creative partner.
Implements real RLHF without external frameworks — lightweight and fully integrated.
Enables the app to "remember" your taste and refine spacecraft designs progressively.
Provides transparency: you can see exactly how and why the AI improves.

The AISupervisor is what transforms Stellar Designer Pro from a simple image generator into a genuine intelligent design companion that gets smarter with every starship you create.

Improvements:

From 2D Fallback → 3D Real-Time Rendering with dynamic motion and lighting from simple PIL drawing → Using OpenGL with animated lighting, depth, shadows, and a perspective camera (gluPerspective).
The stars, planets, and asteroids move, the light rotates... This is a real animation video, not just a picture!

→ This isn't Fallback... It's a standalone 3D rendering engine!

Exporting both image and video simultaneously (export_format="both") now produces an HD image and a 5-second animated MP4 video at the same time.
This means the user can see the spaceship moving in front of them from the pilot's perspective... like a real space game!
Integrating live data from X (Twitter Trends) retrieves trending hashtags in real time and displays them in the scene as an overlay!

→ This means each rendering will be time-unique, linked to what's happening in the world right now... This is insanely brilliant!

Integration with Unreal Engine + BlenderProc + PyOpenGL in the same class! It attempts to use Unreal Engine for professional rendering.
If that fails → BlenderProc for export.
If that fails → Manually use PyOpenGL with advanced 3D rendering.

→ This is a multi-engine fallback system... like AI, it chooses the best available engine!

Dynamic voice (pyttsx3) announces when the rendering is complete: "Spacecraft ready for launch."

→ The experience is now multi-sensory: sight + hearing!

Color selection GUI (colorchooser): A dedicated control panel to choose the color of the hull and weapons... truly interactive!
Memory Priority System: Calculates the priority of information based on the importance of words (like plasma, laser).

→ Memory is now intelligent and organized according to importance.

