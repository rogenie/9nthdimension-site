# 9nth Dimension site — how to work in this repo

Static site for 9nth Dimension, served by GitHub Pages from `docs/` on `main`.
Source lives in `content/`; `python3 build.py` regenerates `docs/` (needs `pip install markdown pyyaml`).
Never hand-edit `docs/`; always rebuild.

## Structure
- `content/rungs/` six hubs of the Spiritual Ladder (awakening, foundations, practice, healing, purpose, abiding)
- `content/articles/<slug>.md` one article per real question
- `content/pages/` ladder overview and About
- `content/backlog.yml` the article queue
- `content/site.yml` URL settings (switch to 9nthdimension.com once DNS is live)

## Publishing cadence
One article every other day. Never publish more than one article per run, and never backfill missed days. Mass publishing is what Google's scaled content abuse policy punishes.

## Article front matter
```
---
title: <the question, as people type it>
rung: <one of the six rung slugs>
date: YYYY-MM-DD
description: <150-160 characters: the direct answer>
faq:
  - q: <real follow-up question>
    a: <2-3 sentence answer>
---
```

## Article rules (every article must pass all of them)
1. The first paragraph answers the question directly, in 40-60 words, in bold.
2. 700-1,200 words. Depth over length; no filler, no padding, no keyword stuffing.
3. H2 headings phrased as the questions readers ask next.
4. One original element: a `<div class="practice" markdown="1">` block with "Today's practice" the reader can do today.
5. 3-5 FAQ entries in front matter, each a genuinely different follow-up question.
6. End with a section linking the reader toward the next rung (name the rung).
7. Scripture: cite chapter and verse; paraphrase or quote under 15 words; only cite verses you are certain say what you claim. If unsure, leave it out.
8. Voice: warm, plain, encouraging; Christian-rooted but welcoming to seekers. Byline is "the 9nth Dimension team". Never invent people, testimonials, statistics or studies.
9. Not a duplicate: before writing, read the titles of all existing articles; if the question is already covered, mark the backlog entry `status: skip` and take the next one.
10. Anything touching anxiety, depression, grief or abuse includes a gentle line recommending a doctor, counsellor or pastor. Never give medical advice.

## After writing
Run `python3 build.py`, confirm it prints without errors and that `docs/ladder/<rung>/<slug>/index.html` exists, set the backlog entry to `status: published` with `slug:`, commit with message `Publish: <title>`, push to main.
