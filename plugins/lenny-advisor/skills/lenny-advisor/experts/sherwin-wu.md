# Sherwin Wu

**Head of Engineering for OpenAI’s API and Developer Platform** | **OpenAI** | Expertise: AI developer platforms, engineering leadership, agentic workflows, B2B SaaS

## Bio
Sherwin Wu leads engineering for OpenAI’s API and developer platform, so he sees firsthand how startups and enterprises are actually building with frontier models. His perspective matters because he combines platform-level visibility with hands-on product and engineering judgment, especially around what AI can do now versus what it will do next.

He previously worked at Opendoor on house pricing models, and now focuses on scaling AI products, engineering teams, and the ecosystem around agentic workflows. He is especially useful when you need a pragmatic view on AI product strategy, engineering management, and how to adopt AI inside real organizations.

## Signature Frameworks

### Build for where the models are going, not where they are today
- **When to use**: When deciding product direction in a fast-moving AI market
- **Steps**:
  1. Identify the capability your product needs to be truly valuable.
  2. Assess whether the model is already close enough to make the product feel useful.
  3. Design the product around the future model capability, not current limitations.
  4. Accept that the product may feel incomplete until the model improves.
  5. Re-evaluate as model quality jumps and remove scaffolding that is no longer needed.
- **Example**: A product that is 80% of the way there today may become excellent once a newer model like o3 or 5.2 lands.

### Bottoms-up AI adoption with top-down support
- **When to use**: When rolling out AI tools inside a company
- **Steps**:
  1. Get executive buy-in and budget for AI tools.
  2. Find employees who are naturally excited and technically adjacent to the work.
  3. Create a tiger team or evangelist group to explore workflows deeply.
  4. Have that team share best practices, run hackathons, and teach others.
  5. Let adoption spread from real use cases rather than mandate it from above.
- **Example**: OpenAI saw stronger adoption when employees could use Codex directly in their own work, not just when leadership declared the company should be AI-first.

### Manager as unblocker and force multiplier
- **When to use**: When leading engineers or other high-output knowledge workers
- **Steps**:
  1. Spend the majority of your time with top performers.
  2. Keep them unblocked and make sure they feel heard and productive.
  3. Look around corners for organizational or process blockers before they hit.
  4. Prepare the resources they will need in advance.
  5. Use AI tools to surface blockers, context, and likely future constraints.
- **Example**: Sherwin compares the manager to a surgical assistant who has the scalpel ready before the surgeon asks for it.

### Agent debugging through context enrichment
- **When to use**: When an AI coding agent fails to do what you want
- **Steps**:
  1. Assume the failure may be due to missing or underspecified context.
  2. Add documentation, comments, or repository files that encode tribal knowledge.
  3. Use structured artifacts like `.md` files, `AGENTS.md`, or Skills.
  4. Improve code structure so the model can infer intent more reliably.
  5. Iterate until the agent can complete the task without human escape hatches.
- **Example**: A 100% Codex-written codebase forced the team to solve failures by adding more repository context instead of just manually fixing the code.

### Layered platform for building agents
- **When to use**: When building AI products on OpenAI’s stack
- **Steps**:
  1. Start with the low-level Responses API for maximum flexibility.
  2. Use the Agents SDK when you want orchestration, sub-agents, and guardrails.
  3. Add AgentKit and widgets for UI and deployment support.
  4. Use evals to measure whether the workflow is actually working.
  5. Choose the lowest layer that still gives you the abstraction you need.
- **Example**: A developer can build a long-running agent directly with Responses API, or use Agents SDK plus AgentKit for a more opinionated end-to-end setup.

## Core Advice
- **When the AI market is changing quickly**: build for the next model generation, not the current one — because today’s limitations are temporary and will likely disappear.
- **When an agent keeps failing**: treat it as a context problem first — because most failures come from missing information, not model incapability.
- **When code review is too slow**: use AI to pre-review PRs — because it can compress human review into a much shorter, higher-value pass.
- **When release friction is slowing engineers down**: automate linting, CI fixes, and deployment steps — because getting code into production is often the real bottleneck.
- **When you want more engineering throughput**: let top performers lean hardest into AI tools — because high-agency people compound the gains fastest.
- **When managing in an AI-heavy environment**: spend more than half your time with your top 10% performers — because they are most likely to become exceptional with AI.
- **When rolling out AI across a company**: pair executive sponsorship with a bottom-up evangelist team — because mandates alone rarely change workflows.
- **When deciding whether to follow customer requests**: balance feedback with your own view of model trajectory — because customers often ask for scaffolding that will soon be obsolete.
- **When worried OpenAI will copy your startup**: focus on building something people love — because most startups fail from weak product-market fit, not platform competition.
- **When choosing what to automate**: target repeatable business processes before creative work — because SOP-driven operations are often the most automatable.
- **When trying to keep up with AI**: learn one or two tools deeply — because breadth is overwhelming and depth is what creates leverage.
- **When building on AI today**: use the simplest abstraction that works — because models keep absorbing scaffolding over time.

## Contrarian Takes
- **Conventional**: You should always listen closely to customers when building AI products. → **Their view**: Customer feedback can mislead you if it anchors you to today’s model limitations — because the model may soon make those requests irrelevant.
- **Conventional**: More scaffolding, agent frameworks, and vector stores are the path to better AI products. → **Their view**: The models will often eat your scaffolding for breakfast — because simpler systems can outperform elaborate layers as models improve.
- **Conventional**: AI adoption should be driven primarily from the top down. → **Their view**: Top-down mandates without bottom-up champions usually fail — because people need hands-on examples and peer learning.
- **Conventional**: OpenAI will inevitably squash startups building on its platform. → **Their view**: Most startups fail because they don’t resonate, not because the platform copied them — because the market is large and OpenAI sees itself as a platform company.
- **Conventional**: Engineering managers mainly need to manage people and process as before. → **Their view**: AI may let managers become much higher leverage and manage far larger teams — because AI can handle more context gathering and routine work.
- **Conventional**: The biggest AI opportunity is in software engineering productivity. → **Their view**: Business process automation may be an even larger opportunity — because much of the economy is repeatable and SOP-driven.

## Notable Quotes
> “The models will eat your scaffolding for breakfast.”

> “This is the worst the models will ever be.”

> “It literally feels like we're wizards casting all these spells and these spells are kind of like going out and doing things for you.”