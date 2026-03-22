# Benjamin Mann

**Co-founder and tech lead for product engineering** | **Anthropic** | Expertise: ai-strategy, product-management, engineering-management, leadership

## Bio
Benjamin Mann is a co-founder of Anthropic and previously helped architect GPT-3 at OpenAI. He sits at the intersection of frontier model development, product execution, and AI safety, which gives him a rare view into both what the technology can do and how it should be deployed.

His perspective matters because he thinks in systems: model capability, product design, organizational structure, and societal impact. He is especially useful when you need a view on how to build AI products that are both powerful and aligned.

## Signature Frameworks

### Economic Turing Test
- **When to use**: When you need a practical definition of AGI or transformative AI based on real economic impact rather than abstract intelligence claims.
- **Steps**:
  1. Pick a specific job or role.
  2. Contract an agent to do that job for a meaningful period, such as a month or three months.
  3. Evaluate whether you would still choose to hire that agent if you learned it was a machine rather than a person.
  4. Repeat across a basket of jobs weighted by economic value.
  5. If AI passes for a large share of money-weighted jobs, treat that as evidence of transformative AI.
- **Example**: If an agent can pass the test for 50% of money-weighted jobs, Mann argues society should expect major GDP growth, employment disruption, and a new economic era.

### Constitutional AI
- **When to use**: When training AI systems that need to be helpful, harmless, honest, and aligned with explicit values rather than only human raters' preferences.
- **Steps**:
  1. Define a constitution: a set of natural-language principles drawn from sources like human rights documents, privacy principles, and internally generated values.
  2. Have the model generate an initial response to a prompt.
  3. Determine which constitutional principles apply to that response.
  4. Ask the model to critique whether its response violates those principles.
  5. If it does, have the model rewrite the response in light of the principle.
  6. Train the model so it learns to produce the corrected response directly.
- **Example**: If a user asks for a story and the draft includes hate speech or exposes private credentials, the model critiques itself against the constitution and rewrites the answer to comply.

### RLAIF (Reinforcement Learning from AI Feedback)
- **When to use**: When human feedback is too slow or expensive and you want models to improve using AI-generated critiques or evaluations.
- **Steps**:
  1. Generate outputs from a model on a task.
  2. Use AI systems to evaluate those outputs against desired criteria such as correctness, maintainability, or policy compliance.
  3. Use those AI judgments as feedback signals for reinforcement learning.
  4. Iterate so the model improves without requiring humans on every loop.
  5. Add oversight and empirical testing to detect failure modes like hidden goals or deceptive behavior.
- **Example**: Models write code while other models judge whether the code is maintainable, correct, and passes linting; constitutional AI is another form of this approach.

### Build for the Exponential
- **When to use**: When designing AI products in a fast-moving frontier where current model limitations may disappear within months.
- **Steps**:
  1. Study the current capability curve and expected rate of improvement.
  2. Do not optimize only for what works today.
  3. Identify workflows that work partially now but could become reliable soon.
  4. Design products for the future state of model capability, not just the present state.
  5. Choose interfaces and workflows with long-term leverage.
- **Example**: Claude Code succeeded because the team assumed engineers would move beyond autocomplete and IDE-only workflows, and built around the terminal as a flexible environment for broader agentic work.

### Ambitious AI Tool Use
- **When to use**: When individuals or teams want to get outsized value from AI tools instead of using them like slightly better old tools.
- **Steps**:
  1. Use the newest tools directly rather than treating them as minor add-ons.
  2. Ask for ambitious end-to-end changes, not just small assistance.
  3. If the first attempt fails, retry multiple times because outputs are stochastic.
  4. Optionally tell the model what failed so it avoids repeating the same approach.
  5. Expand usage beyond obvious technical domains into legal, finance, and operations.
- **Example**: Anthropic’s legal and finance teams use Claude Code for redlining documents and running BigQuery analyses, and the best users often retry from scratch several times.

## Core Advice
- **When you face uncertainty about how AI will affect your career**: start using frontier AI tools now and learn them through real work rather than waiting for perfect clarity — because the transition is already underway and active users will adapt faster.
- **When you face disappointing results from an AI coding or agent workflow**: retry the same task multiple times, and if needed explicitly tell the model what failed and ask it to try a different approach — because model outputs are stochastic and a fresh attempt often works better than patching a bad one.
- **When you face the temptation to use AI only for small, familiar tasks**: ask for more ambitious end-to-end changes and workflows — because using new tools like old tools leaves most of the leverage untapped.
- **When you face pressure to future-proof your children for an AI-heavy world**: prioritize curiosity, creativity, kindness, and self-led learning over prestige credentials — because AI will commoditize facts while durable human traits remain valuable.
- **When you face a product decision in a rapidly improving AI environment**: build for where model capabilities will be in six to twelve months, not just what works today — because compounding capability gains can make present-day optimizations obsolete quickly.
- **When you face tradeoffs between safety work and product competitiveness**: treat safety and alignment as product advantages rather than separate compliance burdens — because alignment can improve trust, personality, and customer appeal.
- **When you face skepticism about whether AI progress is real because benchmarks seem saturated**: look for harder benchmarks and more ambitious use cases instead of assuming progress has stalled — because many benchmarks are simply too easy.
- **When you face emotionally heavy, long-horizon work**: adopt a sustainable “resting in motion” mindset and work at a marathon pace with like-minded peers — because difficult frontier work requires endurance, not bursts.

## Contrarian Takes
- **Conventional**: AI progress is hitting a plateau and scaling laws are slowing down. → **Their view**: Progress is still accelerating; people are misreading shorter release cycles and benchmark saturation as stagnation — because releases are now monthly or quarterly and many benchmarks saturate quickly.
- **Conventional**: Safety work slows AI companies down and makes them less competitive. → **Their view**: Safety and alignment can improve product quality and create competitive advantage — because Claude’s personality, lower sycophancy, and trustworthiness are direct product benefits.
- **Conventional**: AGI should be defined by abstract human-level intelligence across all tasks. → **Their view**: A better lens is transformative AI measured by economic substitution and societal impact — because real hiring decisions reveal whether AI is actually useful.
- **Conventional**: Software-only AI is not that dangerous until robots arrive. → **Their view**: Software systems alone can already create serious real-world harm — because cyberattacks, power-grid disruption, and bio-risk uplift do not require embodiment.
- **Conventional**: To contribute meaningfully to AI safety, you need to be an AI researcher. → **Their view**: Many non-research roles are pivotal to safe AI progress — because product, finance, operations, and even food services help frontier labs function and influence outcomes.
- **Conventional**: The best way to prepare kids for the future is elite schools, credentials, and traditional achievement ladders. → **Their view**: Those markers may matter less than curiosity, creativity, kindness, and emotional development — because AI will reduce the value of memorized facts and prestige signaling.

## Notable Quotes
> “Once we get to superintelligence, it will be too late to align the models probably.”

> “People who use the new tools as if they were old tools tend to not succeed.”

> “It's going to be much weirder very soon.”