# AI Context Archive - 2026-05-26

## Purpose

This archive captures the project context before the next larger change to the interview scoring system.
It is meant to preserve product decisions, technical assumptions, and rollback context.

## Current Project

- Product: Offer Compass / Offer罗盘
- Frontend: Vue 3, Vite, Pinia, Vue Router, Axios, native CSS
- Backend: FastAPI, JWT auth, Supabase, Python service layer
- Database: Supabase PostgreSQL
- Main user table: `users_data`
- Avatar storage: Supabase Storage bucket `avatars`, with public URL stored in `users_data.avatar`
- Local frontend preview: `http://127.0.0.1:5173`
- Local backend API: `http://127.0.0.1:8005`

## Recent Stable Decisions

1. Users must see auth pages before accessing protected feature pages.
2. Registration should succeed, then return the user to login instead of auto-login.
3. User profile avatar should upload to Supabase Storage, not store large image data directly in the database.
4. Default avatar should display before the user uploads a custom avatar.
5. `users_data` is the current main user data table.
6. Feedback collection is currently local-only and not yet a Supabase table.
7. Community feature should stay lightweight in MVP; full community and points system are not first-priority.

## Interview Scoring Problem

Observed issue:

- Candidate can answer irrelevant content and still receive a positive score.
- This is a product/scoring logic problem, not primarily a model training problem.
- Since the app calls third-party LLM APIs, we cannot directly train the model in this MVP.

Correct implementation direction:

1. Define a strict scoring rubric.
2. Apply hard rule checks in backend code before model scoring.
3. Use the rubric in the model prompt only after the answer passes basic validity checks.
4. Validate model output again in code, including score caps.
5. Remove random high-score fallback logic.

## Current First-Pass Scoring Fix

Backend:

- `backend/main.py` currently contains strict rule-based scoring logic near the interview answer endpoint.
- Invalid, too-short, irrelevant, or obviously unserious answers should receive `0`.
- Example verified:
  - Question: explain Transformer Self-Attention
  - Answer: `我喜欢吃饭`
  - Result: `score = 0`

Frontend:

- `frontend/src/stores/interview.js` now calls `getStrictFallbackFeedback(answerText)` in the answer fallback path.
- Backend failure should no longer produce random `5-8` scores.

## Next Planned Change

Refactor the interview scoring rules out of `backend/main.py` into a dedicated service module, likely:

- `backend/app/services/interview_rubric.py`

Expected flow:

```text
candidate answer
-> backend hard validity check
-> invalid answer: direct 0
-> valid answer: optional LLM scoring with strict rubric prompt
-> backend post-check and score cap
-> frontend display score and feedback
```

## Safety Rules For Next Change

- Do not delete existing files.
- Do not change Supabase schema unless explicitly approved.
- Keep changes isolated to interview scoring files.
- Run frontend build after changes.
- Run at least one backend scoring sample:
  - irrelevant answer must return 0
  - empty answer must return 0
  - structured answer with evidence may receive a higher score

## Why Git Archive Matters Here

Git protects the code state.
This context archive protects the reasoning state.

For rollback:

- Git commit/tag can restore files.
- This document can restore why a decision was made.

