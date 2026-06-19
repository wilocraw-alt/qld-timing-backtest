const path = require('path');
const fs = require('fs');

// ---------------------------------------------------------------------------
// CONTENT — EDIT THIS OBJECT per-paper. Everything below is layout helpers.
// ---------------------------------------------------------------------------

const CONTENT = {
  title: '[Paper Title]',
  subtitle: '[Subtitle / Tagline]',
  authors: '[Author Names]',
  affiliation: '[Institution]',

  slides: {
    // 1 — Title slide (dark background, generated automatically below)
    // PLACEHOLDER: Replace all [...] bracketed text with your paper's content.

    // 2 — Problem & Motivation
    problem: {
      title: 'Problem & Motivation',
      lead: '[Describe the core problem and why it matters — 1–2 sentences]',
      items: [
        '[Specific challenge or gap — item 1]',
        '[Specific challenge or gap — item 2]',
        '[Specific challenge or gap — item 3]',
      ],
    },

    // 3 — Related Work
    relatedWork: {
      title: 'Related Work',
      lead: '[Summarize the prior work landscape: methods, gaps, open questions]',
      items: [
        '[Prior approach A] — key strength, key limitation',
        '[Prior approach B] — key strength, key limitation',
        '[Prior approach C] — key strength, key limitation',
        'This work: [how your approach differs / advances the state]',
      ],
    },

    // 4 — Method Overview
    methodOverview: {
      title: '[Method Name / Title]',
      lead: '[One-sentence summary of the method / approach]',
      steps: [
        '[Step 1 description]',
        '[Step 2 description]',
        '[Step 3 description]',
        '[Step 4 description]',
      ],
    },

    // 5 — Method Details
    methodDetails: {
      title: '[Method Detail / Key Component]',
      items: [
        '[Key design decision or mechanism — item 1]',
        '[Key design decision or mechanism — item 2]',
        '[Key design decision or mechanism — item 3]',
        '[Key design decision or mechanism — item 4]',
        '[Key design decision or mechanism — item 5]',
      ],
    },

    // 6 — Experiment Setup
    experimentSetup: {
      title: 'Experiment Setup',
      items: [
        '[Task / benchmark description]',
        '[Setup configuration and parameters]',
        '[Data or inputs used]',
        '[Evaluation metrics]',
      ],
    },

    // 7 — Results (main)
    resultsMain: {
      title: '[Results: Headline Finding]',
      statValue: '[XX]%',
      statLabel: '[Primary metric label]',
      statValue2: '[X.X]',
      statLabel2: '[Secondary metric label]',
      statValue3: '[X]',
      statLabel3: '[Tertiary metric label]',
    },

    // 8 — Results (detailed)
    resultsDetailed: {
      title: '[Results: Detailed Breakdown]',
      rows: [
        ['[Group]', '[Metric A]', '[Metric B]', '[Metric C]'],
        ['[Condition 1]', '[value]', '[value]', '[value]'],
        ['[Condition 2]', '[value]', '[value]', '[value]'],
        ['[Condition 3]', '[value]', '[value]', '[value]'],
      ],
      caption: '[Brief takeaway or observation about the results.]',
    },

    // 9 — Discussion
    discussion: {
      title: 'Discussion',
      items: [
        '[Key finding or implication — item 1]',
        '[Key finding or implication — item 2]',
        '[Broader impact or significance — item 3]',
        '[Limitation or remaining open question — item 4]',
      ],
    },

    // 10 — Limitations
    limitations: {
      title: 'Limitations & Future Work',
      items: [
        '[Limitation or threat to validity — item 1]',
        '[Limitation or threat to validity — item 2]',
        '[Limitation or threat to validity — item 3]',
        'Future work: [planned direction or improvement]',
      ],
    },

    // 11 — Conclusion
    conclusion: {
      title: 'Conclusion & Future Directions',
      items: [
        '[Core contribution or finding — item 1]',
        '[Core contribution or finding — item 2]',
        '[Broader implication or practical relevance — item 3]',
        'Future work: [next steps or open directions]',
      ],
    },

    // 12 — Thank You (dark background, generated automatically)
  },
};

