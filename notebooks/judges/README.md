# Models as judges

A team that builds an AI assistant changes it every week: a new instruction, a newer model, a different way of
finding records. Each change fixes some answers and breaks others, so before it ships someone compares a few
hundred answers from the old and the new version and decides which version is better. Reading them all by hand is
slow. Comparing them with simple code fails, because two answers can say the same thing in different words, and one
wrong number can hide in a fluent paragraph. So the reading is often handed to another language model, which gets
the task, the answers and some grading instructions and returns a verdict. That model is called a judge.

Judges now do much of the grading in AI work. They decide whether a new version of an assistant is better than the
last one. They rank models against each other: the MT-Bench study ([Zheng et al., 2023](https://arxiv.org/abs/2306.05685))
showed that a strong model's preferences agreed with human preferences about as often as two people agreed with
each other, and many leaderboards have relied on model judges since. They filter generated training examples,
keeping the good ones and dropping the rest. And they supply the feedback that some models are trained on:
Constitutional AI ([Bai et al., 2022](https://arxiv.org/abs/2212.08073)) and RLAIF
([Lee et al., 2023](https://arxiv.org/abs/2309.00267)) replace part of the human feedback in training with a
model's judgments.

In every one of these uses the judge's verdict becomes the score, and nobody reads most of the answers behind it.
If the judge prefers a confident wrong answer to a plain right one, the new version looks better while getting
worse, the training data keeps the wrong examples, and a model trained on the feedback learns to sound right
instead of being right. The judge's own mistakes are the hardest ones to see, because the judge is the tool that
was meant to catch mistakes.

## What can go wrong with a judge

Some of a judge's failures are about the answers: it misses a wrong number, accepts a claim the source does not
support, or cannot tell whether a piece of code handles an empty list. Others are about the way the question is
put to it, and these are well documented:

- Order. Many judges favour whichever answer they read first, or second. Swapping the two answers changed the
  verdict often enough in [Wang et al. (2023)](https://arxiv.org/abs/2305.17926) to reverse which of two models
  looked better.
- Length and polish. A longer, better formatted answer tends to win even when it is wrong.
  [Zeng et al. (2023)](https://arxiv.org/abs/2310.07641) built a test from pairs in which the answer that looks
  better does not do what the instruction asked, and many judges preferred it.
- Self-preference. Judges can recognise text written by their own model family and score it higher
  ([Panickssery et al., 2024](https://arxiv.org/abs/2404.13076)).
- Format. A program has to read the verdict. A judge that writes a sentence of working before its answer, or breaks
  the requested format, can leave the program with nothing to count, which is a different failure from a wrong
  verdict.

## How to test a judge

The direct test is to give a judge cases where the right verdict is already known and count how often it agrees.
The cases have to be built so that the right verdict does not depend on another opinion: code that passes or fails
hidden tests, a sum computed exactly, a rule applied by a program. When no such answer key exists, as for most
writing, a judge can still be tested for stability (does the verdict survive swapping the answers, rewording the
instruction, naming the author?) and for agreement with other judges, but agreement alone cannot say which judge
is right.

Every experiment in this folder uses data written for it after the judges were trained, so a judge cannot score
well by remembering the answer key. Each experiment is self-contained: its own notebook, inputs, cached model
responses, results, figures and a README that explains the topic from the beginning. Start with any of them; none
depends on this page.

## Experiments with results

### Grading answers whose right grade is computed (11)

[Notebook 11](11-llm-judges/) generated 120 grading tasks in code (invoice sums, versions of an order record,
conflicting reports, a made-up refund policy), each with two candidate answers whose fields were right or wrong by
construction. Claude Opus 5.5 and GPT-6.1 Sol graded every pair with three prompts and in both answer orders. GPT
was right in all 120 tasks with every prompt, a ceiling. Claude's apparent misses were almost all format failures:
94 of its 96 unsuccessful replies put a short note before a correct grade. Genuine wrong grades were 4 of 1,440.
The tasks were too easy to rank the judges or the prompts, which is the reason the newer experiments below build a
harder exam.

### Scoring writing when there is no answer key (15 and 17)

[Notebook 15](15-analytical-writing-style/) had 27 models write short decision documents and two judges from other
companies score their clarity under four instructions. Telling the judges to hunt for "AI slop" lowered clarity by
1.66 points out of 100, less than the 3.30 points a score moved when the same judge read the same draft again, and
naming the author made no detectable difference. The choice of judge mattered far more: on the same control texts,
judges' average clarity ran from 32.5 to 83.0.

[Notebook 17](17-writing-validation-extension/) showed what that gap does to a ranking. Six writers were scored by
two OpenAI judges and one Anthropic judge. Dropping judges from the writer's own company, a common precaution, put
GPT-6 Astra last of six; giving every writer the same judges put it first. The OpenAI judges scored every one of
282 drafts higher than the Claude judge, by 9.01 points on average, so the precaution ranked writers partly by
which judge they drew.

## Experiments in progress

These five experiments share one aim: to find out how a team should choose, combine and instruct judges. Four of
them use one exam, built in notebook 33, of answer pairs where code decides which answer is better and where the
pairs are hard enough that strong judges make mistakes.

- Which models make reliable judges (33, [issue #94](https://github.com/k-sandhu/experiment-notebooks/issues/94)).
  About ten judges, from Claude Opus 5.5 and GPT-6.1 Sol down to small open-weight models and the Decisions API,
  grade the same 240 pairs: code checked by hidden tests, worked solutions to new word problems, answers that must
  follow several checkable instructions, and answers drawn from long source documents. Each judge also tries to
  solve the code and word problems itself, to test whether a judge can grade answers it cannot produce.
- A weaker model as tie-breaker (34, [issue #95](https://github.com/k-sandhu/experiment-notebooks/issues/95)).
  Where the two strongest judges disagree, can a cheaper model settle it, alone or after reading both judges'
  reasons? This is the setting of debate studies such as
  [Khan et al. (2024)](https://arxiv.org/abs/2402.06782), in which a weaker judge decides between stronger models'
  arguments.
- Teaching a judge one person's taste (35, [issue #96](https://github.com/k-sandhu/experiment-notebooks/issues/96)).
  This repository's owner had every README rewritten to a stricter house style and merged the versions they
  accepted. Can a judge pick the accepted paragraph with no guidance, with the written style rules, with examples
  of past choices, or with a rubric distilled from those examples?
- How to build a judging harness (36, [issue #97](https://github.com/k-sandhu/experiment-notebooks/issues/97)).
  One part of the grading set-up changes at a time: one answer graded alone or two compared, one answer order or
  both, reasoning before or after the verdict, one reply or a majority of five, low or high reasoning effort, a
  strict output format, and solving the task before judging it.
- Structured instructions (37, [issue #98](https://github.com/k-sandhu/experiment-notebooks/issues/98)). Free-form
  instructions against a general rubric, a checklist written for each item, and separate scoring of each checklist
  question, with the hardest look at pairs where the worse answer is longer or more polished.
