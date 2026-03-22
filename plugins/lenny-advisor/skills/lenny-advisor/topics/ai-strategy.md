# AI Strategy

## Overview
AI strategy is about choosing the right problems, the right level of autonomy, and the right operating model for AI products and teams. The core challenge is not just building with models, but designing systems where human judgment, product intent, and machine capability work together.

Most experts agree that AI creates leverage only when paired with strong problem selection, tight feedback loops, and realistic expectations about reliability. In practice, that means starting with the user problem, calibrating in production, and increasing autonomy only as trust and evidence accumulate.

## Key Frameworks

### Human-in-the-loop algorithm design (Adriel Frederick)
- **When to use**: When building products that rely heavily on machine learning, optimization, pricing, ranking, or other algorithmic systems.
- **Steps**:
  1. Define the product intent and strategic goals before optimizing anything.
  2. Decide explicitly what decisions the algorithm should make versus what decisions humans should make.
  3. Identify the constraints and judgment calls algorithms cannot reliably infer.
  4. Design interfaces and tools that give humans the right information to make strategic decisions.
  5. Use the algorithm to amplify human intent at scale rather than operate as an unchecked black box.
  6. Continuously observe outcomes and refine the division of responsibility.
- **Example**: At Lyft, pricing systems needed people in the loop because local teams had to respond to snowstorms, fuel price changes, taxes, or competitive moves in specific cities.

### Marginal user analysis (Adriel Frederick)
- **When to use**: When trying to improve activation, signup conversion, onboarding, or growth in products with large user funnels.
- **Steps**:
  1. Find the user segment just on the cusp of succeeding but currently struggling to convert.
  2. Inspect the worst-case user experience to reveal the full set of failures.
  3. Observe real users directly instead of relying only on funnel data.
  4. List all friction points, including issues not visible in the funnel.
  5. Prioritize barriers that are important and realistically fixable.
  6. Iterate on making the product “stupid easy” for that user to succeed.
- **Example**: At Facebook, Adriel found issues in high-traffic, low-conversion countries like wrong language defaults, phone number formatting problems, and latency to data centers.

### Core growth loop simplification (Adriel Frederick)
- **When to use**: When a product has demand but struggles to turn new users into retained users.
- **Steps**:
  1. Identify the few core actions that unlock value.
  2. Make it easy to find the product.
  3. Make it easy to get into the product.
  4. Make it extremely easy to find friends, collaborators, or relevant connections.
  5. Reinforce the habit of returning by reminding users there is something valuable waiting.
  6. Keep grinding on fundamentals rather than chasing clever hacks.
- **Example**: Facebook repeatedly focused on signup, first friends, and return habits instead of one-off growth hacks.

### Agency-Control Progression (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When building AI agents or AI-assisted workflows where reliability is uncertain and full autonomy would be risky.
- **Steps**:
  1. Start with high human control and low AI agency.
  2. Use AI first for suggestions, drafts, or routing.
  3. Collect human feedback and observe failure modes.
  4. Increase autonomy gradually after the system earns trust.
  5. Expand scope from assistive actions to end-to-end execution.
- **Example**: In customer support, start with AI suggesting responses, then showing answers directly to customers, then allowing actions like refunds.

### Continuous Calibration, Continuous Development (CCCD) (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When building AI products that must improve over time because user behavior and model behavior are non-deterministic.
- **Steps**:
  1. Scope the capability and curate representative examples.
  2. Align PMs, engineers, and subject matter experts on expected behavior.
  3. Set up the application and define evaluation metrics.
  4. Deploy and monitor real usage.
  5. Analyze behavior and spot unexpected error patterns.
  6. Apply fixes and refine evaluation metrics.
  7. Repeat while gradually increasing AI agency.
- **Example**: They developed CCCD after end-to-end support agents became hard to manage due to constant hot fixes and emerging failures.

### Gardener vs. Builder mindset (Alex Komoroske)
- **When to use**: When building products, teams, or strategies in uncertain environments where compounding dynamics matter more than linear execution.
- **Steps**:
  1. Identify opportunities that can grow on their own.
  2. Look for seeds with compounding potential.
  3. Plant many cheap, low-risk experiments.
  4. Watch for organic growth or user pull.
  5. Invest more only in ideas showing acceleration.
  6. Stop watering ideas that stop growing.
- **Example**: A small open-source tool can be a cheap seed; if developers adopt it and it compounds, keep investing.

### Adjacent Possible + North Star (Alex Komoroske)
- **When to use**: When setting product strategy in ambiguous environments where long-term ambition is needed but exact plans are unknowable.
- **Steps**:
  1. Define a low-resolution North Star 3-5 years out.
  2. Make sure it is plausible and exciting to stakeholders.
  3. Survey the adjacent possible: what is feasible now.
  4. Choose the next step with the steepest gradient toward the North Star.
  5. Take the step, observe how reality changes, and reassess.
  6. Update the North Star gradually as conditions change.
- **Example**: Instead of leaping to an end state, take safe, reasonable steps that each make sense on their own.

