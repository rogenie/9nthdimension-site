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

## Brand (must match the @9nthdimension social posts)
- **Positioning:** "Ancient Texts Unsealed": the parts of the Bible and church history most churches skip, organized as the Spiritual Ladder of growth.
- **Reader:** the Awakened Skeptic, Christian women 25-40 who grew up in church and got the Sunday-school version. Not deconstructing their faith; going deeper into it. Biblically literate enough to be bored by surface content, but has never read Enoch and doesn't know how the canon was decided. Write so she feels like an insider, not a beginner.
- **Voice:** warm, reverent and unafraid, like a smart friend letting you in on something. Curious, bold, never New Age, never fluffy, always scripture-anchored, always fair to the evidence.
- **Pillars** (from the backlog's `pillar` field): hidden_scripture, prophecy, ot_mysteries, plus a few practical growth topics.
- **Look:** the site's styling is locked to the carousel engine's Illuminated Manuscript palette (oxblood, aged parchment, antique gold). Don't change colors or fonts without updating both.

## Accuracy guardrails (same as the post engine)
- Only quote or cite a Bible verse if it is real and correctly referenced. Never fabricate wording.
- Always label non-canonical material (1 Enoch, Jubilees, Gospel of Thomas, Josephus, church fathers) as non-canonical, and say which traditions accept which books.
- Present debated readings as "one reading", "some scholars", "ancient tradition holds", never as settled fact. Give the major readings, including skeptical ones, fairly.
- Prophecy: quote the text, give the history, then present the debate as a debate. Never set a date, never name a living person as the Antichrist, never claim a current event is a confirmed fulfillment.
- Banned claims (rewrite if any appear): "proves", "proof", "science confirms/proved", "NASA", "scientists confirmed", "X years before science", "before science knew", "germ theory", "the Bible described X first", "scientifically accurate/proven".
- Archaeology and history: give dates and finds only when you are certain of them; otherwise leave them out.

## Publishing cadence
One article every other day. Never publish more than one article per run, and never backfill missed days. Mass publishing is what Google's scaled content abuse policy punishes.

## Article front matter
```
---
title: <the question, as people type it>
rung: <one of the six rung slugs>
pillar: <hidden_scripture | prophecy | ot_mysteries | growth>
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
4. One original element: a `<div class="practice" markdown="1">` block with "Today's practice" the reader can do today. For text and history topics, make it a reading exercise with exact references (for example, read Jude 14-15, then the 1 Enoch passage it echoes, and compare).
5. 3-5 FAQ entries in front matter, each a genuinely different follow-up question.
6. End with a section linking the reader toward the next rung (name the rung).
7. Scripture: cite chapter and verse; paraphrase or quote under 15 words; only cite verses you are certain say what you claim. If unsure, leave it out.
8. Voice: as in the Brand section above. Byline is "the 9nth Dimension team". Never invent people, testimonials, statistics or studies. Follow every accuracy guardrail above.
9. Not a duplicate: before writing, read the titles of all existing articles; if the question is already covered, mark the backlog entry `status: skip` and take the next one.
10. Anything touching anxiety, depression, grief or abuse includes a gentle line recommending a doctor, counsellor or pastor. Never give medical advice.

## After writing
Run `python3 build.py`, confirm it prints without errors and that `docs/ladder/<rung>/<slug>/index.html` exists, set the backlog entry to `status: published` with `slug:`, commit with message `Publish: <title>`, push to main.
