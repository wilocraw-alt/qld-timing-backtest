# PPTX pitfalls (from real bugs)

## Reusing pptxgenjs option objects
pptxgenjs **mutates option objects in-place** (converting shadow values to EMU).
Reusing one object across calls corrupts the second shape.
- Use **factory functions** or fresh inline objects per call.

## 8-char hex colors
`"E4002B08"` or any hex with >6 characters silently becomes black (`"000000"`).
- Use **6-digit hex only**. Apply transparency via `transparency` property in the fill object.

## Full-slide images for each slide
HTML -> Chrome render -> PNG -> pptx produces **zero editability**.
The entire slide is one unselectable image.
- **Always use native pptxgenjs** (addText/addShape/addTable). Accept slightly lower pixel-fidelity for full editability.
- HTML->PNG is OK only for mockups/previews, never for the final deliverable.

## Accent line under title
A horizontal line under the slide title is a **hallmark of AI-generated slides**.
- **Never use accent lines under titles.** Separate with whitespace or background color instead.

## Cards stretched to full content height
`height: 100%` + `flex: 1` + bottom strip creates **empty interior band**
when content is shorter than the container.
- Use **content-based height** and vertically center the card row in the content area.
  Balanced whitespace beats empty interior.

## Narrow connector labels (e.g. 0.2" wide)
Korean text in a narrow text box wraps **1 character per line**,
producing 8-9 lines that overflow vertically onto neighbors.
- Widen to **>= 1.3"**, set `wrap: false`, use smaller font (9-10pt),
  and position outside the main box region (vertically).

## Embedded image `object-fit: cover`
`cover` clips the image edges. For diagrams with bottom captions,
the caption gets cut off.
- Use **`contain`** instead — the entire image (including caption) stays visible.

## Emoji / FontAwesome icons in headless Chrome
FontAwesome or Unicode emoji renders as **tofu (□)** in headless Chrome
without the font installed.
- Use **inline SVG icons** (in HTML builds) or **native OVAL+text shapes**
  (in pptxgenjs builds).

## Verification by geometry only
Checking shape bounding boxes (`left/top/width/height`)
**misses rendered text overflow** — a label wraps vertically inside a box
that is technically within bounds.
- Add a **text-overflow heuristic**: chars-per-line approx = box_width_px/font_pt;
  flag if cpl <= 3 with text length > 3.

## Diagram label outside slide bounds
Output labels positioned to the right of the last diagram box can extend
**beyond 13.333"** slide width and are invisibly clipped.
- Verify all right edges <= 13.2" (with margin). Use python-pptx shape-bound audit.
