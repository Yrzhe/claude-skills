# Hamel Husain

**AI evals educator, consultant, and co-creator of the AI evals course** | **Independent / Maven course instructor** | Expertise: ai-strategy, evaluation, data analysis, product quality

## Bio
Hamel Husain is one of the clearest voices making AI evals practical for product teams. He translates machine learning error analysis into workflows that PMs and engineers can actually use to understand failures, prioritize fixes, and build reliable LLM products.

His perspective matters because he focuses on what works in real applications, not just benchmark theory. He is especially useful when a team knows an AI product is “off” but needs a disciplined way to discover why.

## Signature Frameworks

### Error analysis via open coding -> axial coding -> counting
- **When to use**: When an AI product is behaving inconsistently and you need to understand real failure modes before writing evals or changing prompts.
- **Steps**:
  1. Sample production traces or logs rather than trying to inspect everything.
  2. Review each trace manually and write one short note about the first, most upstream thing that seems wrong.
  3. Keep notes informal but specific enough to be understandable later.
  4. Continue until you reach theoretical saturation, meaning you are no longer learning new failure types.
  5. Use an LLM to cluster the open-coded notes into axial codes or failure-mode categories.
  6. Refine the categories so they are actionable and product-relevant.
  7. Count the categories with a pivot table or similar analysis to identify the most prevalent or important issues.
  8. Prioritize fixes and decide which issues need automated evaluators versus simple product or prompt fixes.
- **Example**: Using Nurture Boss apartment-leasing traces, they identified issues like “should have handed off to a human,” “conversation flow is janky because of text message,” “offered virtual tour” when none existed, and “did not confirm call transfer with user,” then grouped and counted these failures.

### Benevolent dictator for eval labeling
- **When to use**: When teams get stuck trying to align a committee around what counts as good or bad behavior in an AI product.
- **Steps**:
  1. Choose one trusted person with domain expertise to own the initial labeling and judgment calls.
  2. Have that person perform the open coding and define what good behavior looks like.
  3. Avoid committee-driven scoring early on, which makes the process too slow and expensive.
  4. Use the single decision-maker’s taste as the initial source of truth, then refine later if needed.
- **Example**: For a leasing assistant, the person doing the labeling should understand apartment leasing and customer handling; often this ends up being the PM.

### Binary LLM-as-judge evaluator
- **When to use**: When a failure mode is too subjective or complex for code-based checks, but narrow enough that an LLM can reliably judge pass/fail.
- **Steps**:
  1. Pick one specific failure mode rather than trying to judge overall quality.
  2. Write a prompt that defines exactly when the behavior should be considered a failure.
  3. Force the judge to output a binary result such as true/false or pass/fail.
  4. Run the judge on previously labeled examples.
  5. Compare judge outputs against human labels using a confusion matrix, not just overall agreement.
  6. Iterate on the prompt until false positives and false negatives are acceptably low.
  7. Deploy the judge in CI, unit tests, or production monitoring.
- **Example**: They built a handoff judge for the leasing assistant that checked whether the system should have transferred to a human in cases like explicit human requests, policy-mandated transfers, sensitive resident issues, or unavailable tool data.

### Theoretical saturation stopping rule
- **When to use**: When deciding how many traces to inspect during manual error analysis.
- **Steps**:
  1. Start reviewing traces and recording open codes.
  2. Watch for whether new traces continue to reveal new categories of problems.
  3. Stop when additional traces no longer materially change your understanding of failure modes.
  4. Use rough heuristics like 100 traces only as a starting point, not a fixed rule.
- **Example**: They recommend starting with around 100 traces to unblock people psychologically, but note that some teams may saturate after 15, 40, or 60 depending on the product and their experience.

### Use AI for synthesis, not first-pass judgment
- **When to use**: When deciding where in the eval workflow to automate with LLMs.
- **Steps**:
  1. Do the initial free-form review of traces manually.
  2. Capture detailed notes about what seems wrong.
  3. Use LLMs afterward to synthesize, cluster, relabel, and organize those notes.
  4. Optionally use LLMs to help draft judge prompts or categorize notes into predefined buckets.
  5. Keep humans in the loop for refinement and final decisions.
- **Example**: They warn that if you ask ChatGPT to inspect a trace and find errors, it may say the trace looks good because it lacks product context, but the same model is very useful for turning many open codes into axial-code categories.

