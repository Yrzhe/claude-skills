# Boris Cherny

**Head of Claude Code** | **Anthropic** | Expertise: ai-strategy, engineering-management, product-management, go-to-market

## Bio
Boris Cherny leads Claude Code at Anthropic and has been central to turning AI coding agents into a practical, mainstream workflow. He brings a rare mix of deep engineering judgment, product intuition, and platform thinking from prior leadership roles at Meta/Instagram and from authoring a major TypeScript book.

His perspective matters because he is building at the frontier where model capability, product design, and developer behavior meet. He is especially useful when you need to understand how AI-native products should be designed as models rapidly improve.

## Signature Frameworks

### Latent Demand
- **When to use**: When deciding what product to build next or how to discover high-signal user needs from unexpected behavior.
- **Steps**:
  1. Observe how users are already misusing or hacking your product to accomplish something valuable.
  2. Treat repeated off-label usage as evidence of unmet demand rather than user error.
  3. Build a more purpose-built workflow around that behavior.
  4. In AI products, also observe what the model itself is trying to do and reduce friction around those behaviors.
- **Example**: Anthropic noticed people using Claude Code for non-coding tasks like growing tomato plants, analyzing genomes, recovering photos, and SQL analysis in the terminal. That latent demand led to Cowork.

### Build for the Model Six Months Out
- **When to use**: When building AI-native products in a fast-moving model environment where current capabilities are improving rapidly.
- **Steps**:
  1. Identify workflows that are almost possible today but still feel slightly too weak or unreliable.
  2. Design the product around the future state of model capability rather than current limitations.
  3. Accept weaker product-market fit in the short term while the model catches up.
  4. Be ready to capitalize when the next model inflection point arrives.
- **Example**: Claude Code was built before the models were strong enough to write most of Boris’s code. The product clicked later when Opus 4 and Sonnet 4 improved enough for the workflow to become compelling.

### Minimal Scaffolding / Don’t Box the Model In
- **When to use**: When building agentic AI products and deciding how much orchestration or workflow logic to impose on the model.
- **Steps**:
  1. Give the model a clear goal.
  2. Provide tools instead of rigid step-by-step workflows.
  3. Let the model decide what context it needs and how to gather it.
  4. Avoid over-engineering orchestration that may be obsolete by the next model generation.
- **Example**: Boris said Claude Code worked because Anthropic treated the product as the model itself, with minimal scaffolding and a small set of tools, rather than boxing it into a tightly scripted application.

### Under-Fund to Force Claude-ification
- **When to use**: When staffing new projects and trying to maximize speed and AI leverage rather than adding headcount by default.
- **Steps**:
  1. Start projects with fewer people than feels comfortable.
  2. Hire strong generalists who are motivated to ship.
  3. Push them to use AI aggressively to automate work.
  4. Scale resourcing only after the workflow and value are proven.
- **Example**: Boris said Anthropic sometimes puts one engineer on a project, and the constraint forces them to use Claude heavily and ship quickly.

### Release Early to Learn Product and Safety
- **When to use**: When shipping agentic AI systems where both user behavior and real-world safety properties are hard to predict in advance.
- **Steps**:
  1. Validate alignment and mechanistic interpretability at the model level.
  2. Run evals in controlled settings.
  3. Test internally for extended periods.
  4. Release early enough to observe real-world behavior and gather feedback.
  5. Feed product and safety learnings back into the system.
- **Example**: Anthropic used Claude Code internally for months before release and framed Cowork as a research preview so they could study how the agent behaves in the wild.

### Plan Mode First
- **When to use**: When using Claude Code on non-trivial tasks where you want higher first-pass quality and less rework.
- **Steps**:
  1. Start the task in plan mode.
  2. Have the model propose an approach without writing code.
  3. Review and refine the plan with the model.
  4. Once the plan is solid, let the model execute and auto-accept edits.
- **Example**: Boris said he starts roughly 80% of tasks in plan mode and then lets Opus 4.6 execute once the plan looks right.

