# Michael Truell

**Co-founder and CEO** | **Anysphere (Cursor)** | Expertise: AI coding tools, developer productivity, model development, product strategy

## Bio
Michael Truell is the co-founder and CEO of Anysphere, the company behind Cursor, one of the fastest-growing AI code editors. With a background in computer science, math, and AI research at MIT and Google, he brings a rare combination of technical depth and product intuition to the question of how software creation will change.

His perspective matters because he is not just theorizing about AI-assisted programming—he is building the tool that many developers use every day. He thinks deeply about the future of programming itself, especially how humans and AI should collaborate without sacrificing precision, control, or accountability.

## Signature Frameworks

### Human-in-the-driver's-seat programming
- **When to use**: When building AI tools for professional software creation and you want to preserve control, precision, and accountability.
- **Steps**:
  1. Keep the human as the decision-maker for what the software should do and how it should behave.
  2. Use AI to accelerate implementation, not replace intent.
  3. Provide interfaces that let users point at or edit software at a higher level than raw code.
  4. Support fast iteration loops so humans can review and steer quickly.
  5. Avoid fully chatbot-based workflows when precision and control matter.
- **Example**: Cursor is designed so engineers can specify intent and keep control, rather than handing the whole task to a bot.

### The “what” over the “how” evolution
- **When to use**: When thinking about the future of programming languages, IDEs, or AI-assisted development workflows.
- **Steps**:
  1. Represent software logic in a more human-readable form, closer to English or pseudocode.
  2. Make the logic editable at a high level.
  3. Reduce dependence on millions of lines of opaque code.
  4. Shift the engineer’s job toward specifying desired behavior and outcomes.
  5. Preserve enough structure for precision and navigation.
- **Example**: Michael describes a future where engineers edit a terser logic representation instead of directly thinking in JavaScript, Python, or other formal languages.

### Specialized model ensemble
- **When to use**: When a general foundation model is strong but not optimal for speed, cost, or a narrow coding task.
- **Steps**:
  1. Use the best large foundation models for high-level reasoning.
  2. Add retrieval/search models to find the right code context.
  3. Use fast specialty models for tasks like autocomplete or filling in diffs.
  4. Train or post-train models on the exact subtask where general models are weak.
  5. Combine models with inference tricks to improve latency and quality.
- **Example**: Cursor uses custom models for autocomplete and for turning high-level change sketches from Sonnet/GPT/Gemini into full code diffs.

### Dogfood-first product development
- **When to use**: When building a product for power users and you need a strong signal on usefulness before scaling.
- **Steps**:
  1. Use the product intensely every day as the core team.
  2. Refuse to ship features that are not useful to the team itself.
  3. Iterate quickly based on firsthand pain points.
  4. Release early to real users once the product is minimally useful.
  5. Let user feedback reshape the architecture and roadmap.
- **Example**: Cursor’s first version was built in about three months, then quickly put into users’ hands, and feedback led them to switch to VS Code as a base.

### Conservative AI adoption with tight task scoping
- **When to use**: When teams are trying to use AI effectively in real production coding environments.
- **Steps**:
  1. Break work into smaller chunks instead of handing over huge tasks.
  2. Specify a bit, let the AI work, then review and continue.
  3. Use AI most aggressively where correctness is easy to specify, such as bug fixes.
  4. Keep the review loop short and frequent.
  5. Avoid wholesale end-to-end delegation in long-lived codebases.
- **Example**: Successful Cursor users often alternate between small specification steps and AI-generated work rather than asking for a giant one-shot implementation.

### Build the best thing, not the most locked-in thing
- **When to use**: When operating in a fast-moving AI market with low switching costs and frequent leapfrogs.
- **Steps**:
  1. Assume competitors can catch up or leapfrog.
  2. Focus on continuous product quality improvements.
  3. Invest in R&D where the ceiling is still high.
  4. Use distribution and user feedback to improve the product.
  5. Treat defensibility as a consequence of excellence, not contracts or lock-in.
- **Example**: Michael compares the market more to search in the late 1990s than to a traditional enterprise software market.

## Core Advice
- **When a task seems too big for AI**: Do it in smaller chunks with frequent review cycles instead of one giant prompt — because Cursor users are most successful when they specify a little, let the model work, then refine.
- **When you want to understand what AI can really do**: Try ambitious experiments in a safe side project and intentionally push the model to its limits — because many people underestimate capability until they see it in a low-risk setting.
- **When choosing between a model, plugin, or full IDE**: Build the full environment if you believe the workflow itself will change substantially — because the interface may need to evolve, not just the underlying model.
- **When deciding whether to use chat for software creation**: Avoid relying on plain chat for tasks that require precision and direct control — because chat is too imprecise for detailed software work.
- **When building AI features for coding**: Use specialized models for narrow tasks like autocomplete, retrieval, and diff completion — because foundation models alone are often too slow, too expensive, or not specialized enough.
- **When hiring for a fast-moving technical startup**: Hire for intellectual curiosity, experimentation, blunt honesty, and level-headedness rather than only pedigree — because those traits help teams stay focused and adaptable.
- **When recruiting hard-to-get talent**: Expect recruiting to take years, not weeks, and keep the conversation going over time — because world-class people often need long trust-building cycles.
- **When interviewing for a small, high-trust team**: Use a real two-day work test instead of relying only on standard interviews — because it reveals actual work quality and collaboration style.
- **When building in a rapidly changing AI market**: Stay paranoid about how much better the product could still become — because sustained improvement matters more than a single launch.
- **When tempted to overbuild process early**: Lean on hiring and shared standards first, and add process only as needed — because excellent, level-headed people reduce the need for heavy bureaucracy.
- **When trying to keep a team focused amid AI hype**: Hire people who are less driven by external validation and more driven by high-quality work — because emotional steadiness helps teams ignore noise.
- **When evaluating whether AI will replace engineers soon**: Plan for engineers to remain essential, but expect them to do much more — because software demand is huge and AI expands capacity rather than eliminating the role.

## Contrarian Takes
- **Conventional**: The future of software will either stay mostly like today or become a simple chatbot where you ask AI to build everything. → **Their view**: The future will look weirder than both: a higher-level, more human-readable programming layer that preserves precision and human control — because chat is too imprecise and unchanged formal coding underestimates progress.
- **Conventional**: AI coding tools should eventually let users fully delegate work to autonomous agents. → **Their view**: Humans should stay in the driver’s seat, and the best tools will support fast back-and-forth control rather than full automation — because professional software work requires review and accountability.
- **Conventional**: You should avoid crowded spaces and go after boring, underexplored markets. → **Their view**: A hot, crowded market can still be the right choice if the ceiling is high and incumbents are not ambitious enough — because leapfrogging is possible.
- **Conventional**: AI products are mostly wrappers around foundation models. → **Their view**: The most valuable AI products will develop their own models for key tasks and combine them with foundation models — because specialization matters for speed and quality.
- **Conventional**: The best moat in software is lock-in, contracts, or switching costs. → **Their view**: In fast-moving AI markets, the real moat is continuously building the best product and staying ahead through R&D — because companies can be leapfrogged repeatedly.
- **Conventional**: Hiring fast is the main early-stage mistake. → **Their view**: Cursor hired too slowly at the beginning — because they were overly cautious about team quality.

## Notable Quotes
> “Our goal with Cursor is to invent sort of a new type of programming, a very different way to build software.”

> “At this point, every magic moment in Cursor involves a custom model in some way.”

> “I think taste will be increasingly more valuable.”