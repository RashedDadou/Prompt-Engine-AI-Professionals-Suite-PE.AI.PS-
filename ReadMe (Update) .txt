Prompt Engine AI Professionals Suite (PE.AI.PS) :

KnowledgeLibrary Class :

Persistent Learning DatabaseThe KnowledgeLibrary class is the long-term memory and knowledge storage system of Stellar Designer Pro. It uses SQLite to persistently store and retrieve learned preferences, spacecraft specifications, style biases, and favorite designs across sessions.PurposeEnable the application to remember and evolve based on user interactions over time — making every new design session smarter than the last.Key FeaturesThread-Safe SQLite Integration
Uses threading.local() to provide each thread with its own database connection, preventing conflicts in multi-threaded environments (e.g., during image generation).
Dynamic Table Creation
Automatically creates required tables on first use:knowledge: Stores spacecraft technical details (category, subcategory, key, value).
rl_policy: Stores RLHF-learned numerical preferences (e.g., preferred thrust, angle).
style_bias: Tracks user preference scores for artistic styles (cyberpunk, cinematic, etc.).
favorites: Records saved designs with file path, prompt, and timestamp.

Default Value System
Sets sensible initial values (e.g., 10.0 meganewtons thrust, 15.0° engine angle, titanium-alloy shields) and initial neutral scores for all styles.
Smart Query & Update Methods  query() / update(): For structured spacecraft knowledge.
query_rl() / update_rl(): For numerical RL policy values.
query_style() / update_style(): For style preference scores.
get_preferred_style(): Returns the highest-scoring style for automatic use.

Favorites Management  add_favorite(): Saves design metadata in database and copies image to a dedicated favorites/ folder.
get_favorites(): Retrieves full history of saved designs.

Persistent Learning
All changes (from user ratings via RLHF) are saved immediately and loaded on next launch — your preferences survive app restarts.

BenefitsTrue long-term personalization: the app remembers your favorite engine power, shield material, and visual style forever.
Enables genuine RLHF evolution without external servers or cloud dependency.
Keeps favorite designs organized and easily accessible.
Lightweight, fast, and fully offline-capable.

The KnowledgeLibrary turns Stellar Designer Pro into a learning companion that grows with you — the more you design, the better it understands your vision.




AIImageAssistant Class :

Core Image Generation EngineThe AIImageAssistant class handles all interactions with the Grok Imagine API and provides robust fallback mechanisms for reliable image creation.PurposeSeamlessly generate high-quality spacecraft images using xAI's powerful Grok Aurora model while ensuring the app works offline or during API issues with artistic manual drawings.Key FeaturesReal Grok API Integration
Connects to the official https://api.x.ai/v1/images/generations endpoint.
Supports the latest models (e.g., "grok-imagine-aurora" or "grok-2-image").
Handles authentication via XAI_API_KEY environment variable.
Downloads and saves generated images locally with timestamped filenames.
Flexible Generation Options
Customizable image sizes: 1792x1024 (Landscape), 1024x1024 (Square), 1024x1792 (Portrait).
Returns success status, local file path, original URL, and enhanced prompt for full traceability.
Graceful Error Handling
Catches API timeouts, errors, or missing keys.
Provides clear error messages for debugging.
Enhanced Fallback Drawing System
When the API is unavailable (no key, rate limits, or network issues):  Generates a beautiful manual spacecraft illustration using PIL.  
Includes deep space background, glowing nebula effects, detailed hull, plasma engines with flame trails, and energy shields.  
Customizable and visually appealing — far beyond basic shapes.  
Saves fallback images with unique filenames.

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
