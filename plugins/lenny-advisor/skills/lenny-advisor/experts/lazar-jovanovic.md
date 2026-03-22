# Lazar Jovanovic

**Professional vibe coding engineer** | **Lovable** | Expertise: ai-strategy, product-management, design, go-to-market

## Bio
Lazar is the first official vibe coding engineer at Lovable, building internal tools, templates, and customer-facing products with AI despite not coming from a traditional coding background. His perspective matters because he sits at the intersection of product thinking, design taste, and AI execution—showing how vague ideas can become production-ready software through strong planning and iteration.

## Signature Frameworks

### Parallel Clarity Sprint
- **When to use**: When you start with a vague idea and need to quickly find the best direction before committing to a build.
- **Steps**:
  1. Brain-dump the idea using voice or chat into a first project.
  2. Open a second project with a more refined written prompt.
  3. Create a third version using screenshots or references from tools like Mobbin or Dribbble.
  4. Create a fourth version using code snippets or templates from libraries like 21st.dev or DotBuild.
  5. Compare the outputs to identify the clearest and highest-quality direction.
  6. Use the winning direction as the basis for deeper planning.
- **Example**: Start four Lovable tabs in parallel: one with a voice brain dump, one with a typed prompt, one with design references, and one with code snippets, then choose the strongest result.

### PRD-to-Tasks Execution System
- **When to use**: When you have chosen a direction and need to turn it into a reliable build process an AI agent can execute with minimal confusion.
- **Steps**:
  1. Write a `masterplan.md` explaining the why, who, and desired feel of the product.
  2. Write an implementation plan that defines build order and sequencing.
  3. Write `design guidelines.md` to specify look, feel, and constraints.
  4. Write a user journey document that maps the end-to-end flow.
  5. Consolidate everything into `tasks.md` or `plan.md` with concrete tasks and subtasks.
  6. Add `rules.md` or `agents.md` / project knowledge so the agent knows how to behave.
  7. Tell the agent to read all files first, then execute one task at a time.
  8. Review the output and update the docs as the project evolves.
- **Example**: For a project, create `masterplan.md`, implementation plan, design guidelines, user journey docs, then `tasks.md`, and instruct Lovable to read them before doing any work.

### Four-by-Four Debugging Workflow
- **When to use**: When a build breaks and you need to diagnose and fix issues without wasting context or blindly trusting the agent.
- **Steps**:
  1. Use the tool’s built-in “try to fix” flow if the agent detects the issue.
  2. Add or inspect console logs in the preview/dev environment to increase observability.
  3. Export the codebase to GitHub and use an external diagnostic tool like Codex or Claude with logs and context.
  4. Revert to a prior version and rethink the prompt if the issue was caused by bad instructions.
  5. After the fix, ask the agent how to prompt it better next time.
  6. Encode the lesson into `rules.md` so future runs benefit from the learning.
- **Example**: If a third-party integration breaks, first try Lovable’s fix button, then add console logs, then use Codex or Repomix + Claude, and finally update `rules.md` with what you learned.

### Exposure-Time Taste Building
- **When to use**: When you need to improve judgment, design taste, or clarity about what “good” looks like in AI-assisted building.
- **Steps**:
  1. Deliberately consume high-quality design, copy, and product examples.
  2. Follow world-class builders and designers.
  3. Study great interfaces, onboarding flows, fonts, and visual systems.
  4. Use that exposure to calibrate prompts and decisions.
  5. Practice by building repeatedly to turn taste into a muscle.
- **Example**: Learn design styles like Bauhaus and glassmorphism by exposing yourself to great design and building an app to study them.

## Core Advice
- **When you start with only a vague idea**: Do a brain dump first, then refine the idea in separate parallel builds instead of trying to perfect one prompt — because parallel exploration creates clarity faster and avoids overcommitting to a weak first direction.
- **When you want better AI output**: Be extremely specific and provide references, screenshots, or code snippets rather than saying “you know what I mean” — because AI lacks human context and will otherwise optimize for the wrong interpretation.
- **When you are building with AI**: Spend most of your time planning and chatting, not executing — because clarity is the real bottleneck.
- **When you want to avoid AI slop**: Optimize for taste, design quality, fonts, and copy, not just raw output speed — because good enough is now easy; differentiation comes from judgment and polish.
- **When you are building a complex project**: Create source-of-truth docs like `masterplan.md`, implementation plan, design guidelines, user journey, and `tasks.md` before deep execution — because these documents preserve context and reduce drift.
- **When the agent starts losing context**: Break work into one task at a time and keep updating docs instead of piling on prompts — because context windows are limited and smaller scopes preserve quality.
- **When a build breaks and the fix is unclear**: Add console logs and instrument the code so you can see what is actually happening — because observability often reveals the issue quickly.
- **When the built-in agent cannot solve a bug**: Export the codebase and use a second model or tool as a diagnostic consultant — because a different model can spot issues the original agent missed.
- **When you realize the problem was your prompt**: Revert, rethink the prompt, and encode the lesson into `rules.md` — because the best long-term fix is improving the system, not just the one-off request.
- **When you want to improve your prompting ability**: Ask the AI to help you write a better prompt for itself — because the model can often explain what context or structure it needed.
- **When you are trying to become a professional vibe coder**: Build in public and share your work, failures, and learnings — because Lazar’s role emerged from doing the job publicly before being hired.
- **When you are deciding whether to learn traditional coding first**: Focus on judgment, clarity, and taste instead of spending all your energy learning to code from scratch — because AI can generate code; the scarce skill is deciding what to build and how it should feel.

## Contrarian Takes
- **Conventional**: You need a technical background to build software well. → **Their view**: Not having a technical background can be an advantage — because you are less likely to assume something is impossible.
- **Conventional**: The main skill in AI-assisted building is coding faster. → **Their view**: The real skill is clarity, judgment, and taste — because coding is increasingly commoditized.
- **Conventional**: You should fix issues by iterating in the same chat until the agent gets it right. → **Their view**: Starting over with better context is often cheaper and faster — because early clarity saves tokens, time, and rework.
- **Conventional**: You should optimize for the fastest raw output from AI. → **Their view**: Optimize for planning speed and decision quality — because fast output without clarity just creates garbage faster.
- **Conventional**: Software engineers will disappear as AI improves. → **Their view**: Elite engineering becomes even more important — because more builders increases the need for maintenance, security, and reliability.
- **Conventional**: Tech stack choice is a major differentiator. → **Their view**: Tech stack matters far less than quality, taste, and user experience — because users care about the final experience.

## Notable Quotes
> “AI, regardless of your background, is an amplifier. If you don't know what you're doing, you're just going to produce garbage faster.”

> “We won't be rewarded in the world of AI for faster raw output; we will be rewarded for better judgment.”

> “Coding is going to be like calligraphy.”