### Three-Layer Safety Evaluation
- **When to use**: When assessing whether an AI agent is safe enough to deploy in increasingly autonomous settings.
- **Steps**:
  1. Study alignment and mechanistic interpretability at the neuron/model level.
  2. Run evals in synthetic or laboratory-style scenarios.
  3. Observe behavior in the real world after controlled release.
- **Example**: Boris described Anthropic’s safety process for Claude Code and Cowork as combining interpretability, evals, and real-world observation.

## Core Advice
- **When you face uncertainty about what AI product to build next**: Do close observation of how users are already bending your product to solve adjacent problems, then build toward those behaviors — because unexpected usage reveals real demand more reliably than abstract ideation.
- **When you face pressure to tightly orchestrate an AI workflow**: Do less orchestration: give the model tools and a goal instead of forcing a rigid sequence of steps — because more capable general models often outperform heavily scaffolded systems.
- **When you face early-stage experimentation with AI and worry about token costs**: Do the opposite of premature optimization: give engineers generous token budgets and optimize later only after something works — because the biggest breakthroughs often come from trying ideas that seem too expensive at first.
- **When you face a new project and are tempted to overstaff it**: Do slightly under-resource the project so strong people are forced to automate aggressively with AI — because constraint can drive better AI adoption and faster shipping.
- **When you face a hard debugging or analysis task and instinctively reach for manual workflows**: Do ask Claude to investigate first, even for tasks you think require specialized human debugging techniques — because model capabilities improve so quickly that old assumptions become outdated fast.
- **When you face a non-trivial coding task in Claude Code**: Do start in plan mode, refine the plan, then let the model execute — because a reviewed plan reduces wasted edits and increases the odds of a correct one-shot implementation.
- **When you face model selection decisions for serious coding work**: Do use the most capable model rather than defaulting to the cheapest one — because a stronger model may consume fewer total tokens by making fewer mistakes.
- **When you face career uncertainty in an AI-transformed workplace**: Do become AI-native and more cross-functional rather than specializing narrowly in one discipline — because the most valuable people will be generalists who can operate across functions.
- **When you face the challenge of building AI products in a rapidly changing capability landscape**: Do build for where the model will be in six months, not just what it can do today — because products that feel slightly early can become breakout hits later.
- **When you face the need to get more feedback from users**: Do respond to user feedback extremely quickly, ideally by shipping fixes right away — because fast response loops increase the volume and quality of future feedback.

## Contrarian Takes
- **Conventional**: Coding is still a core human skill everyone in software should keep practicing manually. → **Their view**: Coding is becoming virtually solved, and in a year or two learning to code may matter far less than people think — because the valuable work is shifting to deciding what to build and reviewing outcomes.
- **Conventional**: To make AI reliable, you need lots of workflow scaffolding, orchestration, and tightly controlled prompts. → **Their view**: You often get better results by giving the model tools and freedom rather than boxing it into rigid workflows — because handcrafted scaffolding gets overtaken by the next model generation.
- **Conventional**: To control AI costs, companies should tightly limit token usage from the start. → **Their view**: Early on, companies should be generous with tokens and optimize only after they discover something valuable — because premature cost control suppresses experimentation.
- **Conventional**: More headcount is the best way to increase output on important projects. → **Their view**: Slightly under-funding projects can produce better outcomes because it forces teams to fully leverage AI — because constraint pushes automation and speed.
- **Conventional**: Engineering, product, and design will remain clearly separate functions. → **Their view**: These roles are already overlapping heavily, and titles like software engineer may give way to something more like builder — because everyone codes and contributes across planning, design, implementation, and prioritization.

## Notable Quotes
> “100% of my code is written by Claude Code. I have not edited a single line by hand since November.”

> “In a year or two, it’s not going to matter. Coding is virtually solved.”

> “I think by the end of the year everyone is going to be a product manager, and everyone codes.”