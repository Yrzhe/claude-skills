# Karina Nguyen

**AI researcher on Frontier Product Research** | **OpenAI** | Expertise: ai-strategy, product-management, design, go-to-market

## Bio
Karina Nguyen works at the intersection of frontier model training and product design, with a focus on making AI systems behave reliably in real user workflows. At OpenAI, she has contributed to product-oriented model training and post-training methods for features like Canvas, tasks, and the o1 reasoning model; previously at Anthropic, she worked on post-training, evaluations, Claude 3, and product experiences like document upload and long-context workflows.

Her perspective matters because she has seen both sides of the stack: how models are shaped, and how those models become useful products. She is especially valuable when you need to turn vague AI capability into a concrete, shippable experience.

## Signature Frameworks

### Behavior-first synthetic training for AI products
- **When to use**: When building a new AI product feature and you need the model to reliably exhibit a few core behaviors before broad launch.
- **Steps**:
  1. Define the product's core behaviors in concrete terms.
  2. Create synthetic examples that demonstrate those behaviors.
  3. Train the model on those examples rather than waiting for large amounts of human-labeled data.
  4. Measure progress with robust evals tied to the intended behavior.
  5. Launch in beta, collect real user feedback, and shift the synthetic data distribution toward real usage patterns.
- **Example**: For Canvas, the team focused on three behaviors: when to trigger Canvas, how to edit a document precisely versus rewrite it, and how to generate useful comments on a document. They used o1 and synthetic data to simulate conversations, generate documents, and train commenting/editing behavior.

### AI product eval design
- **When to use**: When shipping AI features where correctness is probabilistic and you need a repeatable way to measure whether the model is improving.
- **Steps**:
  1. List representative user scenarios and expected outcomes.
  2. Create deterministic pass/fail evals where possible.
  3. Add human preference evals for subjective quality dimensions.
  4. Track whether new models beat prompted baselines and previous versions.
  5. Watch for regressions in other capabilities while optimizing a specific behavior.
- **Example**: For Canvas, PMs could create labeled examples of conversations that should trigger Canvas versus not trigger it. For tasks, deterministic evals checked whether a requested time like “7:00 PM” was extracted and scheduled correctly.

### Prompting as product prototyping
- **When to use**: When exploring new AI product ideas before investing in full engineering implementation.
- **Steps**:
  1. Prototype the intended behavior directly through prompts.
  2. Demo the experience internally or to early users.
  3. Observe where the model already creates value and where it breaks.
  4. Use those observations to define the product spec, tool schema, or training plan.
  5. Only then invest in engineering and model training.
- **Example**: At Anthropic, Karina prototyped file uploads and long-context workflows directly in the browser before they became productized. She also described using prompting to prototype personalized starter prompts and conversation title generation.

### Tool-spec design for agent features
- **When to use**: When building agentic features that require the model to convert natural language into structured actions.
- **Steps**:
  1. Start from a user request and identify the minimum information needed to complete the task.
  2. Design a structured schema for the extracted fields.
  3. Teach the model how to map user language into that schema.
  4. Add follow-up behavior for missing information.
  5. Evaluate whether the agent completes the task correctly and asks clarifying questions when needed.
- **Example**: For tasks, the team designed a JSON-like tool spec so the model could extract time, recurrence, and instruction from prompts like “Remind me to go to lunch at 8:00 AM tomorrow” or “Every day I want to learn about the latest AI news.”

## Core Advice
- **When you face the challenge of building a new AI feature with unclear user behavior**: Do a behavior-first breakdown: identify the 2-3 core behaviors the model must get right, then train and evaluate specifically for those — because AI products fail when teams optimize vaguely.
- **When you face uncertainty about whether an AI feature is actually improving**: Do explicit eval design with both deterministic checks and human preference comparisons — because without evals, teams rely on anecdotes.
- **When you face pressure to collect lots of human-labeled data before shipping**: Do synthetic training first for rapid iteration, then use real user feedback after beta to refine the model — because synthetic data is cheaper, faster, and scalable.
- **When you face a blank page on a new AI product idea**: Do prompt-based prototyping before writing a full PRD or building the system — because prompting lets you simulate the experience and discover edge cases early.
- **When you face career uncertainty as AI gets better at hard skills like coding and writing**: Do deliberate skill-building in creativity, prioritization, communication, listening, and collaboration — because these human-centered skills are harder to automate.
- **When you face the temptation to optimize a model for one narrow product behavior**: Do regression checks across broader intelligence and capability evals before declaring success — because improving one behavior can hurt others.
- **When you face the need to build AI agents that act on behalf of users**: Do extra work on intent understanding and follow-up questions instead of only optimizing task completion — because trust depends on correctly modeling user intent.
- **When you face a product category where the model is improving quickly but not yet fully capable**: Do product design for the future model, not just the current one — because the right form factor can unlock value as models improve.

## Contrarian Takes
- **Conventional**: Model training is mostly a brute-force science problem of scale, compute, and data. → **Their view**: Model training is more an art than a science, especially in post-training and behavior shaping — because data quality, debugging, and trade-offs matter as much as scale.
- **Conventional**: AI progress will stall because frontier labs are running out of internet data. → **Their view**: The real frontier is post-training on effectively infinite tasks — because web search, computer use, writing, and tool use can keep scaling.
- **Conventional**: Hard skills will remain the safest moat for product and engineering careers. → **Their view**: Soft skills like creativity, listening, prioritization, and management may become more valuable — because models are rapidly absorbing execution-heavy work.
- **Conventional**: Strategy is one of the last things AI will be able to do well. → **Their view**: AI can become very strong at strategy — because strategy is largely about synthesizing many inputs and connecting dots.
- **Conventional**: The main challenge in AI products is model capability itself. → **Their view**: Form factor and product experience can be as important as raw model capability — because the interface must match how humans actually work.

## Notable Quotes
> “Model training is more an art than a science.”

> “Prompting is a new way of product development or prototyping for designers and for product managers.”

> “We went from personal computers to personal model basically here.”