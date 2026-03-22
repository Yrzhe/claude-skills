# Operations

## Overview
Operations is about making work reliable, scalable, and legible across products, teams, and organizations. In Lenny’s conversations, the strongest operations advice centers on feedback loops, clear decision-making, gradual autonomy, and designing systems that surface reality instead of hiding it. Good operations reduce chaos, improve trust, and let teams move faster without breaking things.

## Key Frameworks

### Agency-Control Progression (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When building AI agents or AI-assisted workflows where reliability is uncertain and full autonomy would be risky.
- **Steps**:
  1. Start with high human control and low AI agency.
  2. Use the AI for suggestions, drafts, or routing first.
  3. Collect human feedback and observe failure modes.
  4. Increase autonomy gradually only after trust is earned.
  5. Expand from assistive actions to end-to-end execution.
- **Example**: In customer support, start with AI suggesting replies to agents, then showing answers directly to customers, and only later allow actions like refunds or feature requests.

### Continuous Calibration, Continuous Development (CCCD) (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When AI products must improve over time because user behavior and model behavior are non-deterministic.
- **Steps**:
  1. Scope the capability and curate representative examples.
  2. Align PMs, engineers, and SMEs on expected behavior.
  3. Set up the app and define evaluation metrics.
  4. Deploy and monitor real usage.
  5. Analyze behavior and identify unexpected errors.
  6. Fix issues and refine metrics.
  7. Repeat while gradually increasing AI agency.
- **Example**: Built after end-to-end support agents became unmanageable due to hot fixes and emerging failures.

### Actionable Feedback Loop for AI Products (Aishwarya Naresh Reganti + Kiriti Badam)
- **When to use**: When improving AI reliability after launch and deciding between evals, production monitoring, or both.
- **Steps**:
  1. Create a small trusted test set for critical behaviors.
  2. Monitor production for explicit and implicit user signals.
  3. Inspect traces that indicate failure or dissatisfaction.
  4. Identify recurring failure patterns.
  5. Turn recurring failures into eval datasets or metrics.
  6. Keep monitoring because new failures will emerge.
- **Example**: A user regenerating an answer instead of downvoting it is an implicit failure signal.

### Gardener vs. Builder Mindset (Alex Komoroske)
- **When to use**: When working in uncertain environments where compounding, ecosystems, or emergent behavior matter more than linear execution.
- **Steps**:
  1. Look for opportunities that can grow on their own.
  2. Plant many cheap, low-risk experiments.
  3. Watch for organic growth or user pull.
  4. Invest more only in ideas showing acceleration.
  5. Stop watering ideas that stop growing.
- **Example**: Build a small open-source tool quickly; if nobody uses it, the cost is low, but if it compounds, keep investing.

### 70/30 Team Portfolio for Emergence (Alex Komoroske)
- **When to use**: When leading a product team inside a larger organization and you need both credibility and room for breakthrough work.
- **Steps**:
  1. Spend about 70% on visible, valuable work.
  2. Use that execution to build trust.
  3. Reserve about 30% for exploratory bets.
  4. Let motivated people pursue promising ideas.
  5. Protect early ideas from premature scrutiny.
- **Example**: Let a junior PM pursue a “silly” idea if they are energized and there is plausible upside.

### Adjacent Possible + North Star (Alex Komoroske)
- **When to use**: When setting strategy in ambiguous environments where long-term ambition is needed but exact plans are unknowable.
- **Steps**:
  1. Define a low-resolution North Star 3–5 years out.
  2. Make sure it is plausible and inspiring.
  3. Survey the adjacent possible: what is feasible now.
  4. Choose the next step with the steepest gradient toward the North Star.
  5. Reassess after each move.
  6. Update the North Star gradually as reality changes.
- **Example**: Avoid leaping directly to the end state; take safe, reasonable steps that each make sense on their own.

### Difficult Feedback Conversation Script (Alisa Cohn)
- **When to use**: When giving constructive performance feedback about behavior, collaboration, or skill gaps.
- **Steps**:
  1. Get your mindset right: help, don’t vent.
  2. Open neutrally and matter-of-factly.
  3. State observable facts or credible reports.
  4. Tie feedback to role expectations.
  5. Invite their perspective.
  6. End with a concrete expectation for change.
