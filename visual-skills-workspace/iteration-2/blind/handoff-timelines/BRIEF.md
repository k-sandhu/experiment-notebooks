# Blind review of two explainers

You are reviewing two visual explainers, A and B, made by different people from the same request and
the same data. Judge them as the intended reader would experience them. Do not read or judge their
source code, comments or file sizes; judge what appears on screen and how it behaves.

For the case you are given:
- The request and the audience are in `request.txt`.
- The verified facts and numbers are in `facts.md` (the truth to check accuracy against).
- `A/` and `B/` each hold `explainer.html` and contact sheets (`sheet_w360.png` = phone width,
  `sheet_w560.png` = desktop card width), which show every step at several moments.

How to review:
1. Read `request.txt` and `facts.md`.
2. Look at all contact sheets of A and B (use the Read tool on the PNG files).
3. Open each page yourself in headless Chromium with Python Playwright at 390 px wide and use it as a
   reader would: step through it, press its buttons, drag its sliders, try its interactions. Take
   screenshots of anything you want to look at closely (save them under your review folder). If the
   default launch fails, pass `executable_path` to a Chromium under `%LOCALAPPDATA%/ms-playwright`.
4. Score each explainer from 1 (poor) to 5 (excellent) on:
   - **message**: would a newcomer come away able to state the main finding with its number?
   - **accuracy**: are numbers and claims on screen correct against facts.md, with illustrative or
     simulated values labelled and uncertainty stated where the data calls for it?
   - **engagement**: does it hold attention, and does the interaction or motion help understanding
     rather than decorate?
   - **craft**: layout, legibility at phone width, stable controls, no overlaps or clipping, polish.
   - **fit**: does it deliver the form the request asked for (lesson, replay, interactive, LinkedIn
     visual, engaging piece) for the stated audience?
5. Pick an overall winner (A, B or tie) and explain in 3-5 sentences what decided it, citing specific
   steps or screens. List up to 3 concrete defects for each.

Write your verdict as JSON to `verdict.json` in your review folder:
```json
{"case": "...", "scores": {"A": {"message": 0, "accuracy": 0, "engagement": 0, "craft": 0, "fit": 0},
                           "B": {"message": 0, "accuracy": 0, "engagement": 0, "craft": 0, "fit": 0}},
 "winner": "A|B|tie", "reason": "...", "defects": {"A": ["..."], "B": ["..."]}}
```
Reply with the JSON only.
