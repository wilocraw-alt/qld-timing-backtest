# Build & Verify Guide

This guide covers technical implementation rules and verification loops for native `pptxgenjs` builders.

## Native Build Mechanics

Write a single Node.js script (e.g., `slides/build_pptx.js`) that constructs the presentation programmatically.

### Layout Dimensions & Conversions

Set layout wide:
```javascript
const pptxgen = require("pptxgenjs");
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE"; // 13.333" x 7.5" (16:9 ratio)
```

To easily map layout specifications from a 1280px-wide mock canvas to inches:
```javascript
const toInches = px => px * 13.333 / 1280;
```

### Key Implementation Rules

1. **Never Reuse Option Objects**: `pptxgenjs` mutates option objects in-place (e.g., converting shadow values to EMUs). Reusing an options object across multiple shapes corrupts subsequent shapes. Use inline objects or factory functions:
   ```javascript
   // ✅ CORRECT
   const makeShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.10 });
   slide.addShape(pptx.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   slide.addShape(pptx.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   ```
2. **Colors (6-digit Hex Only)**: Do **not** prefix colors with `#`. Do **not** use 8-char hex values (e.g., `FF000030`), as they will silently corrupt the PowerPoint file. To apply transparency, use the `transparency` property in the options object:
   ```javascript
   // ✅ CORRECT
   fill: { color: "3B82F6", transparency: 50 }
   ```
3. **Text Padding / Alignment**: Text boxes contain internal margins by default. When aligning text with shapes, lines, or icons at the exact same horizontal coordinate, set `margin: 0` in the text box options.
4. **Shape Mapping**:
   - `ROUNDED_RECTANGLE` (with `rectRadius: 0.12` or similar) for content cards.
   - `RECTANGLE` for headers, flat dividers, and colored accent stripes. (Do not pair `ROUNDED_RECTANGLE` with flat accent stripes, as it creates clipping artifacts).
   - `OVAL` for icon backings and bullets.
   - `LINE` for connections, using `dashType: "dash"` for dashed/dotted loops.

## Verification Workflow

### Environment Limitations

The local sandbox environment lacks rendering libraries (no LibreOffice, poppler, or sudo) to generate PDF/image previews. Therefore, automated verification relies on static audit script execution, followed by visual confirmation by the user in a PowerPoint client.

### Build → Audit → Confirm Loop

Follow these steps for every slide deck modification:

1. **Build**: Run the Node script to generate the deck:
   ```bash
   node slides/build_pptx.js
   ```
2. **Audit**: Run the shared static audit script to analyze the PowerPoint file. It checks editability (verifies native elements rather than flat slides), boundaries, and text wrapping:
   ```bash
   python3 audit_pptx.py path/to/presentation.pptx
   ```
   *Heuristic*: The audit flags text boxes that are too narrow for their contents, which causes Korean characters to wrap vertically (1-character per line). Read the [pitfalls list](pitfalls.md) for more details.
3. **Fix**: Resolve any boundaries or text overflow warnings reported by the audit script in the Node script, then rebuild and re-audit.
4. **Confirm**: Submit the final `.pptx` file to the user for visual confirmation.
