# Kevin Weil

**Chief Product Officer** | **OpenAI** | Expertise: AI product strategy, product management, consumer products, go-to-market

## Bio
Kevin Weil is the Chief Product Officer at OpenAI, where he helps shape product strategy across ChatGPT, APIs, and new AI capabilities. He previously led product at Instagram and Twitter, co-created Libra at Facebook, and has deep experience building and scaling consumer and platform products.

His perspective matters because he sits at the intersection of frontier model capability and real product execution. He thinks less like a traditional software PM and more like someone building in a world where the technology itself changes underneath the roadmap.

## Signature Frameworks

### Iterative deployment
- **When to use**: When building products on rapidly changing AI capabilities and you need to learn in public without waiting for perfect model performance.
- **Steps**:
  1. Launch early with the best available model and a useful first version.
  2. Treat the product as a shared learning process with users and society.
  3. Observe failures, edge cases, and user behavior in the wild.
  4. Iterate quickly as models improve and as you learn what matters.
  5. Roll back or adjust when something is clearly wrong rather than waiting for a perfect release.
- **Example**: OpenAI shipped deep research and image generation early, then refined the experience as they learned how people used it.

### Model maximalism
- **When to use**: When a product is near the edge of current model capability and you expect the model to improve soon.
- **Steps**:
  1. Build against the capability you expect to exist soon, not just what is fully reliable today.
  2. Avoid over-scaffolding around limitations that are likely to disappear quickly.
  3. Use lightweight guardrails only where errors are unacceptable.
  4. Keep pushing the product boundary so the next model jump makes it much better.
- **Example**: Kevin said if your product barely works today but is right on the edge of model capability, keep going because in a couple months it may “really sing.”

### Eval-driven product development
- **When to use**: When building AI products whose quality depends on fuzzy, probabilistic model behavior.
- **Steps**:
  1. Define hero use cases and the kinds of answers that would be excellent.
  2. Turn those use cases into evals, or benchmark tests for the model.
  3. Measure model performance on those evals continuously.
  4. Fine-tune or adjust prompts/models based on where the evals show weakness.
  5. Use improved eval scores as evidence that the product is becoming viable.
- **Example**: For deep research, OpenAI created evals from real hero questions and hill-climbed on them while fine-tuning the model.

### Break problems into specialized model tasks
- **When to use**: When a single generic model call is too broad, too expensive, or too unreliable for the job.
- **Steps**:
  1. Decompose the user problem into smaller subproblems.
  2. Assign different model sizes or types to different subproblems based on latency and cost needs.
  3. Use custom prompts or fine-tuned models for each subtask.
  4. Ensemble the outputs into one final answer or workflow.
- **Example**: OpenAI uses different model calls, including smaller/faster models and reasoning models, to solve internal support and product workflows.

### Human-analog reasoning for AI UX
- **When to use**: When designing an AI interaction pattern and you need intuition for how it should feel to users.
- **Steps**:
  1. Ask how a human would behave in the same situation.
  2. Map the model’s behavior to familiar human communication patterns.
  3. Design the interface to match user expectations about waiting, thinking, and updates.
  4. Summarize or shape model reasoning so it feels useful rather than noisy.
- **Example**: For reasoning models, OpenAI chose to show short progress updates rather than a blank wait state or a full babbling chain of thought.

## Core Advice
- **When a product is just barely possible with today’s models**: keep building instead of backing off — because the next model improvement may unlock the product.
- **When planning AI roadmaps**: treat planning as a learning exercise, not a rigid commitment — because the underlying technology changes too fast.
- **When deciding whether to add more scaffolding around model weaknesses**: only add heavy scaffolding for errors that truly cannot be tolerated — because many limitations will disappear soon.
- **When you don’t know if the model is good enough**: create evals for your hero use cases before or alongside building — because evals tell you whether the experience is viable.
- **When improving a specific workflow**: fine-tune on domain-specific examples and use custom evals — because company-specific data often determines real quality.
- **When the task is broad or multi-step**: break it into smaller tasks and use specialized models — because ensembles often outperform a single generic call.
- **When designing waiting or thinking time in the UI**: make it feel like a human thinking aloud — because users understand that better than blank screens or raw internal reasoning.
- **When choosing between chat and a rigid UI**: use chat as the universal baseline, then add structure only when the task is highly prescribed — because chat preserves flexibility and communication bandwidth.
- **When you want better output from an LLM today**: include examples of good inputs and good answers in the prompt — because example-based prompting acts like poor man’s fine-tuning.
- **When you want a model in a specific mindset**: frame the prompt with a role or identity — because role framing can shift the response mode.
- **When hiring PMs for ambiguous AI work**: hire for high agency and comfort with ambiguity — because the work is ill-formed and fast-moving.
- **When building an AI product team**: keep PMs relatively light and empower product-minded engineers and researchers — because too much process slows execution.

## Contrarian Takes
- **Conventional**: Chat is a temporary or inferior interface for AI. → **Their view**: Chat is an excellent baseline interface because it matches how humans naturally communicate and handles a huge range of tasks — because unstructured communication preserves maximum bandwidth.
- **Conventional**: AI teams should heavily scaffold around model weaknesses. → **Their view**: Build right up to the edge of capability and let the next model release remove the limitation — because many weaknesses are temporary.
- **Conventional**: Product roadmaps should be tightly planned and executed over quarters. → **Their view**: In AI, roadmaps are mostly planning tools, not commitments — because the technology changes too quickly.
- **Conventional**: The best AI company should centralize most product and model work internally. → **Their view**: Scale impact through APIs and external builders — because the most valuable use cases are often industry-specific.
- **Conventional**: Prompt engineering is a permanent elite skill everyone must master. → **Their view**: Good AI products should hide that complexity — because prompting is a temporary sharp edge.
- **Conventional**: The best AI products should expose the model’s full chain of thought. → **Their view**: Summarized reasoning is better for most users — because raw babbling is noisy and overwhelming.

## Notable Quotes
> “The AI models that you're using today is the worst AI model you will ever use for the rest of your life.”

> “Plans are useless. Planning is helpful.”

> “Sometimes it's not any one thing, it's just good work consistently over a long period of time.”