// ---------------------------------------------------------------------------
// Palette — Teal Trust (from contract)
// ---------------------------------------------------------------------------
const C = {
  primary: '028090',
  secondary: '00A896',
  accent: '02C39A',
  darkBg: '0F172A',
  lightBg: 'F8FAFC',
  text: '1E293B',
  muted: '64748B',
  white: 'FFFFFF',
  cardBg: 'FFFFFF',
  cardBorder: 'E2E8F0',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const FIGURES_DIR = path.join(__dirname, '..', 'figures');
const OUTPUT = path.join(__dirname, '..', 'main.pptx');

function figurePath(name) {
  const p = path.join(FIGURES_DIR, name);
  return fs.existsSync(p) ? p : null;
}

function makeShadow() {
  return { type: 'outer', color: '000000', blur: 6, offset: 2, angle: 135, opacity: 0.10 };
}

// ---------------------------------------------------------------------------
// Slide builders
// ---------------------------------------------------------------------------

function buildTitleSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText(CONTENT.title, {
    x: 1.0, y: 1.2, w: 8.0, h: 1.2,
    fontSize: 40, fontFace: 'Georgia', color: C.white, bold: true, align: 'center',
    margin: 0,
  });

  slide.addText(CONTENT.subtitle, {
    x: 1.5, y: 2.6, w: 7.0, h: 0.6,
    fontSize: 18, fontFace: 'Calibri', color: C.primary, align: 'center',
    margin: 0,
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.4, w: 3.0, h: 0.04,
    fill: { color: C.accent },
  });

  slide.addText(CONTENT.authors, {
    x: 1.0, y: 3.7, w: 8.0, h: 0.5,
    fontSize: 14, fontFace: 'Calibri', color: C.muted, align: 'center',
    margin: 0,
  });

  slide.addText(CONTENT.affiliation, {
    x: 1.0, y: 4.2, w: 8.0, h: 0.4,
    fontSize: 12, fontFace: 'Calibri', color: C.muted, align: 'center',
    margin: 0,
  });
}

function buildProblemSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.problem.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  slide.addText(CONTENT.slides.problem.lead, {
    x: 0.6, y: 1.3, w: 8.8, h: 0.5,
    fontSize: 14, fontFace: 'Calibri', color: C.muted, italic: true, margin: 0,
  });

  const items = CONTENT.slides.problem.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.problem.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.0, w: 8.8, h: 2.8,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 2.2, w: 8.0, h: 2.4,
    valign: 'top', margin: 0,
    paraSpaceAfter: 6,
  });
}

function buildRelatedWorkSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.relatedWork.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  slide.addText(CONTENT.slides.relatedWork.lead, {
    x: 0.6, y: 1.3, w: 8.8, h: 0.5,
    fontSize: 13, fontFace: 'Calibri', color: C.muted, italic: true, margin: 0,
  });

  const items = CONTENT.slides.relatedWork.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.relatedWork.items.length - 1,
      fontSize: 13, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 2.0, w: 8.8, h: 2.8,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 2.2, w: 8.0, h: 2.4,
    valign: 'top', margin: 0,
    paraSpaceAfter: 6,
  });
}

function buildMethodOverviewSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.methodOverview.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const steps = CONTENT.slides.methodOverview.steps.map((step, i) => ({
    text: `${i + 1}.  ${step}`,
    options: {
      breakLine: i < CONTENT.slides.methodOverview.steps.length - 1,
      fontSize: 15, fontFace: 'Calibri', color: C.text,
      paraSpaceAfter: 10,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(steps, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
  });
}

function buildMethodDetailsSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.methodDetails.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const items = CONTENT.slides.methodDetails.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.methodDetails.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
    paraSpaceAfter: 8,
  });
}

function buildExperimentSetupSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.experimentSetup.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const items = CONTENT.slides.experimentSetup.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.experimentSetup.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
    paraSpaceAfter: 8,
  });
}

function buildResultsMainSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.resultsMain.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const statHeight = 3.0;

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.5, w: 2.8, h: statHeight,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });
  slide.addText(CONTENT.slides.resultsMain.statValue, {
    x: 0.6, y: 1.7, w: 2.8, h: 1.2,
    fontSize: 48, fontFace: 'Georgia', color: C.primary, bold: true, align: 'center',
    margin: 0,
  });
  slide.addText(CONTENT.slides.resultsMain.statLabel, {
    x: 0.6, y: 3.0, w: 2.8, h: 1.2,
    fontSize: 14, fontFace: 'Calibri', color: C.muted, align: 'center',
    margin: 0,
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.6, y: 1.5, w: 2.8, h: statHeight,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });
  slide.addText(CONTENT.slides.resultsMain.statValue2, {
    x: 3.6, y: 1.7, w: 2.8, h: 1.2,
    fontSize: 48, fontFace: 'Georgia', color: C.secondary, bold: true, align: 'center',
    margin: 0,
  });
  slide.addText(CONTENT.slides.resultsMain.statLabel2, {
    x: 3.6, y: 3.0, w: 2.8, h: 1.2,
    fontSize: 14, fontFace: 'Calibri', color: C.muted, align: 'center',
    margin: 0,
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.6, y: 1.5, w: 2.8, h: statHeight,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });
  slide.addText(CONTENT.slides.resultsMain.statValue3, {
    x: 6.6, y: 1.7, w: 2.8, h: 1.2,
    fontSize: 48, fontFace: 'Georgia', color: C.darkBg, bold: true, align: 'center',
    margin: 0,
  });
  slide.addText(CONTENT.slides.resultsMain.statLabel3, {
    x: 6.6, y: 3.0, w: 2.8, h: 1.2,
    fontSize: 14, fontFace: 'Calibri', color: C.muted, align: 'center',
    margin: 0,
  });
}

function buildResultsDetailedSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.resultsDetailed.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const tableData = CONTENT.slides.resultsDetailed.rows.map((row, ri) =>
    row.map(cell => ({
      text: cell,
      options: ri === 0
        ? { bold: true, color: C.white, fill: { color: C.primary }, fontFace: 'Calibri', fontSize: 13 }
        : { color: C.text, fontFace: 'Calibri', fontSize: 13, fill: { color: ri % 2 === 0 ? C.cardBg : C.lightBg } },
    }))
  );

  slide.addTable(tableData, {
    x: 0.6, y: 1.3, w: 8.8,
    colW: [1.5, 2.4, 2.4, 2.5],
    border: { pt: 0.5, color: C.cardBorder },
    rowH: [0.5, 0.5, 0.5, 0.5],
  });

  slide.addText(CONTENT.slides.resultsDetailed.caption, {
    x: 0.6, y: 3.6, w: 8.8, h: 0.5,
    fontSize: 12, fontFace: 'Calibri', color: C.muted, italic: true, margin: 0,
  });
}

function buildDiscussionSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.discussion.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const items = CONTENT.slides.discussion.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.discussion.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
    paraSpaceAfter: 8,
  });
}

function buildLimitationsSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.limitations.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const items = CONTENT.slides.limitations.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.limitations.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
    paraSpaceAfter: 8,
  });
}

function buildConclusionSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.lightBg };

  slide.addText(CONTENT.slides.conclusion.title, {
    x: 0.6, y: 0.3, w: 8.8, h: 0.6,
    fontSize: 28, fontFace: 'Georgia', color: C.primary, bold: true, margin: 0,
  });

  const items = CONTENT.slides.conclusion.items.map((item, i) => ({
    text: item,
    options: {
      bullet: true, breakLine: i < CONTENT.slides.conclusion.items.length - 1,
      fontSize: 14, fontFace: 'Calibri', color: C.text,
    },
  }));

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 3.4,
    fill: { color: C.cardBg }, shadow: makeShadow(),
  });

  slide.addText(items, {
    x: 1.0, y: 1.5, w: 8.0, h: 3.0,
    valign: 'top', margin: 0,
    paraSpaceAfter: 8,
  });
}

function buildThanksSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.darkBg };

  slide.addText('Thank You', {
    x: 1.0, y: 1.5, w: 8.0, h: 1.0,
    fontSize: 40, fontFace: 'Georgia', color: C.white, bold: true, align: 'center',
    margin: 0,
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.0, y: 2.7, w: 2.0, h: 0.04,
    fill: { color: C.accent },
  });

  slide.addText('Questions & Discussion', {
    x: 2.0, y: 3.0, w: 6.0, h: 0.6,
    fontSize: 18, fontFace: 'Calibri', color: C.primary, align: 'center',
    margin: 0,
  });
}

// ---------------------------------------------------------------------------
// Main — build the deck
// ---------------------------------------------------------------------------

function main() {
  // eslint-disable-next-line global-require
  const pptxgen = require('pptxgenjs');
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';
  pres.author = CONTENT.authors;
  pres.title = CONTENT.title;

  // Sandwich: dark / light / light / ... / light / dark
  buildTitleSlide(pres);
  buildProblemSlide(pres);
  buildRelatedWorkSlide(pres);
  buildMethodOverviewSlide(pres);
  buildMethodDetailsSlide(pres);
  buildExperimentSetupSlide(pres);
  buildResultsMainSlide(pres);
  buildResultsDetailedSlide(pres);
  buildDiscussionSlide(pres);
  buildLimitationsSlide(pres);
  buildConclusionSlide(pres);
  buildThanksSlide(pres);

  pres.writeFile({ fileName: OUTPUT }).then(() => {
    console.log('Wrote ' + OUTPUT);
  }).catch(err => {
    console.error('Failed to write ' + OUTPUT, err);
    process.exit(1);
  });
}

// ---------------------------------------------------------------------------
// Graceful degredation if pptxgenjs not installed
// ---------------------------------------------------------------------------
try {
  main();
} catch (e) {
  if (e.code === 'MODULE_NOT_FOUND' && e.message.includes('pptxgenjs')) {
    console.log('');
    console.log('  pptxgenjs not found. To install:');
    console.log('    cd ' + path.join(__dirname) + ' && npm install');
    console.log('');
    console.log('  (Skipping .pptx build — pdf+docx unaffected.)');
    process.exit(0);
  }
  throw e;
}
