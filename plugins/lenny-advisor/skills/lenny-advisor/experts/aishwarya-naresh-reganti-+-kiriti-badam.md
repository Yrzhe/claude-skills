# Aishwarya Naresh Reganti + Kiriti Badam

**AI product advisors, educators, and practitioners** | **OpenAI / independent AI product education and consulting** | Expertise: ai-strategy, product-management, design, go-to-market, operations, engineering-management

## Bio
Aishwarya Naresh Reganti and Kiriti Badam help teams build AI products that actually work in the real world, not just in demos. They’ve supported dozens of enterprise and startup deployments, and they teach a highly practical course on building enterprise AI products.

Aishwarya brings deep experience in AI research and product leadership from Alexa and Microsoft, while Kiriti brings infrastructure and systems experience from Google, Kumo, and now Codex at OpenAI. Their perspective matters because they focus on the hard part of AI products: reliability, workflow fit, adoption, and the learning loops required to improve over time.

## Signature Frameworks

### Agency-Control Progression
- **When to use**: When building AI agents or AI-assisted workflows where reliability is uncertain and full autonomy would be risky.
- **Steps**:
  1. Start with high human control and low AI agency.
  2. Use the AI first for suggestions, drafts, or routing rather than autonomous actions.
  3. Collect human feedback and observe failure modes.
  4. Increase autonomy gradually only after the system earns trust.
  5. Expand scope from assistive actions to end-to-end execution.
- **Example**: In customer support, start with AI suggesting responses to agents, then show answers directly to customers, and only later allow the system to issue refunds or create feature requests.

### Problem-First AI Product Development
- **When to use**: When teams are tempted to start from flashy AI capabilities or agent architectures instead of a concrete user problem.
- **Steps**:
  1. Define the exact user or business problem first.
  2. Break the problem into smaller solvable units.
  3. Choose the minimum level of autonomy needed for the first version.
  4. Use AI only where it clearly improves the workflow.
  5. Expand capability after validating the initial problem is being solved.
- **Example**: Before building an “agent,” ask: “What problem am I actually solving?” and scope the first version to that narrow workflow.

### Continuous Calibration, Continuous Development (CCCD)
- **When to use**: When building AI products that must improve over time because user behavior and model behavior are both non-deterministic.
- **Steps**:
  1. Scope the capability and curate representative input/output examples.
  2. Align PMs, engineers, and subject matter experts on expected behavior.
  3. Set up the application and define evaluation metrics.
  4. Deploy and monitor real usage.
  5. Analyze behavior and spot unexpected error patterns.
  6. Apply fixes and add or refine evaluation metrics where needed.
  7. Repeat the loop while gradually increasing AI agency.
- **Example**: They developed CCCD after seeing end-to-end customer support agents become unmanageable due to constant hot fixes and emerging failures.

### Actionable Feedback Loop for AI Products
- **When to use**: When teams need to improve AI reliability after launch and decide between evals, production monitoring, or both.
- **Steps**:
  1. Create a small trusted test set for known critical behaviors.
  2. Deploy with production monitoring for explicit and implicit user signals.
  3. Inspect traces that indicate failures or dissatisfaction.
  4. Identify recurring failure patterns.
  5. Turn important recurring failures into evaluation datasets or metrics.
  6. Keep monitoring production because new failures will continue to emerge.
- **Example**: If users regenerate an answer instead of giving a thumbs down, treat that as an implicit failure signal and investigate the trace.

## Core Advice
- **When you face pressure to launch a fully autonomous AI agent quickly**: do a lower-agency version first, with humans in the loop and constrained decision-making — because this reduces risk, preserves trust, and gives you real behavioral data.
- **When you face an AI product with unpredictable behavior**: calibrate in production by monitoring traces, user signals, and emerging failure patterns — because you cannot predict all inputs or outputs upfront.
- **When you face internal confusion about whether evals are enough**: do both offline evals and production monitoring — because evals catch known risks while production reveals unknown failures.
- **When you face leadership skepticism or poor AI adoption inside a company**: create dedicated time for leaders to rebuild their AI intuitions — because AI changes old product and technical assumptions.
- **When you face resistance from subject matter experts who fear AI will replace them**: build culture around augmentation, not replacement — because SMEs are essential for defining ideal behavior and interpreting failures.
- **When you face messy enterprise workflows and data**: analyze the workflow deeply before adding agents, and combine AI with deterministic code where appropriate — because enterprise systems contain undocumented rules and tech debt.
- **When you face a vendor promising one-click agents with immediate ROI**: do due diligence and prefer systems with a learning pipeline and feedback flywheel — because critical workflows usually need months of iteration.
- **When you face uncertainty about whether your AI system is ready for more autonomy**: check whether calibration cycles are still surfacing surprising patterns; if surprise is low, move to the next stage — because autonomy should follow trust, not precede it.

## Contrarian Takes
- **Conventional**: The goal is to launch the most autonomous agent as quickly as possible. → **Their view**: Start with minimal autonomy and increase agency only after the system earns trust — because full autonomy creates too many failure modes and too much risk.
- **Conventional**: Evals are the main solution to AI product reliability. → **Their view**: Evals are necessary but insufficient; production monitoring matters just as much — because real usage reveals unexpected behaviors.
- **Conventional**: If a company is first to ship an agent, it gains the advantage. → **Their view**: The real advantage is building the right flywheels to improve over time — because durable value comes from learning loops.
- **Conventional**: Buying or deploying a one-click agent should quickly produce ROI. → **Their view**: Reliable automation for critical workflows usually takes four to six months — because enterprise data and workflows are messy.
- **Conventional**: More tools and faster implementation are the main differentiators. → **Their view**: Design, taste, judgment, and problem selection matter more — because implementation is getting cheaper.
- **Conventional**: Multi-agent systems are the natural answer to complex AI problems. → **Their view**: Many multi-agent setups are harder to control than people think; supervisor patterns are more practical — because peer-to-peer coordination creates guardrail problems.

## Notable Quotes
> “It's not about being the first company to have an agent among your competitors. It's about have you built the right flywheels in place so that you can improve over time.”

> “Pain is the new moat.”

> “Be obsessed with your customers. Be obsessed with the problem. AI is just a tool.”