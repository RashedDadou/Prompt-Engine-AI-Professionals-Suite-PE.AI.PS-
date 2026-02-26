### The main project idea is:

Designing a supervisory AI system, supported by three assistants, each specializing in a specific task.

**An intelligent main supervisor (AI Supervisor)** manages the entire process and distributes tasks to **specialized assistants** (X3 Assistants) who handle the finer details.

### Role Distribution

- **AI Supervisor**
General Manager: Understands the request, determines its type (text or image), coordinates between assistants, reviews results, and decides whether to retry or accept.

- **AI Text Assistant**
Text specialist: Corrects grammar and syntax, improves phrasing, removes ambiguity, and prepares the final text before generation.

- **AI Image Assistant**
Provides prompt generation and optimization: Builds robust prompts, manages negative prompts, analyzes defects, and performs iterative optimization.

- **AI Helper**
Enrichment Expert: Adds specialized technical and visual details according to the field (space, vehicles, nature, history, art, etc.), suggests clarifying questions, and identifies priority and prohibited words.

### Why this design?

- **Reduced load on the main model** → Each helper focuses on a single task with high precision.
- **Improved accuracy and consistency** → The supervisor monitors and corrects, while the helpers handle the finer details.
- **Flexibility and scalability** → New helpers (such as AI Code Assistant and AI Research Assistant) can be added in the future.
- **Feedback loops** → The supervisor automatically retryes if problems are found, with continuous improvement.

### Time context

This model was designed in **1 July 2025**, a time when no one had adopted this design, as most prompt engineering systems relied on a single integrated engine (prompt → generate directly).
The idea was relatively early in using a "Supervisor + Specialists" architecture to improve prompt quality and reduce errors.

### The Main Challenge

Precise coordination between the supervisor and the three assistants is crucial to ensure that every step is coherent and that no information is lost or contradictions occur.
This design represents a step towards multi-agent AI systems, which are expected to become more common in 2026.
What do you think of this version? Would you like us to add practical examples or focus more on a specific aspect (such as the benefits of feedback loops)?
Design Structure:

AI_X3 /

├── supervisor.py # Main flow + Supervisor + process()

├── ai_helper.py # AIHelper + DomainExpert + Domain Enrichment

├── text_assistant.py # Text correction + supervise_and_generate

├── image_assistant.py # Connect to Replicate (or other)

├── text_feedback.py # Feedback Loop for analyzing and improving prompts

├── constants.py # (Optional) Keywords, regex patterns, etc.

