# Expanded-constraints Kimi pilot

Twenty requested posts: four models, five successive standalone drafts each. These are generated outputs for review.

## gpt-6.1-sol

### Post 1

Kimi K3.1 Pro scored 55 in Artificial Analysis’s evaluation, ahead of GPT-6 Astra and Gemini 4 Argon at 53, and behind Claude Opus 5.5 at 58. That puts it close to the leading proprietary models on that evaluation. Moonshot promises to release the full model weights by November 4, which would make this level of performance available for teams to evaluate on their own infrastructure.

The API is already available at $2 per million input tokens and $10 per million output tokens, matching GPT-6.1 Sol’s pricing and costing half as much as Claude Opus 5.5. A Highspeed version offers a claimed 2–3× speed increase at twice the price, with cached input tokens priced the same. For latency-sensitive workloads, that creates a specific trade-off to measure against response-time requirements.

The weight release is still pending. Once available, the licence and hardware requirements will help determine whether running the model privately is practical. Benchmark scores give teams a reason to test it; task accuracy, serving costs and latency will determine whether it belongs in production.

### Post 2

Moonshot is charging twice as much for a version of Kimi K3.1 Pro that it says runs 2–3 times faster. Cached input tokens cost the same on both versions, so the premium for a workload will depend partly on how much input comes from the cache.

The standard API costs $2 per million input tokens and $10 per million output tokens, matching GPT-6.1 Sol. Kimi also supports low, medium and max reasoning levels. A useful evaluation would compare those settings on the same tasks before committing to the faster service.

There is a reason to put it on the test list: Artificial Analysis scored Kimi at 55, ahead of GPT-6 Astra at 53 and behind Claude Opus 5.5 at 58. That aggregate score leaves the purchasing decision open. For an interactive application, measure whether the faster version brings acceptable answers within the required response time, then calculate the extra cost at expected traffic levels.

### Post 3

Kimi K3.1 Pro is available through Moonshot’s OpenAI-compatible API. The article’s author tested it with an existing command-line tool, asking for an SVG of a pelican riding a bicycle at each supported reasoning level: low, medium and max. They also ran the same prompt against Kimi K3, giving the comparison a consistent task across both models.

One practical detail matters for anyone repeating that approach: the tool’s “llm openai endpoint” command does not log results automatically. The author explicitly saved standard output and the reasoning trace to separate files. Keeping those records makes it possible to revisit a result and compare runs without relying on selected screenshots.

Kimi K3.1 Pro’s score of 55 on Artificial Analysis makes it a credible candidate for further testing. The pelican examples offer a narrower view of its output. For a workflow that generates SVGs, a useful follow-up would check whether the markup renders correctly and how consistently the model follows the prompt across repeated runs at each reasoning setting.

### Post 4

Moonshot’s benchmarks place Kimi K3.1 Pro roughly alongside Claude Opus 5.5 and GPT-6 Astra, with results varying by test. Artificial Analysis provides a separate comparison: Kimi scored 55, below Opus 5.5 at 58 and above GPT-6 Astra at 53. Those results support evaluating Kimi alongside the leading proprietary models, while leaving its performance on a particular workload to be tested.

The model is already available through Moonshot’s API at $2 per million input tokens and $10 per million output tokens. Full weights are promised for November 4, 2026. That release would let teams assess running it on their own infrastructure, subject to the licence and hardware requirements.

Teams considering that route can start collecting representative test cases against the API now. Saving the outputs alongside the reasoning settings would establish a baseline for evaluating a self-hosted deployment when the weights become available. Serving costs and response times would need to be measured on the intended hardware.

### Post 5

Kimi K3.1 Pro’s standard API pricing matches GPT-6.1 Sol: $2 per million input tokens and $10 per million output tokens. The article puts it at half Claude Opus 5.5’s price. For teams comparing model costs, those rates provide a starting point; the bill also depends on how many tokens each model uses to complete the work.

The quality results make that comparison worth running. Artificial Analysis scored Kimi at 55, with Opus 5.5 at 58 and GPT-6 Astra at 53. Those scores provide context, while a workload-specific test can establish how often each model produces an acceptable result.

A practical cost test would use the same set of tasks and count retries and rejected outputs in the total spend. Kimi supports low, medium and max reasoning settings, so each setting deserves a separate result. The cheapest configuration per completed task may differ from the cheapest one per million tokens.

## gpt-6.1-terra

### Post 1

Tag format failure: raw response shown below.

