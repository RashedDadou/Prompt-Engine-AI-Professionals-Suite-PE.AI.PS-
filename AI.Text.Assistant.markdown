### AITextAssistant Class – Intelligent Prompt Engineer

The `AITextAssistant` class is the brain behind Stellar Designer Pro's smart prompt enhancement system. It transforms simple user descriptions into highly detailed, professional-grade prompts optimized for the Grok Imagine (Aurora) model.

#### Purpose
Automatically enrich user input with technical, aesthetic, and cinematic details to produce superior spacecraft imagery — without requiring the user to be a prompt engineering expert.

#### Key Features

- **Pattern-Based Analysis**  
  Uses advanced regular expressions to detect key concepts in the user's prompt such as:
  - Engines/thrusters/propulsion
  - Angles/orientation
  - Thrust/power values
  - Shields/armor
  - Length/dimensions
  - Engine distribution/layout
  - Colors and materials

- **Knowledge-Driven Enhancement**  
  Pulls real-time values from the `KnowledgeLibrary`:
  - Preferred thrust (e.g., 12.5 meganewtons)
  - Preferred engine angle (e.g., 18.0 degrees)
  - Shield material (e.g., titanium-alloy)
  - Learned style bias (cinematic, cyberpunk, etc.)

- **Contextual Memory Integration**  
  Analyzes the last few user inputs (short-term memory) to detect recurring requests (e.g., "better engine distribution") and proactively adds relevant improvements.

- **Smart Detail Injection**  
  Dynamically appends professional descriptions like:
  - "main engines delivering 12.5 meganewtons each"
  - "auxiliary engines angled at 18.0 degrees for superior maneuverability"
  - "multi-layered titanium-alloy shields"
  - "symmetrically distributed in triangular clusters for perfect balance"

- **Artistic & Quality Boosters**  
  Always adds high-end rendering hints:
  - Dramatic volumetric lighting
  - Deep space nebula backdrop
  - Lens flare effects
  - Masterpiece, ultra-detailed, 8K resolution, sharp focus, professional rendering

- **Style Bias Awareness**  
  Incorporates the user's learned preferred artistic style for consistent aesthetic evolution over multiple generations.

#### Benefits
- Users with zero prompt engineering knowledge get stunning, coherent results.
- The app "learns" your taste over time through RLHF integration.
- Ensures technical accuracy and visual grandeur in every generated spacecraft design.

This class turns casual ideas into masterpiece-level AI art prompts — the secret sauce that makes Stellar Designer Pro truly intelligent.