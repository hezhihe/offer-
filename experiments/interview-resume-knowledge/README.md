# Interview And Resume Knowledge Experiment

## Purpose

This folder isolates interview and resume knowledge extracted from private learning materials before it is wired into product code.

The goal is not to copy course content into the app. The goal is to convert useful ideas into maintainable product rules.

## Source Materials Reviewed

- Resume writing method material
- Interview practice material
- Self-selling / interview value expression slide deck

## Product Direction

Use the materials to improve:

1. Resume analysis and rewrite feedback
2. Mock interview qualitative feedback
3. Interview answer rewrite suggestions

Do not train a model in this MVP. Use the knowledge as:

- prompt rules
- evaluation rubrics
- test cases
- product copy guidelines

## Safety Boundary

- Do not upload private source files to external systems.
- Do not paste long original excerpts into prompts.
- Extract only general rules and product logic.
- Keep source PDFs/PPTX outside the repo unless the user explicitly approves.

## Next Integration Targets

1. `backend/app/services/interview_rubric.py`
2. `backend/app/services/resume_rubric.py`
3. Backend prompts for interview and resume analysis
4. Frontend display: concrete feedback, not abstract scores

