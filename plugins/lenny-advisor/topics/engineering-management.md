# Engineering Management

## Overview
Engineering management in the AI era is about building teams, systems, and product processes that can adapt quickly while still shipping reliably. The core challenge is no longer just managing people and code; it is managing feedback loops, autonomy, trust, and cross-functional execution as AI changes how software gets built.

## Key Frameworks

### Agency-Control Progression (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When building AI agents or AI-assisted workflows where reliability is uncertain and full autonomy would be risky.
- **Steps**:
  1. Start with high human control and low AI agency.
  2. Use the AI first for suggestions, drafts, or routing rather than autonomous actions.
  3. Collect human feedback and observe failure modes.
  4. Increase autonomy gradually only after the system earns trust.
  5. Expand scope from assistive actions to end-to-end execution.
- **Example**: In customer support, start with AI suggesting responses to agents, then showing answers directly to customers, and only later allowing refunds or feature requests.

### Continuous Calibration, Continuous Development (CCCD) (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When building AI products that must improve over time because user behavior and model behavior are both non-deterministic.
- **Steps**:
  1. Scope the capability and curate representative input/output examples.
  2. Align PMs, engineers, and subject matter experts on expected behavior.
  3. Set up the application and define evaluation metrics.
  4. Deploy and monitor real usage.
  5. Analyze behavior and spot unexpected error patterns.
  6. Apply fixes and add or refine evaluation metrics where needed.
  7. Repeat the loop while gradually increasing AI agency.
- **Example**: Created after end-to-end support agents became unmanageable due to hot fixes and emerging failures.

### Actionable Feedback Loop for AI Products (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When teams need to improve AI reliability after launch and decide between evals, production monitoring, or both.
- **Steps**:
  1. Create a small trusted test set for known critical behaviors.
  2. Deploy with production monitoring for explicit and implicit user signals.
  3. Inspect traces that indicate failures or dissatisfaction.
  4. Identify recurring failure patterns.
  5. Turn important recurring failures into evaluation datasets or metrics.
  6. Keep monitoring production because new failures will continue to emerge.
- **Example**: If users regenerate an answer instead of downvoting it, that implicit signal should trigger investigation.

### Teammate-first Agent Adoption (Alexander Embiricos)
- **When to use**: When introducing coding agents into real engineering workflows and trying to build trust with users over time.
- **Steps**:
  1. Start with interactive use inside the IDE or CLI rather than fully remote delegation.
  2. Have the agent first understand the codebase and answer questions.
  3. Collaborate on an approach or plan before asking it to implement.
  4. Let it execute tasks with access to the local environment and dependencies.
  5. Gradually configure permissions, tools, and validation so it can handle longer, more autonomous tasks.
  6. Move toward delegation and eventually proactivity once trust and setup are in place.
- **Example**: Treat Codex like a smart intern: work side by side first, then give it more access over time.

### Plan-driven Long-task Execution (Alexander Embiricos)
- **When to use**: When asking Codex to work on complex or long-running coding tasks that need to stay coherent over time.
- **Steps**:
  1. Collaborate with Codex to write a plan.md or equivalent planning document.
  2. Break the work into verifiable steps.
  3. Review and refine the plan until you are confident in it.
  4. Ask Codex to execute against that plan.
  5. Use validation checkpoints so the agent can confirm progress and continue longer.
- **Example**: A co-authored markdown plan with verifiable steps lets the agent work much longer.

### Integrated Model-Harness-Product Optimization (Alexander Embiricos)
- **When to use**: When building agentic AI products where model quality alone is not enough to deliver strong user outcomes.
- **Steps**:
  1. Train a model optimized for a specific task environment.
  2. Build the API layer to support agent-specific behaviors.
  3. Design the harness/tooling layer with clear opinions about how the model should operate.
  4. Iterate product and research together rather than separately.
  5. Add cross-stack capabilities like context compaction that require coordination across all layers.
- **Example**: Codex compaction required changes in the model, API, and harness so the agent could keep working after exceeding context.

### End-to-end Software Creation Platform (Amjad Masad)
- **When to use**: When you want to reduce friction for technical and non-technical users by combining coding, runtime, database, deployment, and iteration in one place.
- **Steps**:
  1. Start with a natural-language description of the app you want to build.
  2. Let the system choose or configure the stack, runtime, packages, and database.
  3. Generate an initial working prototype end-to-end, including backend and deployment setup.
  4. Inspect the code and progress transparently while the AI builds.
  5. Test the app, ask the AI to fix issues, and iterate on features or UI.
  6. Deploy directly once the prototype is usable.
- **Example**: Replit built a Node.js feature-request dashboard with Postgres, UI, and deployment-ready setup in minutes.

### AI Adoption Maturity Path (Asha Sharma)
- **When to use**: When rolling out AI across an enterprise and trying to move from experimentation to measurable business impact.
- **Steps**:
  1. Make everyone AI fluent by embedding copilots or AI tools into daily workflows.
  2. Apply AI to improve an existing process, such as support, fraud, or operations.
  3. Measure the impact and connect it to P&L or intrinsic business value.
  4. Use proven wins to drive growth, retention, customer experience, or new categories.