- **Example**: “I wanted to have a conversation with you about some things I’ve been hearing from your peers...”

## Decision Guide
- If you need to launch an AI workflow with uncertain reliability, consider **Agency-Control Progression** because it reduces risk while building trust — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If your AI product keeps failing in ways your team didn’t anticipate, use **CCCD** because calibration must continue after launch — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you are unsure whether evals are enough, use the **Actionable Feedback Loop** because production signals reveal unknown failures — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If you are tempted to start from an AI feature instead of a user problem, use **Problem-First AI Product Development** because solution-first thinking leads to overbuilt products — per **Aishwarya Naresh Reganti + Kiriti Badam**.
- If your team is inside a large org and needs room for experimentation, use the **70/30 portfolio** because visible execution buys permission for exploration — per **Alex Komoroske**.
- If you are planning strategy in a messy market, use **Adjacent Possible + North Star** because it balances direction with adaptability — per **Alex Komoroske**.
- If you are deciding whether to keep investing in an idea, use the **Gardener vs. Builder mindset** because compounding signals should drive commitment — per **Alex Komoroske**.
- If your organization is drifting from reality, use the **organizational kayfabe lens** because bad news is often filtered out as it moves upward — per **Alex Komoroske**.
- If your company is getting too large for startup-style control, use **Slime mold organizational design** because scale forces a choice between coherence and autonomy — per **Alex Komoroske**.
- If you need to give hard feedback, use the **Difficult Feedback Conversation Script** because clarity plus calm reduces defensiveness — per **Alisa Cohn**.
- If a conversation becomes heated, use **Pause-and-reset for defensiveness** because continuing while dysregulated usually makes things worse — per **Alisa Cohn**.
- If you are ending a meeting and need real follow-through, use **Three questions to end every meeting** because alignment breaks down without explicit ownership — per **Alisa Cohn**.

## Expert Consensus
- Operations improve when teams create tight feedback loops between real usage and decision-making.
- AI systems should be introduced gradually, with humans in the loop until reliability is proven.
- Good operations depend on surfacing reality early, especially bad news and failure signals.
- Clear expectations, explicit ownership, and written follow-up prevent most execution drift.
- In uncertain environments, small reversible steps beat big speculative leaps.

## Points of Debate
- **Full autonomy vs. gradual autonomy** (Aishwarya Naresh Reganti + Kiriti Badam): Some want to ship the most autonomous agent quickly; they argue for starting with low agency and earning trust first.
- **Evals vs. production monitoring** (Aishwarya Naresh Reganti + Kiriti Badam): Evals are useful, but they are insufficient without real-world monitoring and user signals.
- **Top-down control vs. emergent systems** (Alex Komoroske): Traditional planning assumes control; the opposing view is to design for emergence, compounding, and adjacent moves.
- **Coherence vs. autonomy at scale** (Alex Komoroske): Large orgs can optimize for a unified experience or for independent teams, but not both equally.
- **Employee happiness vs. winning culture** (Alisa Cohn): Some leaders optimize for comfort; she argues the real job is clarity, accountability, and results.

## Key Metrics & Benchmarks
- **Only 8% of U.S. workers use AI daily** — indicates AI adoption is still early.
- **Zapier sales reps save 10 hours per week on lead research** — shows meaningful workflow leverage from AI.
- **Duolingo went from 100 courses in 12 years to 150 courses in 12 months** — strong example of AI accelerating output.
- **Intercom saw about a 20% year-over-year durable improvement in merged pull requests** — a proxy for AI-assisted engineering productivity.
- **Duolingo gave every employee $300 to try AI tools, courses, and subscriptions** — a practical internal enablement benchmark.
- **Zapier’s live demos attract over 60 employees every week** — shows the value of recurring internal AI learning.

## Notable Quotes
- “Start with the problem, not the agent.”
- “You don’t need to know the answer upfront if you can take cheap, reversible steps.”
- “What did we decide here? Who needs to do what by when? Who else needs to know?”