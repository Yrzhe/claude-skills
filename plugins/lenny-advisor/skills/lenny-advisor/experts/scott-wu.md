# Scott Wu

**Co-founder and CEO** | **Cognition** | Expertise: ai-strategy, engineering-management, product-management, strategy

## Bio
Scott Wu leads Cognition, the company behind Devin, an autonomous AI software engineer built to work inside real engineering teams. His perspective matters because he thinks about AI not as a demo or chatbot, but as a workflow-changing system that has to fit into codebases, tools, and team habits.

He brings a rare mix of competitive programming depth, product thinking, and startup execution. That makes him especially useful for anyone trying to understand how AI will reshape software engineering, team structure, and what great product design looks like in an AI-native world.

## Signature Frameworks

### Treat Devin like a junior engineer workflow
- **When to use**: When onboarding teams to an AI coding agent or trying to get reliable output from Devin.
- **Steps**:
  1. Start with small, well-defined tickets instead of big ambiguous projects.
  2. Set up the repository, test environment, linting, CI, and a dedicated VM for Devin.
  3. Give Devin a first pass asynchronously and let it work on the bulk of the task.
  4. Jump in only for the 10-20% that needs human judgment, architecture decisions, or final polish.
  5. Review the output, merge if correct, and give feedback so Devin learns over time.
- **Example**: Use Devin on a bug fix or a small UI change first, then expand to larger tasks once it understands the codebase and team conventions.

### Asynchronous multi-Devin execution
- **When to use**: When a team wants to maximize throughput and parallelize engineering work.
- **Steps**:
  1. Break the day’s work into multiple independent tasks.
  2. Assign each task to a separate Devin instance.
  3. Let Devins work in parallel while humans stay available for steering.
  4. Intervene only when a task needs scoping, architecture decisions, or final verification.
  5. Use the time saved to focus on higher-level product and architecture decisions.
- **Example**: At Cognition, engineers often work with up to five Devins at once, and Devin accounts for about a quarter of PRs.

### Well-defined task selection
- **When to use**: When deciding what to hand to an AI agent versus what to keep human-led.
- **Steps**:
  1. Choose tasks that are easy to verify and easy to test.
  2. Prefer bug fixes, small front-end changes, testing, and documentation.
  3. Avoid vague problem statements; convert them into concrete tasks.
  4. Provide enough context for Devin to scope the work correctly.
  5. Use human review for tasks with high ambiguity or complex trade-offs.
- **Example**: “Add Lenny’s newsletter link to the Devin homepage” is a strong Devin task because the success criteria are obvious.

### Layered codebase understanding
- **When to use**: When working in large repositories or onboarding new engineers.
- **Steps**:
  1. Start with a high-level architectural view of the codebase.
  2. Zoom into relevant components only as needed.
  3. Use indexed knowledge, wiki-style summaries, and code search to answer questions.
  4. Ask targeted questions about specific subsystems or implementation details.
  5. Use the representation to scope tasks and reduce context-switching.
- **Example**: Devin Wiki can explain how a large codebase is structured, then answer a focused question about a specific implementation detail.

### Build the product interface around agent limitations
- **When to use**: When designing AI products that need to be usable by real teams.
- **Steps**:
  1. Assume users need to learn a new interaction model, not just a smarter chatbot.
  2. Add planning, feedback, and handoff points to the workflow.
  3. Let users inspect, steer, and interrupt the agent at any time.
  4. Expose confidence and intermediate reasoning where useful.
  5. Iterate on both capability and UX together.
- **Example**: Devin evolved from a simple handoff model into a workflow where users can plan with it, jump in mid-task, and touch up its code.

### Focus on stickiness, not just moat
- **When to use**: When thinking about defensibility in fast-moving AI markets.
- **Steps**:
  1. Build a product that improves as the user and team use it more.
  2. Accumulate codebase, workflow, and organizational knowledge over time.
  3. Make the product deeply embedded in team collaboration surfaces.
  4. Increase switching costs through familiarity and shared context, not lock-in alone.
  5. Keep improving usefulness so users want to stay.
- **Example**: Devin becomes more valuable as it learns a team’s codebase, process, and conventions, and as multiple teammates collaborate through it.

## Core Advice
- **When introducing Devin or any coding agent to a team**: Treat it like a new junior engineer and start with small, well-defined tickets — because agents perform best when the work is concrete and verifiable.
- **When an AI agent is failing because it lacks context or tooling**: Set up repo access, test environment, linting, CI, and a dedicated VM first — because the agent needs the same feedback loops a human engineer uses.
- **When you want to maximize engineering throughput**: Run multiple Devins in parallel — because parallel task execution beats a single synchronous workflow.
- **When a task is ambiguous or hard to verify**: Keep the human in the loop for scoping, architecture choices, and final review — because Devin is strongest on execution, not judgment.
- **When deciding whether to hand a task to Devin**: Prefer bug fixes, small UI changes, testing, and documentation — because these have clear success criteria and fast feedback.
- **When onboarding a new engineer to a large codebase**: Use codebase wiki/search tools to answer architecture questions — because layered understanding reduces context-switching.
- **When designing an AI product workflow**: Add planning, feedback, and interruption points — because users need steering, not black-box automation.
- **When worried about competition in AI**: Optimize for stickiness through learning and workflow integration — because AI markets are easy to enter, but hard to make indispensable.
- **When deciding what skills engineers should keep developing**: Double down on architecture, systems thinking, and precise problem definition — because AI shifts value toward deciding what to build.
- **When learning to code in the AI era**: Still learn fundamentals like databases, networking, and runtime behavior — because understanding layers matters more as syntax becomes easier.
- **When trying to get team adoption of a new AI tool**: Start with a few enthusiastic early adopters — because visible wins create momentum for broader rollout.
- **When building a startup in a fast-moving market**: Stay close to customers, move fast, hire exceptionally well, and think ahead — because AI markets change quickly.

## Contrarian Takes
- **Conventional**: AI coding tools will reduce the need for software engineers. → **Their view**: AI will likely create more programmers and more engineers, not fewer — because easier programming expands demand faster than efficiency gains.
- **Conventional**: The main job of an AI coding product is to maximize raw model intelligence. → **Their view**: The harder problem is teaching the model real engineering conventions and designing the workflow around them — because integration matters as much as capability.
- **Conventional**: Moats are the key to winning in AI. → **Their view**: Stickiness matters more than a hard moat — because usefulness, learning, and workflow embedding are what keep users.
- **Conventional**: AI products should stay narrow. → **Their view**: Generative AI naturally pushes products toward broader workflows — because adjacent surfaces like search, wiki, Slack, and Linear become part of the job.
- **Conventional**: Engineering work will become mostly automated execution. → **Their view**: Human value shifts toward architecture, problem definition, and trade-offs — because AI removes repetition, not judgment.
- **Conventional**: Management is the right metaphor for supervising AI agents. → **Their view**: Working with Devin is closer to being an architect — because the task is choosing abstractions and handoffs, not managing people.

## Notable Quotes
> “I really think that programming is only going to become more and more important as AI gets more powerful.”

> “We want to make Devin part of your flow, not it losing control.”

> “I think it's often less about moats and more about stickiness.”