- **Example**: Start with daily workflow use, then process improvement, then growth inflection.

## Decision Guide
- If you are under pressure to launch a fully autonomous agent quickly, consider **Agency-Control Progression** because trust and reliability should be earned before autonomy expands — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If your AI product behaves unpredictably in the wild, use **CCCD** because production behavior must be calibrated continuously — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you are unsure whether evals are enough, use **Actionable Feedback Loop for AI Products** because offline tests catch known risks while production monitoring reveals unknown failures — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If leadership is skeptical about AI, do hands-on learning and create dedicated time for leaders to rebuild intuition — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If subject matter experts fear replacement, frame the work as augmentation and involve them in behavior definition — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If your enterprise workflow is messy, analyze the workflow deeply before adding agents — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If a vendor promises instant ROI from a one-click agent, be skeptical and look for a learning pipeline and feedback flywheel — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you are introducing a coding agent to a team, start in the IDE or CLI and treat it like a teammate — per **Alexander Embiricos**.
- If a coding task is long or complex, co-write a plan first so the agent can stay coherent and verifiable — per **Alexander Embiricos**.
- If a new user is evaluating a coding agent, try a hard bug, codebase understanding, and planning in parallel — per **Alexander Embiricos**.
- If AI output is creating too much review burden, redesign the experience to empower the human and reduce validation work — per **Alexander Embiricos**.
- If model quality is plateauing but product outcomes are weak, optimize the full stack: model, API, and harness — per **Alexander Embiricos**.
- If you need to validate a product idea quickly, prototype it yourself with AI before asking engineering for roadmap commitment — per **Amjad Masad**.
- If your team is blocked by generic SaaS, build a custom internal tool with AI instead — per **Amjad Masad**.
- If your roadmap is unstable because AI is changing fast, keep planning flexible and re-prioritize aggressively — per **Amjad Masad**.
- If you are rolling out AI company-wide, first make the org fluent, then improve one real process, then scale to growth use cases — per **Asha Sharma**.

## Expert Consensus
- AI products improve through **feedback loops**, not one-time launches.
- **Production monitoring matters as much as evals** because real users reveal new failure modes.
- **Autonomy should increase gradually** as trust, validation, and observability improve.
- The bottleneck is often **workflow design and system integration**, not just model intelligence.
- In AI-native organizations, **product, engineering, design, and operations converge** around the loop of build, measure, and improve.

## Points of Debate
- **Full autonomy first** (conventional wisdom) vs. **gradual autonomy** (Aishwarya Naresh Reganti + Kiriti Badam): one side prioritizes speed; the other prioritizes trust, safety, and learning.
- **Evals are enough** vs. **evals plus production monitoring** (Aishwarya Naresh Reganti + Kiriti Badam): one side assumes test coverage can be sufficient; the other argues real usage always exposes new failures.
- **Model-first optimization** vs. **full-stack optimization** (Alexander Embiricos): one side focuses on model intelligence; the other says harness, API, and workflow matter just as much.
- **Specs-driven development** vs. **fluid communication-driven workflows** (Alexander Embiricos): one side expects formal specs to dominate; the other expects more conversational, agent-assisted collaboration.
- **Implementation speed as the main moat** vs. **problem selection and taste as the moat** (Aishwarya Naresh Reganti + Kiriti Badam): one side values building faster; the other values choosing the right problem and experience.
- **Multi-agent systems as the default answer** vs. **supervisor patterns and simpler control** (Aishwarya Naresh Reganti + Kiriti Badam): one side favors distributed agents; the other warns about coordination and guardrail complexity.

## Key Metrics & Benchmarks
- **Only 8% of U.S. workers use AI daily** — Gallup poll; shows adoption is still early.
- **Zapier sales reps save 10 hours per week on lead research** — a concrete productivity gain from AI-assisted workflows.
- **Duolingo went from 100 courses in 12 years to 150 courses in 12 months** — shows AI can dramatically accelerate content creation.
- **Intercom reports about a 20% year-over-year durable improvement in merged pull requests** — a proxy for AI-assisted engineering productivity.
- **Duolingo gave every employee $300 to try AI tools, courses, and subscriptions** — a practical enablement benchmark.
- **Zapier’s live demos attract over 60 employees every week** — a sign that internal AI education can be operationalized.
- **Over 1,500 merged PRs / averaging 10 per day** — Devin contributions at Gumroad, showing agentic coding can reach meaningful production volume.
- **Over 6 million lines** — size of Nubank’s ETL monolith that Devin helped migrate.
- **Tens of thousands of people** — production users of Devin, indicating real-world adoption beyond demos.

## Notable Quotes
- “Start with minimal autonomy and increase agency only after the system earns trust.” — Aishwarya Naresh Reganti + Kiriti Badam
- “The real advantage is building the right flywheels to improve over time.” — Aishwarya Naresh Reganti + Kiriti Badam
- “The biggest blocker is not model intelligence; it is human typing speed and human validation speed.” — Alexander Embiricos