### Teammate-first agent adoption (Alexander Embiricos)
- **When to use**: When introducing coding agents into real engineering workflows and trying to build trust over time.
- **Steps**:
  1. Start inside the IDE or CLI rather than fully remote delegation.
  2. Have the agent understand the codebase and answer questions first.
  3. Collaborate on an approach before asking it to implement.
  4. Let it execute tasks with local access and dependencies.
  5. Gradually expand permissions and validation.
  6. Move toward delegation and proactivity once trust is established.
- **Example**: Treat Codex like a smart intern: work side by side first, then give it more autonomy.

## Decision Guide
- If you are building an algorithmic product, consider **human-in-the-loop algorithm design** because product intent and judgment must stay explicit — per **Adriel Frederick**.
- If activation is weak and funnel data is inconclusive, consider **marginal user analysis** because direct observation reveals hidden friction — per **Adriel Frederick**.
- If users sign up but do not retain, consider **core growth loop simplification** because durable growth comes from making the core value path obvious and easy — per **Adriel Frederick**.
- If you are launching an AI workflow with uncertain reliability, consider **Agency-Control Progression** because autonomy should increase only after trust is earned — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If your AI product keeps breaking in new ways after launch, use **CCCD** because production behavior must be calibrated continuously — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you need to improve AI reliability, use **Actionable Feedback Loop for AI Products** because offline evals and production signals catch different failure modes — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you are unsure whether to pursue a big bet or many small tests, use **Experiment Portfolio Balancing** because too many tiny experiments can crowd out meaningful change — per **Adriel Frederick**.
- If you are working in a highly uncertain market, use the **Gardener vs. Builder mindset** because cheap seeds and compounding loops outperform overplanned certainty — per **Alex Komoroske**.
- If you need a roadmap in an ambiguous space, use **Adjacent Possible + North Star** because it balances ambition with reversible next steps — per **Alex Komoroske**.
- If you are integrating an innovation team into a larger company, use **R&D team integration framework** because isolated teams risk resentment and “organ rejection” — per **Adriel Frederick**.
- If you are introducing coding agents to engineers, use **Teammate-first agent adoption** because trust grows faster when the agent behaves like a collaborator first — per **Alexander Embiricos**.
- If you are tempted to start from flashy AI capabilities, use **Problem-First AI Product Development** because the problem should define the solution, not the other way around — per **Aishwarya Naresh Reganti + Kiriti Badam**.

## Expert Consensus
- Start with the user problem, not the model.
- Keep humans in the loop until the system proves reliability.
- Use production feedback, not just offline evaluation.
- Increase autonomy gradually as trust and evidence improve.
- AI advantage comes from workflow design, feedback loops, and taste, not just raw model access.
- In uncertain environments, small reversible steps beat grand plans.
- Organizational alignment matters as much as technical capability.

## Points of Debate
- **Full autonomy vs. gradual autonomy** (Aishwarya Naresh Reganti + Kiriti Badam):  
  - **Gradual autonomy**: safer, more trustworthy, and easier to debug.  
  - **Full autonomy**: tempting for speed, but often creates too many failure modes too early.

- **Evals-first vs. production-first learning** (Aishwarya Naresh Reganti + Kiriti Badam):  
  - **Evals-first**: useful for known risks and repeatable checks.  
  - **Production-first**: necessary because real users reveal unknown failures and implicit dissatisfaction.

- **Builder mindset vs. gardener mindset** (Alex Komoroske):  
  - **Builder**: useful when the path is known and execution is the main challenge.  
  - **Gardener**: better when value emerges from compounding, ecosystems, and user pull.

- **Centralized coherence vs. distributed autonomy** (Alex Komoroske):  
  - **Coherence**: better for integrated experiences and strong brand consistency.  
  - **Autonomy**: better for speed, resilience, and local adaptation in large orgs.

- **Big bets vs. many small experiments** (Adriel Frederick / Alex Komoroske):  
  - **Big bets**: needed when the product needs fundamental change.  
  - **Small experiments**: useful for learning, but can become a distraction if overused.

## Key Metrics & Benchmarks
- **Only 8% of U.S. workers use AI daily** — Gallup poll; indicates AI adoption is still early.
- **Zapier sales reps save 10 hours per week on lead research** — shows concrete workflow leverage.
- **Duolingo went from 100 courses in 12 years to 150 courses in 12 months** — strong example of AI accelerating content production.
- **Intercom saw about a 20% year-over-year durable improvement in merged pull requests** — proxy for AI-assisted engineering productivity.
- **Duolingo gave every employee $300 to try AI tools, courses, and subscriptions** — a practical internal enablement benchmark.
- **Zapier’s live demos attract over 60 employees every week** — shows the value of recurring AI learning rituals.
- **Over 1,500 merged PRs / averaging 10 per day** — Devin’s contribution at Gumroad, showing real production usage.
- **Over 6 million lines** — size of Nubank’s ETL monolith that Devin helped migrate, indicating suitability for large legacy systems.

## Notable Quotes
- “Use the algorithm to amplify human intent at scale rather than operate as an unchecked black box.” — **Adriel Frederick**
- “You do not need to predict the winning acorn in advance if the cost of planting is low and the upside of a compounding winner is high.” — **Alex Komoroske**
- “A product that works 95% of the time but occasionally punches the user in the face is not viable.” — **Alex Komoroske**