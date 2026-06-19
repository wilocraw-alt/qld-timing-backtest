# Build the paper to BOTH PDF and Word (.docx), with figures.
# Toolchain: latexmk + xelatex (texlive-xetex; for Korean: texlive-lang-korean +
# fonts-nanum), pandoc (docx), rsvg-convert (librsvg2-bin; SVG figures),
# ghostscript `gs` (pgfplots/standalone-tex charts -> PNG). English-only papers
# may switch xelatex->pdflatex.
PAPER=main

all: pdf docx pptx

# --- figures: one source -> PDF (for LaTeX) + PNG (for Word). Include them in
# --- LaTeX WITHOUT an extension: \includegraphics{figures/name} (pdflatex uses
# --- .pdf; build_docx.py rewrites to .png so Word embeds the raster). ---------
SVGS  := $(wildcard figures/*.svg)
FIGTEX:= $(wildcard figures/*.fig.tex)
FIGS  := $(SVGS:.svg=.pdf) $(SVGS:.svg=.png) $(FIGTEX:.fig.tex=.pdf) $(FIGTEX:.fig.tex=.png)

figures: $(FIGS)

# Diagrams authored as SVG (easy to hand-edit; e.g. the experiment structure).
figures/%.pdf: figures/%.svg
	rsvg-convert -f pdf -o $@ $<
figures/%.png: figures/%.svg
	rsvg-convert -f png -d 150 -p 150 -o $@ $<

# Data charts authored as standalone LaTeX (pgfplots): figures/<name>.fig.tex.
figures/%.pdf: figures/%.fig.tex
	cd figures && pdflatex -interaction=nonstopmode $*.fig.tex >/dev/null 2>&1 && mv $*.fig.pdf $*.pdf
figures/%.png: figures/%.pdf
	gs -q -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 -dUseCropBox -sOutputFile=$@ $<

pdf: figures
	latexmk -xelatex -interaction=nonstopmode $(PAPER).tex || \
	( xelatex -interaction=nonstopmode $(PAPER).tex && bibtex $(PAPER) && \
	  xelatex -interaction=nonstopmode $(PAPER).tex && xelatex -interaction=nonstopmode $(PAPER).tex )

# Same content as the PDF, as Word. build_docx.py inlines main.bbl, turns
# \cite{k} into [n], and rewrites figures to .png so citations + figures render
# in Word too (works with pandoc < 2.11, no citeproc needed).
docx: main.bbl figures
	python3 build_docx.py

main.bbl:
	$(MAKE) pdf

# PowerPoint presentation target (.pptx)
pptx: figures
	@if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then \
		echo "Building PowerPoint presentation..."; \
		if [ ! -d slides/node_modules ]; then \
			echo "Installing slides dependencies..."; \
			(cd slides && npm install --no-audit --no-fund) || echo "Warning: npm install failed, trying to continue anyway..."; \
		fi; \
		node slides/build_pptx.js || echo "Warning: Failed to generate PPTX deck."; \
	else \
		echo "Warning: node or npm not found. Skipping PPTX generation."; \
	fi

# Content and visual QA helpers
pptx-qa:
	@echo "Running Static Audit..."
	@AUDIT_SCRIPT=../../.claude/skills/pptx-deck/audit_pptx.py; \
	if [ -f "$$AUDIT_SCRIPT" ] && command -v python3 >/dev/null 2>&1 && python3 -c "import pptx" >/dev/null 2>&1; then \
		python3 "$$AUDIT_SCRIPT" main.pptx --forbidden aimux dispatcher handoff work.log run-summary per_agent || \
		echo "Warning: Audit found issues (see above). Continuing with QA."; \
	else \
		echo "Warning: Audit script or python-pptx not available. Skipping static audit."; \
	fi
	@echo "Running Content QA..."
	@echo "Converting main.pptx to PDF and rendering slides..."
	@mv main.pdf .main_paper.pdf 2>/dev/null || true
	@if [ -f ../../.claude/skills/pptx/scripts/office/soffice.py ]; then \
		python3 ../../.claude/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf main.pptx >/dev/null 2>&1 || \
		soffice --headless --convert-to pdf main.pptx >/dev/null 2>&1 || \
		echo "Warning: LibreOffice PDF conversion failed."; \
	elif command -v soffice >/dev/null 2>&1; then \
		soffice --headless --convert-to pdf main.pptx >/dev/null 2>&1 || \
		echo "Warning: LibreOffice PDF conversion failed."; \
	else \
		echo "Warning: soffice wrapper or LibreOffice not found. Skipping PDF conversion."; \
	fi
	@if [ -f main.pdf ]; then \
		if command -v pdftoppm >/dev/null 2>&1; then \
			pdftoppm -jpeg -r 150 main.pdf slide || echo "Warning: pdftoppm failed."; \
		else \
			echo "Warning: pdftoppm not found. Skipping image rendering."; \
		fi; \
		rm -f main.pdf; \
	fi
	@mv .main_paper.pdf main.pdf 2>/dev/null || true

# Snapshot the current paper (sources + outputs) to versions/vNNN-<date>[-label]/
# BEFORE a rewrite so prior versions are never clobbered:  make snapshot LABEL=foo
snapshot:
	./snapshot.sh $(LABEL)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.fls *.fdb_latexmk *.xdv sections/*.aux \
	      figures/*.aux figures/*.log .main_docx.tex

.PHONY: all pdf docx figures snapshot clean pptx pptx-qa
