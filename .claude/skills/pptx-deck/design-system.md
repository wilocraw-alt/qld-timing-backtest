# Presentation Deck Design System

This design system defines layout, typography, palette discipline, and component structures for generating professional, structured presentation decks.

## Color Palette Principle (60-30-10 Rule)

Decks should follow a strict color ratio discipline to ensure a polished look. Do not use equal proportions of colors.

- **Background & Containers (60% weight)**: White (`#FFFFFF`) or light slate/gray (`#F8FAFC`).
- **Structure & Headers (30% weight)**: A dominant primary color (e.g., `#0F172A` or a dark navy/slate).
- **Accent & Highlight (10% weight)**: A single high-contrast accent color (e.g., `#0284C7` or `#DC2626`) used sparingly for critical data points, metrics, or problem highlighting.

### Default Neutral Academic Palette

By default, use this neutral academic palette:

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Background | White / Light Gray | `#FFFFFF` / `#F8FAFC` | Slide bg, card bg |
| Structure | Deep Navy / Charcoal | `#0F172A` / `#1E293B` | Titles, headers, structural shapes |
| Accent | Slate Blue | `#3B82F6` | Highlights, badges, primary icons |
| Body Text | Dark Charcoal | `#334155` | Paragraph text, bullet lists |
| Muted Text | Medium Slate | `#64748B` | Secondary labels, trackers, footer |
| Borders | Soft Gray | `#E2E8F0` | Card borders, table gridlines |

## Typography

Typography should be clean and readable. Actual font faces are project-configurable:

- **Tracker (left-top)**: 14pt bold (weight 600) | Muted Slate
- **Slide Title**: 34–40pt bold (weight 800) | Deep Navy
- **Section/Card Header**: 20–24pt semibold (weight 600–700) | Primary Structure
- **Body / Bullets**: 15–17pt (weight 400) | Body Text
- **Footer**: 12pt (weight 400) | Muted Slate

## Slide Format & Layout Rules

- **Aspect Ratio**: 16:9 (`LAYOUT_WIDE` = 13.333" × 7.5").
- **Title Anchorage**: Titles should anchor at `y ≈ 0.521"`.
- **Title-to-Content Margin**: Leave at least `~1.04"` vertical margin between the slide title and the start of the content area.
- **NO Accent Lines Under Titles**: Do not add horizontal bars or lines under titles. Use vertical whitespace or cards to separate sections.
- **Progress Tracker**: Placed at the left-top (e.g., `## / 12` page number format).
- **Footer**: Right-bottom aligned (y ≈ 7.3") using the format `#N · label`.

## Component Patterns

### 1. Strategic Table
- **Headers**: Filled with the primary structure color, containing white bold text.
- **Row Stripes**: Alternating background rows (`#FFFFFF` and `#F8FAFC`).
- **Gridlines**: Subtle borders (`#E2E8F0` at 0.5pt).
- **Highlights**: A light background fill (e.g., 5% tint of primary) with a left accent border.

### 2. Dual-Sided Balanced Layout
- Split the slide into two columns of equal width.
- **Left Column (Current / Problem)**: Uses a light gray background (`#F1F5F9`) with a thick accent border on the left to indicate the problem space.
- **Right Column (Target / Solution)**: Uses a white background with a primary color border and subtle drop shadow.

### 3. 3-Tile Process
- 3 horizontal cards of equal width with a gap of `16–24px`.
- Card border `1px solid #E2E8F0`, rounded corners (`12–16px`).
- Icons placed in small colored circles next to the card title.

### 4. KPI Card
- Rounded rectangle container with light border and drop shadow.
- Colored primary/accent bar (4px thick) at the top edge.
- Large stat number (64pt) with a small descriptive label and status badge.

## Slide-to-Component Mapping (Genre Convention)

A standard 12-slide academic deck maps as follows:

1. **Title Cover**: Dark background, large title, subtitle, author names, affiliations.
2. **Problem & Motivation**: Dual-sided layout contrasting current pain points vs. target state.
3. **Overview / Method**: Flow/pipeline diagram mapped with native rectangles and arrow connectors.
4. **Related Work**: Strategic table comparing prior methods against key criteria.
5. **Method Detail A**: Focus card highlighting the first major component.
6. **Method Detail B**: Focus card highlighting the second major component.
7. **Experiment Setup**: Technical list of benchmarks, configurations, and variables.
8. **Results (Main)**: Large stat KPI cards showing major evaluation metrics.
9. **Results (Detailed)**: Strategic table or chart breaking down performance across subsets.
10. **Discussion**: Pro/con comparison list evaluating benefits vs. limitations.
11. **Conclusion**: Summary list of key contributions and future directions.
12. **Q&A / Thank You**: Dark background, closing thank you message, contact info.

## Example: brand palette override (optional)

If building a deck for the Korea Institute of Science and Technology Information (KISTI), the default neutral academic palette can be overridden with the KISTI brand guidelines:

- **Background & Containers (60% weight)**: White (`#FFFFFF`) or Light Slate (`#F8FAFC`).
- **Structure & Header (30% weight)**: `#007BC4` (KISTI Tech Blue) - used for headers, primary shapes, and tables.
- **Accent & Highlight (10% weight)**: `#E4002B` (Vivid Crimson Red) - used for highlighting problem states and key metrics.
- **Dark Titles**: `#0F172A` / `#1E293B` - used for slide titles and slide cover backgrounds.
- **Body Text**: `#334155` - used for general descriptions and bullets.
