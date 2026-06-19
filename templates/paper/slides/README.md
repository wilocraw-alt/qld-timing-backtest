# slides/ — Paper Presentation Deck

This directory contains the pptxgenjs scaffold for building an academic
conference talk (.pptx) from the paper's content.

## How to author a deck

1. **Read the paper source**: `sections/*.tex` (or `main.docx` via markitdown).
2. **Edit CONTENT** in `build_pptx.js` — replace the placeholder text, authors,
   bullets, and stats with your paper's actual content.
3. **Reuse figures**: figures from the paper (`figures/*.png`) are embedded
   automatically if present. No extra figure generation needed.
4. **Build**: `make pptx` (or `node slides/build_pptx.js` from the paper root).
5. **QA**: `make pptx-qa` — static audit (editability, bounds, text overflow, forbidden words) + content check + render to images for visual inspection.
   Use a subagent to inspect `slide-*.jpg` for layout issues.

## Rules

- **No internal harness names**: Do not mention `run-summary.json`, `work.log`,
  `handoff_*`, `aimux`, `dispatcher`, etc. in slide text, captions, or speaker
  notes. Present data as measured results only.
- **Follow the palette**: Teal Trust (`028090` / `00A896` / `02C39A`). Maintain
  the dark-title/dark-thanks sandwich structure.

## Prerequisites

- Node.js + npm
- pptxgenjs (`npm install` in this directory)
- LibreOffice (`soffice`) + poppler (`pdftoppm`) — for QA rendering
- `pip install "markitdown[pptx]"` — for content QA

All are optional for the pdf+docx build; `make pptx` degrades gracefully if
Node.js is absent.
