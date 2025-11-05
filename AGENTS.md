# Children’s Activity Booklet Agent

## Purpose
This agent generates multi-page children’s activity booklets using:
- An AI model to create structured page specifications (creative content).
- A Python-based PDF renderer to build a consistent printable booklet.
- A fully local Dockerized environment for privacy, reproducibility, and cost control.

---

## System Architecture Overview

### 1. Langflow (Orchestration Layer)
- Provides a visual workflow builder.
- Connects LLM → Validation → Rendering steps.
- Runs fully locally inside Docker.

### 2. LLM (Idea + Structure Generator)
- Takes a theme and audience parameters (age, complexity).
- Produces structured JSON describing booklet pages.
- LLM creativity is encouraged, formatting is controlled downstream.

### 3. Validator (Specification Normalizer)
- Converts AI output (which may include text chatter) into clean JSON.
- Ensures each page has required fields (layout, title, text, optional image).
- Enforces max page count and prevents malformed specs from breaking the renderer.

### 4. Python Renderer (Deterministic Output)
- Uses ReportLab (and optionally Pillow) to generate printable PDF pages.
- Ensures visual consistency across all booklet outputs.
- This approach avoids font/layout instability of LLM-generated images or PDFs.

---

## Key Design Principles

| Principle | Application |
|---------|-------------|
| **LLM = Creativity** | Storyline ideas, page instructions, age-appropriate tone. |
| **Python = Structure** | Layout, fonts, spacing, printable geometry. |
| **Docker = Reproducibility** | Same environment, every time, everywhere. |
| **Text-only pipeline between components** | Prevents Langflow type mismatch issues. |


## Advantages of This Approach
- Fully offline compatible.
- Lower inference cost than generating images/PDF layout using AI.
- Easier to evolve booklet formats without retraining or re-prompting.
- More consistent, professional, and printable results.

---

## Next Steps (Optional Enhancements)
- Add automatic image generation for coloring pages.
- Introduce multiple visual layout templates.
- Add difficulty scaling per age group.
- Export as EPUB / web flipbook viewer.
