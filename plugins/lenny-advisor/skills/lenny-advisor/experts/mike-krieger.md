# Mike Krieger

**Chief Product Officer** | **Anthropic** | Expertise: AI product strategy, product design, engineering management, consumer product building

## Bio
Mike Krieger is the Chief Product Officer at Anthropic and the co-founder of Instagram. He brings rare experience spanning consumer product creation, product strategy, and engineering leadership, now applied to frontier AI systems.

His perspective matters because he thinks about AI not as a feature layer, but as a full product stack: model capability, context, workflow design, and human agency. He is especially useful when you need to decide how to build durable AI products around fast-changing model capabilities.

## Signature Frameworks

### Model intelligence + context/memory + applications/UI
- **When to use**: When designing an AI product or platform and deciding where to invest product effort.
- **Steps**:
  1. Improve model intelligence through research and post-training.
  2. Provide the right context and memory so the model can reason over relevant information.
  3. Build applications and UI that make the capability discoverable and usable.
  4. Ensure the three layers work together rather than optimizing any one in isolation.
- **Example**: MCP helps Claude use Slack and Google Drive context to answer product strategy questions better than web-only context.

### Minimum viable strategy for AI-native teams
- **When to use**: When your team is moving faster because AI is generating much more code and you need to keep people aligned without over-prescribing.
- **Steps**:
  1. Define the smallest strategy needed to orient the team.
  2. Let builders explore at the edge of model capabilities.
  3. Surface and resolve upstream alignment issues early.
  4. Anticipate downstream bottlenecks in review, merge, and release.
  5. Continuously adjust the process as AI changes throughput.
- **Example**: At Anthropic, AI-generated code shifted the bottleneck from coding to decision-making/alignment and merge queues, forcing a re-architecture of the release process.

### Build at the edge, then measure against real usage
- **When to use**: When building on top of frontier models and trying to create durable AI products.
- **Steps**:
  1. Push the model on hard, real customer problems.
  2. Expect the model to fail at the edge and use that to learn.
  3. Create repeatable evaluation loops using traces, A/B tests, and internal benchmarks.
  4. Compare model upgrades against actual customer workflows, not just abstract benchmarks.
- **Example**: Cursor, Harvey, and Manus keep trying hard use cases until a new model version suddenly makes the product viable.

### Product + research embedding loop
- **When to use**: When building AI products where model behavior and product experience are tightly coupled.
- **Steps**:
  1. Embed product people directly with researchers and post-training teams.
  2. Use product feedback to shape model behavior, not just UX.
  3. Feed product learnings back into research and fine-tuning.
  4. Revise the product experience based on what the model can now do better.
- **Example**: Artifacts improved when Claude Code skills and product people worked together on post-training and product revamps, rather than just prompting the model more.

### MCP as a protocol for reusable context
- **When to use**: When an AI system needs access to external tools, documents, or workflows in a repeatable way.
- **Steps**:
  1. Identify repeated one-off integrations that are being rebuilt from scratch.
  2. Abstract them into a protocol instead of custom integrations.
  3. Expose context sources and actions through a standard interface.
  4. Make the same integration usable across models and products.
- **Example**: Anthropic turned internal integration work into MCP so Claude could access Slack, Google Drive, and other systems in a reusable way.

## Core Advice
- **When you want better AI output from Claude or similar models**: Do the opposite of your default tone or style — if you would normally be polite, ask it to be brutal; if you would normally be vague, ask it to think hard — because contrastive prompting breaks the model out of generic responses.
- **When you need a stronger critique of a strategy or plan**: Ask the model to roast it rather than merely improve it — because blunt instructions surface issues softer prompts miss.
- **When you are trying to prototype a product idea early**: Use Claude and artifacts to create a functional demo before formal engineering work begins — because early prototypes make ideas tangible and shift the process earlier.
- **When your team is blocked by too much AI-generated code**: Rework the merge/review pipeline before adding more headcount — because the bottleneck often moves from coding to review and release.
- **When you are deciding what product work to prioritize in an AI company**: Focus on the smallest strategy that gives builders room to explore rather than over-specifying the roadmap — because AI changes quickly and over-strategy slows teams down.
- **When you are building an AI product for a specific industry**: Learn the domain deeply and design around the actual workflow, even if it looks weird from the outside — because durable AI startups win by fitting real specialist work.
- **When you are building on frontier models and the model seems almost good enough**: Keep pushing the edge and build a repeatable evaluation process for each model upgrade — because the best teams know exactly when a new model unlocks the product.
- **When you are designing an AI product experience**: Optimize for user agency, not just convenience or conversation length — because the right product balances model autonomy with human independence.
- **When you are building metrics for an AI assistant**: Measure whether the product helped the user get work done, not just engagement or chat length — because short interactions can be highly valuable and long ones can be misleading.
- **When you are choosing where to compete as a challenger brand**: Lean into your unique strengths instead of trying to beat the market leader at its own game — because Anthropic should focus on builders and agentic workflows, not consumer mindshare.
- **When you are deciding whether to shut down a struggling startup or product**: Call it when the product no longer has its own compounding momentum — because continuing can waste years that could go to better opportunities.
- **When you are trying to help kids or learners prepare for an AI-heavy future**: Encourage curiosity, inquiry, and independent thinking rather than defaulting to AI for every answer — because preserving cognition matters.

## Contrarian Takes
- **Conventional**: AI product teams should optimize for more conversation and more engagement. → **Their view**: The right goal is whether the model actually helped the user accomplish something — because a good conversation may be very short.
- **Conventional**: The main bottleneck in software development is engineering throughput. → **Their view**: With AI writing most code, bottlenecks move to alignment and merge/review/release systems — because code generation is no longer the slowest step.
- **Conventional**: AI companies should primarily chase consumer mindshare. → **Their view**: A challenger should focus on what it is uniquely good at, like builders, developers, and agentic workflows — because consumer adoption is hard to force.
- **Conventional**: The best way to build AI products is to wrap a model with polished UX. → **Their view**: Highest leverage comes from embedding product people with researchers and shaping the model itself — because product and model behavior are inseparable.
- **Conventional**: More integrations should be built as custom product features. → **Their view**: Integrations should be standardized into protocols like MCP — because reusable context is more scalable and composable.
- **Conventional**: A successful founder should keep a struggling startup alive as long as possible. → **Their view**: Shutting it down early can be right if the product is not compounding — because sunk cost should not dominate strategy.

## Notable Quotes
> “I had the very bizarre experience of I had two tabs open. It was AI 2027, and my product strategy, and it was this moment where I'm like, ‘Wait, am I the character in the story?’”

> “I think there's room for several generationally important companies to be built in AI right now.”

> “A small request. When you're making hard product decisions, remember the quiet moments matter too.”