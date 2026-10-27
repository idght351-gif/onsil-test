# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A study/quiz app for the Korean 온실가스관리기사 (Greenhouse Gas Management Engineer) practical exam. All UI text is Korean, and the user communicates in Korean.

- `app/` — the working app: React 18 + TypeScript + Vite + Tailwind v4, a mobile-first PWA with no backend.
- `streamlit/` — the Python/Streamlit port so the app can be deployed (spec: `PRD.md`, staged build prompts: `PROMPTS.md`). Stage 1 skeleton exists: `app.py` routes on `st.session_state["screen"]` to `ui/screens/<name>.render()`, navigation goes through `core/nav.go()` (sets state + `st.rerun()`), data comes from `data/*.json`. Answering/grading/storage (stage 2) and styling (stage 3) are not built yet.
- `prd.md` — product spec for the React app (game rules R1–R10, calc grading, photo solutions).
- `온실가스 20xx*.txt` — source exam questions (2020–2023). They contain **no answers**. All model answers, explanations and mnemonic tips in `app/src/data/questions.ts` are self-authored, so treat them as needing verification.
- `디자인코드.txt` — HTML of a third-party tape-brand site used as the visual reference. Borrow its palette, shapes and textures only; never its logos or photos.

## Commands

Run these from the repo root (or drop `--prefix app` when inside `app/`):

```bash
npm --prefix app run dev      # dev server on :5173
npm --prefix app run phone    # dev server exposed on LAN (vite --host) for testing on a phone
npm --prefix app run build    # tsc -b (type check) + vite build
```

There is no lint config and no test runner. Data and grading checks are run as ad-hoc scripts:

1. Write a `.ts` file that imports `app/src/data/questions` and `app/src/lib/*`. Use absolute paths, because the scratch dir is outside the repo.
2. Bundle it with `npx esbuild <file> --bundle --platform=node --outfile=<out>.cjs`.
3. Run it with `node`.

Useful invariants to check:

- **Blanks:** every template `{{n}}` count matches `blanks.length`.
- **Model answers:** the model answer grades as `correct`.
- **Distractors:** the first distractor grades as wrong.
- **Choices:** each blank yields 4 unique choices.
- **Calc blanks:** no step answer leaks into the calc blank template.

`.claude/launch.json` (repo root) defines the preview servers `ghg-quiz` (port 5173, `--host`) and `ghg-streamlit` (port 8501).

Streamlit (run from inside `streamlit/` so `.streamlit/config.toml` is picked up):

```bash
python -m streamlit run app.py
```

`streamlit/data/questions.json` is generated from the React data; after editing `app/src/data/questions.ts`, regenerate it by bundling `streamlit/scripts/export_data.ts` with esbuild (command in the file header) and running it from the repo root.

## Architecture (app/)

**No router.** `App.tsx` holds a `route` state plus a `Session`. Each screen in `src/screens/` is a function component that gets callbacks. Wrong-note retry stores pending IDs, then reuses the difficulty → countdown flow.

**Quiz flow.** `Quiz.tsx` renders `QuestionRunner`, keyed per question so its state resets each time. The runner walks through these phases:

1. `answer`
2. `selfcheck` — only for a hard calc question with a photo
3. `feedback`
4. `explain`

The result is written to storage when entering `explain`, not on submit. That way the hard-mode self-grade override ("맞았어요/틀렸어요") counts.

**Question model** (`src/types.ts`) is a union of `text` and `calc`.
- **Text questions:**
  - `template`: the model answer with `{{1}}`-style blanks.
  - `blanks`: each has `answer`, `synonyms` and `distractors`.
  - `keywords`: used for hard mode. `"a|b"` means either one is accepted.
  - `unordered`: list answers that may come in any order.
- **Calc questions** have `steps`, and the last step is the final answer. `quiz.ts:calcAsBlanks` turns the steps into a blank template for easy/normal mode. It masks earlier step values that appear in later expressions as `(①)`, so step exprs in the data must use exactly the formatted value of earlier steps.

**Difficulty → grading** (`src/lib/grading.ts`):
- **하 (easy):** 4-choice per blank (`choicesFor`). Number distractors are generated as common-mistake multiples.
- **중 (normal):** typed blanks. `normalize` ignores spaces, case, commas, subscripts and `·`. Numbers are compared with a relative tolerance of 0.1% (`NUM_TOLERANCE`).
- **상 (hard), text:** keyword ratio ≥ 0.7.
- **상 (hard), calc:**
  - Numbers are pulled out of the typed work. `extractNumbers` skips digits attached to letters, such as the 2 in CO2.
  - These are matched against step values, along with the final value.
  - Verdict: correct = final ok and steps ≥ 0.75; partial = only one of the two.
  - Photo mode uses a manual per-step checklist instead of number matching.

**Storage** (`src/lib/storage.ts`):
- localStorage keys are `ghg.wrongNotes.v1`, `ghg.stats.v1`, `ghg.settings.v1` and `ghg.favTips.v1`. All access is wrapped in try/catch.
- Wrong-note rules:
  - A wrong or partial answer adds or updates the note and resets its streak.
  - 2 correct answers in a row (`GRADUATE_STREAK`) graduate it.
- Photos are shrunk to ~900px JPEG data URLs. If saving fails, the note is saved without the photo.

**Domain conventions:**
- GWP uses IPCC 2nd Assessment Report values, as the Korean guidelines do: CH4 21, N2O 310, SF6 23,900.
- Fuel calculations use 순발열량 (net calorific value).
- Oxidation factor applies to CO2 only.
- CH4 and N2O factors in kg are divided by 1,000 before multiplying by GWP.

## Styling

Tailwind v4 is set up through `@tailwindcss/vite`. All design tokens and custom classes live in `src/index.css`:

- **Colors:** `ink` #013900, `lime` #b6fe00, `forest`, `paper`, `pen` (red). The old `brand-*` scale is remapped to greens.
- **Dark mode is intentionally disabled.** `@custom-variant dark` requires a `.dark` class that is never set. Leftover `dark:` classes are inert.
- **Custom classes:**
  - `.paper` / `.grid-paper`: textures.
  - `.tape`: a masking-tape strip with a clip-path.
  - `.peel-*`: the tape-peel reveal, used by `components/PeelTape.tsx`.
  - `.draw`: SVG stroke-draw animation, used by `components/Doodles.tsx` for the red-pen ⭕/△/✕ marks.
  - `.font-display`: Black Han Sans, loaded from Google Fonts in `index.html`.
- **Doodle timing:** in `Quiz.tsx`, the grade mark's delay is computed from the peel stagger, so the mark appears after the tapes finish peeling.

## Gotchas

- **Case-insensitive filenames:** Windows treats `PRD.md` and `prd.md` as the same file. That is why the Streamlit PRD lives at `streamlit/PRD.md`.
- **Tailwind version:** `tailwindcss@4.0.0` breaks the build ("Cannot convert undefined or null to object"). Stay on 4.1.x.
- **Browser preview:** when the browser pane is hidden, animations are throttled. Screenshots can show screens mid-animation or stale. Prefer `get_page_text`, or wait and retake.
- **Streamlit storage:** `streamlit-local-storage` 0.0.25's `LocalStorage` returns `{}` before the browser has answered. Persisting state on the first run would wipe the saved data. Wait until the real value arrives (e.g. call the raw component with `default=None`) before writing.
