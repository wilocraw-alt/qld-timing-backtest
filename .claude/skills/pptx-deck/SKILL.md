---
name: pptx-deck
description: "Use when creating, editing, or styling structured presentation decks (such as academic conference slide decks or technical reports). Covers native, editable pptxgenjs builds, structured layouts, and automated auditing."
license: Proprietary
---

# Presentation Deck Skill

## Deciding the Build Approach

**For final deliverables, always use NATIVE pptxgenjs** (`addText`, `addShape`, `addTable`, native charts/bars).
HTML → Chrome render → PNG-per-slide produces **uneditable images** (flat screenshots). This is only acceptable for mockups or visual previews, never for the final, editable slide deck deliverable. Diagrams and cards must also consist of native shapes and text, not embedded images.

## Workflow

1. Read [design-system.md](design-system.md) for palette, typography, and layout rules.
2. Write (or edit) a Node.js build script using `pptxgenjs` (typically `slides/build_pptx.js`).
3. Run the build script to create the `.pptx` presentation.
4. Run the static audit script to verify structure, boundary, and text overflow bounds:
   ```bash
   python3 audit_pptx.py path/to/presentation.pptx
   ```
5. Confirm the layout and design visually in PowerPoint.

## Reference Files

| File | Purpose |
|------|---------|
| [design-system.md](design-system.md) | Structured presentation design system (palette, typography, components, layouts) |
| [build-and-verify.md](build-and-verify.md) | Native build guidelines, coordinate conversion, and verification loops |
| [pitfalls.md](pitfalls.md) | Checklist of bugs and issues to avoid during slide generation |
