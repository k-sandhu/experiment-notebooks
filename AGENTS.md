# Instructions for AI agents

This repo is a collection of independent experiments, one Jupyter notebook each. Read this file before
adding or changing a notebook.

## Layout

```
notebooks/NN-short-name/
  NN_short_name.ipynb   the experiment, committed with its outputs
  README.md             goal, headline result, key figure, how to run
  data/                 inputs, caches of every model response, results tables
  figures/              PNGs saved by the notebook (used by README.md)
```

## Rules for notebooks

- **Self-contained.** A notebook imports nothing from this repo. Helpers (CLI wrappers, caches, plot style)
  are defined inside the notebook, even if another notebook has the same code. Paths are relative to
  the notebook's folder.
- **Goal first.** The first cell states the question, why it matters, the data, the method and the
  headline result. A reader should get the answer from the first screen.
- **Structure:** goal and summary, setup and configuration, data (with a look at it), method, results
  (charts and tables), error analysis with concrete examples, limitations, how to reproduce.
- **Commit outputs.** Run top to bottom (`jupyter nbconvert --to notebook --execute --inplace`) before
  committing. A re-run must replay from the caches in `data/` without any API calls.
- **Charts:** matplotlib, one style block per notebook, a title that states the finding, labelled axes,
  no dual y-axes. Save the key figure to `figures/`.

## Model access

- OpenAI, Anthropic and Meta Muse models are called **only through their CLIs**: `codex exec`, `claude -p`
  and `muse exec`. Never through their HTTP APIs or SDKs.
- OpenRouter (`OPENROUTER_API_KEY`) is used only for open-weight models and for the OpenAI Decisions API,
  which has no CLI.
- Anything that costs money has a size knob (`N_...`, `MODELS`) at the top of the notebook. Defaults stay
  small. Print the spend at the end.
- Cache every model response on disk, keyed by the full request. Never commit keys or tokens.
- Judges are top models (Claude Opus, GPT via Codex, Muse) and never the model being judged alone.

## Data

Public data with its source and licence recorded, or synthetic data generated for the experiment. No
private or client data. Large public files (PDFs) are downloaded on demand and git-ignored.

## Writing style

Plain, specific, short. State what was measured and what it showed, with numbers.

- No filler or hype: "delve", "crucial", "robust", "seamless", "leverage", "unlock", "game-changer",
  "it's worth noting", "in today's fast-paced world", "comprehensive".
- No rhetorical questions as headings, no emoji, no exclamation marks.
- Do not claim more than the data supports. Small samples get confidence intervals or a caveat.
- Prefer a table or a number over an adjective.