Kimi K3.1 Pro is available through Moonshot’s API, with model weights promised by November 4. Its early benchmark results suggest those weights could give developers access to a model that competes with leading closed models.

Artificial Analysis scored it at 55, ahead of GPT-6 Astra and Gemini 4 Argon at 53, and behind Claude Opus 5.5 at 58. Moonshot’s own benchmarks also show Kimi close to Opus 5.5 and GPT-6 Astra, though those results come from the model’s developer.

API pricing is $2 per million input tokens and $10 per million output tokens. A Highspeed version costs twice as much for most tokens and runs 2–3 times faster, according to Moonshot; cached input tokens cost the same on both versions.

The weight release will determine whether developers can run the model themselves. For now, access is through the API.

### Post 2

Kimi K3.1 Pro gives API users a choice between standard pricing and a Highspeed version that Moonshot says runs 2–3 times faster. Highspeed costs twice as much for most tokens, while cached input tokens cost the same on both versions.

The standard API price is $2 per million input tokens and $10 per million output tokens. Developers weighing the faster option will need to consider how much response time matters for their application and how often they can reuse cached input.

Moonshot has promised to release the model weights by November 4. Until then, K3.1 Pro is available through its API.

### Post 3

Kimi K3.1 Pro supports three reasoning levels: low, medium and max. The article’s author tested each one on the same prompt, asking the model to generate an SVG of a pelican riding a bicycle, and ran the same comparison against Kimi K3.

That kind of repeated prompt gives a way to inspect differences in a specific output. Broader benchmark scores provide a separate measure: Artificial Analysis scored K3.1 Pro at 55, between Claude Opus 5.5 at 58 and several models at 53, including GPT-6 Astra.

K3.1 Pro is available through Moonshot’s API. Moonshot says it will release the full model weights by November 4.

### Post 4

Moonshot’s Kimi K3.1 Pro has reached the API with benchmark scores close to those of leading closed models. Artificial Analysis scored it at 55, behind Claude Opus 5.5 at 58 and ahead of GPT-6 Astra, Claude Fable 5.1 and Gemini 4 Argon at 53.

Moonshot says it will release the full model weights by November 4. If that happens, developers will be able to work with the weights of a model that has scored near the top of this benchmark.

For now, API access costs $2 per million input tokens and $10 per million output tokens. Moonshot also offers a Highspeed version that it says runs 2–3 times faster at twice the price for most tokens.

### Post 5

Kimi K3.1 Pro is available through an OpenAI-compatible API endpoint, so developers can try it with tools that support that interface. The article’s author used the LLM command-line tool to send the same SVG prompt at each of Kimi’s three reasoning levels: low, medium and max.

The author also ran the prompt against Kimi K3 at those levels, making it possible to compare the generated images across both models. The LLM endpoint command does not log results, so the author saved the output and reasoning trace separately.

Moonshot says it will release the full K3.1 Pro model weights by November 4. Until then, the model is available through its API.

## claude-opus-5-5

### Post 1

Moonshot released Kimi K3.1 Pro on its API on October 23 and has promised the full model weights by November 4. If that date holds, this will be the first open weight model to score this close to the leading closed models.

Artificial Analysis scores it 55 on its index. That puts it ahead of Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon, which all score 53, and behind only Claude Opus 5.5 at 58. Moonshot's own benchmarks show it roughly level with Opus 5.5 and GPT-6 Astra, winning on a few and coming close on the rest.

API pricing is $2 per million input tokens and $10 per million output tokens. That matches GPT-6.1 Sol and is half the price of Opus 5.5. A Highspeed version runs 2 to 3 times faster at double the price, although cached input tokens cost the same on both versions.

The API is OpenAI-compatible, so you can try it now without new tooling. The original write-up runs it through the llm openai endpoint command from LLM 0.32, pointed at https://api.moonshot.ai/v1, and tests all three reasoning levels the model supports: low, medium and max. That command doesn't log results, so the author redirected stdout to one file for the output and stderr to another for the reasoning trace.

Once the weights are published, teams that need to run a model on their own infrastructure will be able to use one that benchmarks close to the leading closed models.

### Post 2

Kimi K3.1 Pro is available today only through Moonshot's API. Moonshot says the full weights will be released by November 4, and once that happens anyone can download and run a model that Artificial Analysis ranks second overall.

Its score there is 55. Claude Opus 5.5 leads at 58, and Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon sit just behind Kimi at 53. Open weight models have usually trailed the closed frontier by a clear margin, and this is the first time a model with weights on the way has placed this high.