## Core Advice
- **When an AI product feels off but you don’t know why**: Do manual error analysis on a sample of real traces before writing evals or changing prompts — because looking directly at production behavior reveals the actual failure modes, which are often different from what teams imagine upfront.
- **When pressured to automate eval creation immediately with AI**: Do not use an LLM for the initial free-form note-taking stage; have a human with domain expertise review traces first — because LLMs often miss product-contextual issues and will incorrectly mark flawed traces as acceptable.
- **When too many possible issues appear in a single trace**: Record only the first, most upstream error you notice and move on — because this keeps the process fast, consistent, and tractable instead of turning each trace into an exhaustive debate.
- **When disagreement slows down what counts as good output**: Appoint a benevolent dictator with domain expertise to own the initial labeling and taste decisions — because a single trusted decision-maker dramatically reduces process cost and helps teams make progress instead of stalling in committee.
- **When you have a messy list of open-coded notes**: Use an LLM to cluster them into actionable failure-mode categories, then count them — because LLMs are strong at synthesis, and simple counting is often enough to reveal the highest-leverage problems to fix.
- **When a failure mode seems subjective or hard to encode in software**: Build a narrow binary LLM-as-judge evaluator for that one failure mode — because LLM judges work better when the task is tightly scoped and the output is pass/fail rather than a vague score.
- **When tempted to use 1–5 or 1–7 scoring for LLM judges**: Use binary pass/fail decisions instead of Likert-style scales — because binary judgments are easier to define, easier to interpret, and less likely to create meaningless averages like 4.2 that no one can act on.
- **When a judge prompt seems to work on first try**: Validate it against human labels with a confusion matrix before trusting it — because raw agreement can be misleading, especially when failures are rare.
- **When a product issue is obviously fixable in code or prompting**: Fix it directly instead of over-investing in an eval for it — because evals have a cost-benefit tradeoff and not every issue deserves a permanent automated evaluator.
- **When evals seem like a huge recurring burden**: Treat the first round as a one-time setup cost, then maintain it with lightweight weekly reviews — because once categories and judges exist, teams can often review and improve in as little as 30 minutes per week.
- **When trace review feels too cumbersome**: Build lightweight internal tools that make trace review and annotation easy — because reducing friction increases the odds that teams will actually inspect data, which he sees as the highest-ROI activity in AI product development.
- **When deciding whether evals are only for pre-launch testing**: Run evaluators on production traces continuously for monitoring, not just in CI — because online monitoring gives a much sharper and more realistic view of application quality than offline tests alone.

## Contrarian Takes
- **Conventional**: Evals are basically unit tests for AI systems. → **Their view**: Unit tests are only a small part of evals; evals should include error analysis, production monitoring, product metrics, and broader measurement of quality — because AI products are open-ended and stochastic.
- **Conventional**: You should start by writing tests or evaluator prompts for what you think matters. → **Their view**: Start by looking at real traces and discovering actual failure modes first — because teams are often wrong about the important failures until they inspect real usage data.
- **Conventional**: AI can automate the whole eval process, including finding what is wrong. → **Their view**: Humans must do the initial contextual judgment; AI is better used later for synthesis and organization — because LLMs lack the product and domain context needed for nuanced trace review.
- **Conventional**: More nuanced scoring scales produce better evaluators. → **Their view**: Binary pass/fail judges are usually better than 1–5 or 1–7 scales — because multi-point scales create ambiguity and hard-to-use metrics.
- **Conventional**: If top AI teams say they rely on vibes, evals must not matter. → **Their view**: Even “vibes” teams are usually doing some form of evals, whether explicit or implicit — because dogfooding, monitoring, and systematic failure review are all evaluation.
- **Conventional**: A/B tests are an alternative to evals. → **Their view**: A/B tests are part of the eval toolkit and work best when grounded in prior error analysis — because otherwise teams test the wrong hypotheses.
- **Conventional**: Good evals should be standardized and tool-driven. → **Their view**: Application-specific evals require product-specific thinking and cannot be fully outsourced to generic tools — because generic hallucination scores often do not correlate with what users actually care about.

## Notable Quotes
> “The goal is not to do evals perfectly, it's to actionably improve your product.”

> “You can appoint one person whose taste that you trust.”

> “It's the highest ROI activity you can engage in.”