The hosted pricing gives a sense of what Moonshot thinks it's worth: $2 per million input tokens and $10 per million output, the same as GPT-6.1 Sol and half the price of Opus 5.5. A Highspeed option costs twice as much and runs 2 to 3 times faster. Cached input tokens cost the same on both, so workloads that reuse long prompts get the extra speed for less than double the cost.

The model supports three reasoning levels, low, medium and max. The original write-up ran its usual test, asking for an SVG of a pelican riding a bicycle, at each level and against the earlier Kimi K3 for comparison. Because the API is OpenAI-compatible, that kind of side-by-side takes only an endpoint URL and a key.

### Post 3

Moonshot's launch benchmarks for Kimi K3.1 Pro put it roughly level with Claude Opus 5.5 and GPT-6 Astra, ahead on a few tests and close on the others. Vendor numbers deserve some caution, so the more useful figure comes from Artificial Analysis, which scored it independently at 55. That places it behind Opus 5.5 at 58 and ahead of Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon, all at 53.

The two sources roughly agree. Kimi trails Opus 5.5 by a few points on the independent index, and Moonshot's own charts show that gap as smaller.

The model went live on the Kimi API on October 23. Moonshot says the full weights will follow by November 4, which would make it the highest-scoring open weight model so far. Pricing is $2 per million input tokens and $10 per million output, half of what Opus 5.5 costs. A Highspeed tier runs 2 to 3 times faster at double the price, with cached input tokens priced the same as the standard tier.

Benchmarks only go so far, and the original write-up also includes a hands-on check. It generated an SVG of a pelican riding a bicycle at each of the model's three reasoning levels, low, medium and max, and ran the same prompt against Kimi K3 for comparison. The calls went through the llm openai endpoint command, which works with any OpenAI-compatible API but doesn't log results. The author saved stdout and stderr to separate files so the reasoning trace was kept alongside the output.

### Post 4

When a new model ships on an OpenAI-compatible API, you can test it the same day without waiting for an SDK or plugin. The write-up on Kimi K3.1 Pro shows this with the llm openai endpoint command added in LLM 0.32. You give it the base URL (https://api.moonshot.ai/v1), a stored key, the model name kimi-k3.1-pro, and a prompt. Flags such as --responses and -o reasoning_effort low pass through to the API.

One detail is easy to miss. That command doesn't write to LLM's log database, so the author redirected stdout and stderr to separate files. The output goes to one file and the reasoning trace to the other, which keeps both for later comparison.

With that setup, the author ran the standard pelican-on-a-bicycle SVG prompt at each of Kimi's three reasoning levels, low, medium and max, and then ran the same prompts against Kimi K3 to compare the generations.

The model itself is worth testing. Artificial Analysis scores it 55, second only to Claude Opus 5.5 at 58 and ahead of GPT-6 Astra, Claude Fable 5.1 and Gemini 4 Argon. It costs $2 per million input tokens and $10 per million output, and Moonshot says the full weights will be released by November 4.

### Post 5

Kimi K3.1 Pro comes in two speeds on Moonshot's API. The standard version costs $2 per million input tokens and $10 per million output tokens. The Highspeed version runs 2 to 3 times faster and costs twice as much, so $4 and $20, with one exception: input tokens that hit the cache cost the same on both.

That exception matters for agents and coding tools that resend a long system prompt or a large codebase context on every call. Much of their input is cached, so switching to Highspeed raises the bill by less than double, and the main extra cost is in output.

The standard price matches GPT-6.1 Sol and is half of Claude Opus 5.5. On Artificial Analysis, Kimi scores 55, against 58 for Opus 5.5 and 53 for GPT-6 Astra, Claude Fable 5.1 and Gemini 4 Argon. Moonshot's own benchmarks put it roughly level with Opus 5.5 and GPT-6 Astra.

Moonshot also says the full weights will be released by November 4. After that, teams can compare the API price against running the model on their own hardware or through other hosting providers.

## claude-sonnet-5-5

### Post 1

Moonshot released Kimi K3.1 Pro on its API on October 23 and says full model weights will follow by November 4. Weights are not out yet, so it is still a hosted model for now.

On Artificial Analysis it scores 55. Claude Opus 5.5 leads at 58, and Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon each sit at 53. Moonshot's own benchmarks put Kimi roughly level with Opus 5.5 and GPT-6 Astra, ahead on a few tests and close on the rest. If the weights arrive on schedule, this will be the first open weight model to score this near the frontier.

Pricing is $2.00 per million input tokens and $10 per million output tokens. That matches GPT-6.1 Sol and is half the price of Opus 5.5. A Highspeed version runs 2 to 3 times faster at twice the price, except that input tokens served from cache cost the same as on the standard version.

The source write-up tested the model through Moonshot's API with the llm openai endpoint command in LLM 0.32, which works with any OpenAI-compatible endpoint. It does not log results, so the author redirected stdout and stderr to files to capture the output and the reasoning trace. The test prompt was an SVG of a pelican riding a bicycle, run at each of Kimi's three reasoning levels (low, medium and max) and again on Kimi K3 for comparison.

### Post 2

Kimi K3.1 Pro gives teams choosing a model on cost a concrete comparison. Moonshot prices it at $2.00 per million input tokens and $10 per million output tokens, the same as GPT-6.1 Sol and half the price of Claude Opus 5.5. On the Artificial Analysis index Kimi scores 55 against 58 for Opus 5.5, so half the price comes with a three-point gap. Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon each score 53.

Moonshot also sells a Highspeed version that runs 2 to 3 times faster at twice the price, with input tokens served from cache billed at the standard rate. Going by the article's figures, uncached Highspeed pricing lands close to what Opus 5.5 costs, so the faster tier mostly makes sense where latency matters more than the savings. Teams that send long, repeated prompts will pay less than the headline doubling suggests, since cache hits cost the same on both versions.

The model is available through Moonshot's API now, and the company has said it will release full weights by November 4, 2026. Once they are out, teams that need to run a model on their own infrastructure could consider Kimi alongside the hosted options. An index score and a vendor's own benchmarks describe general performance, so the model's results on a team's actual prompts remain the number to check before switching.

### Post 3

Moonshot's Kimi K3.1 Pro went live on its API on October 23, and one write-up about it shows a short way to test a new model without waiting for tooling support. The author used the llm openai endpoint command, which was added to LLM 0.32 in August and runs prompts against any OpenAI-compatible endpoint. The command takes Moonshot's base URL, a stored API key, the model name kimi-k3.1-pro, the prompt, a flag to use the responses API, and a reasoning_effort option.

This command does not log results, so the author redirected stdout and stderr into separate files to keep both the answer and the reasoning trace. The prompt was a request for an SVG of a pelican riding a bicycle, and Kimi K3.1 Pro supports three reasoning levels, low, medium and max, so the author ran it at each one. The same prompt then went to the earlier Kimi K3 at the same three levels, which gives a comparison between versions that changes only the model.

The model itself scores 55 on Artificial Analysis, behind only Claude Opus 5.5 at 58, and Moonshot has promised to release its full weights by November 4, 2026.

### Post 4

Two sources place Kimi K3.1 Pro near the top of the current field. Moonshot's own benchmarks show it roughly level with Claude Opus 5.5 and GPT-6 Astra, ahead on a few tests and close on others. Artificial Analysis, an outside evaluator, scores it 55. That puts it two points above Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon, which each score 53, and three below Opus 5.5 at 58. A vendor chooses which benchmarks to publish, so the independent score carries more weight, and both point to the same general position.

According to the article, this is the first time a model that is about to have open weights has scored this high against the frontier. The qualifier is that the weights are not out yet. Moonshot says it will release them in full by November 4, 2026. Until then the model is only available through Moonshot's API, at $2.00 per million input tokens and $10 per million output tokens.

If the release happens on schedule, organizations that cannot send data to an outside API, or that want to run a model on their own hardware, will have a model near the top of the index to choose from.

### Post 5

Moonshot is releasing Kimi K3.1 Pro in two steps. The model reached its API on October 23, and the company says full weights will follow by November 4, 2026, twelve days later. Until then it is a hosted service only, so early users pay Moonshot's prices of $2.00 per million input tokens and $10 per million output tokens. A Highspeed option runs 2 to 3 times faster at twice the price.

The API follows the OpenAI format, so tools that already speak that protocol can call it without special support. The author of one write-up used the llm openai endpoint command in LLM 0.32 with Moonshot's base URL and the model name kimi-k3.1-pro, and ran a test prompt at low, medium and max reasoning effort on the day the model launched.

Artificial Analysis scores the model at 55, behind only Claude Opus 5.5 at 58 and ahead of Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon, which each score 53. Early users are therefore working with a model close to the top of that index while the weights are still unpublished. Whether Moonshot publishes them on schedule remains open, and the date it gave is November 4.
