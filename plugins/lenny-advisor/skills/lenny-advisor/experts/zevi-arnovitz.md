# Zevi Arnovitz

**Product Manager** | **Meta** | Expertise: AI-assisted product building, non-technical prototyping, prompt/workflow design, product management

## Bio
Zevi Arnovitz is a PM at Meta and former PM at Wix who built a practical, AI-first way to ship products without a traditional technical background. His perspective matters because he has turned AI from a novelty into a repeatable operating system for product work: capturing ideas, exploring constraints, planning, building, reviewing, and learning.

He is especially valuable for non-technical builders and PMs who want to move from “AI can help me brainstorm” to “AI can help me ship real features with quality.”

## Signature Frameworks

### AI-native product build workflow
- **When to use**: When you want to turn an idea into a real feature or product with AI while keeping structure and quality high.
- **Steps**:
  1. Capture the idea quickly as an issue in Linear while you are mid-work.
  2. Run an exploration phase to clarify the problem, current codebase context, and implementation constraints.
  3. Create a concise markdown plan with tasks, status, and critical decisions.
  4. Execute the plan in the codebase using the appropriate model/tool for the task.
  5. Manually QA the feature locally before release.
  6. Run multiple AI code reviews from different models.
  7. Run peer review by having one model critique another model's output.
  8. Update documentation and tooling so the same mistake is less likely to happen again.
- **Example**: For StudyMate, Zevi captured a feature request for fill-in-the-blank questions in Linear, explored the implementation with Claude, generated a markdown plan, executed it with Cursor/Composer, then reviewed and documented the changes.

### Progressive tool graduation
- **When to use**: When you are non-technical or intimidated by code and want to build confidence gradually.
- **Steps**:
  1. Start in ChatGPT or Claude projects to stay in chat mode and learn the basics.
  2. Move to Bolt or Lovable for simple app-building with guided opinions.
  3. Graduate to Cursor in light mode once you need more control.
  4. Use terminal and darker, more direct dev workflows only after you are comfortable.
  5. Switch tools when you outgrow the previous one rather than forcing everything into one tool.
- **Example**: Zevi started with GPT projects, then used Bolt/Lovable, and later moved to Cursor with Claude Code when he needed more control for payments and more complex product work.

### Model specialization and multi-model review
- **When to use**: When you want higher-quality output by using different AI models for different strengths.
- **Steps**:
  1. Use one model for exploration and planning.
  2. Use a fast model like Cursor Composer for quick implementation tasks.
  3. Use a strong UI model like Gemini for front-end work.
  4. Use Codex and Claude to independently review the same code.
  5. Compare the reviews and resolve disagreements through peer review.
  6. Keep the model that is best at the specific task rather than expecting one model to do everything.
- **Example**: Zevi described using Composer for speed, Gemini for UI, Claude for collaborative planning, and Codex for catching hard bugs.

### Learning opportunity loop
- **When to use**: When you encounter something technical you do not understand and want to learn quickly without getting lost.
- **Steps**:
  1. Invoke a dedicated learning prompt or command.
  2. Tell the model you want the 80/20 explanation and that you are a technical PM in the making.
  3. Ask it to explain the current architecture, decision, or bug in plain language.
  4. Use the explanation to build enough understanding to continue the work.
  5. Repeat whenever you hit a new knowledge gap.
- **Example**: Zevi uses `/learning opportunity` when he does not understand a database or architecture issue and wants Claude to explain it using the 80/20 rule.

### Postmortem-driven prompt/tooling improvement
- **When to use**: When AI makes a mistake repeatedly and you want the workflow to improve over time.
- **Steps**:
  1. Notice the failure or bad output.
  2. Ask the model what in the prompt, tooling, or system instructions caused the mistake.
  3. Identify the root cause rather than just fixing the symptom.
  4. Update the relevant command, documentation, or tooling.
  5. Retest so the same error is less likely to recur.
- **Example**: After Claude made a bad implementation choice, Zevi asked what in the system prompt caused it and then updated the workflow so the mistake would not happen again.

### AI interview prep stack
- **When to use**: When preparing for a competitive interview and you want both AI practice and human feedback.
- **Steps**:
  1. Create a project that acts as your coach.
  2. Feed it the best frameworks and information you can find.
  3. Mock interview with the model repeatedly.
  4. Use external question banks and analyze which questions appear most often.
  5. Prioritize practice based on frequency and difficulty.
  6. Do human mock interviews for the highest-stakes preparation.
  7. Ask the model for direct feedback and perfect-answer examples.
- **Example**: For Meta interviews, Zevi built a Claude project coach, used a question bank to prioritize practice, and still did human mocks because they were the most valuable.

## Core Advice
- **When you have an idea or bug while already in the middle of building something**: Use a quick capture command to turn it into a Linear issue immediately — because this preserves flow and ensures the idea is not lost.
- **When you are non-technical and code feels intimidating**: Start in chat-based AI projects before moving into full coding environments — because a gentler interface reduces fear and helps you learn the concepts first.
- **When a feature touches payments, databases, or other high-risk systems**: Spend extra time on exploration and planning before writing code — because rushing straight into implementation creates gnarly bugs and bad technical decisions.
- **When you want AI to act like a real technical partner**: Give it a strong role prompt that tells it to challenge you and not be a people pleaser — because models can otherwise validate bad assumptions.
- **When you are building a feature and need clarity on what to do next**: Run an exploration phase before asking for a plan — because exploration helps the model understand the codebase, the problem, and the constraints.
- **When you are ready to implement a feature**: Convert the discussion into a markdown plan with clear tasks and status tracking — because a written plan makes execution easier and creates a durable artifact.
- **When you need to move fast on straightforward implementation work**: Use the fastest capable model for the task instead of one model for everything — because different models have different strengths and speed matters.
- **When you are reviewing AI-generated code**: Do not rely on a single review; have multiple models review the same branch — because different models catch different classes of mistakes.
- **When AI keeps making the same mistake**: Ask the model to diagnose the root cause and then update the prompt or docs — because fixing the workflow prevents repeated errors.
- **When you are using AI to produce work for others**: Own the output and do not treat AI as an excuse for low quality — because the responsibility is still yours.
- **When you are a junior PM or early-career builder**: Use AI to get reps in strategy, messaging, and product thinking beyond your current job scope — because side projects accelerate learning.
- **When you are preparing for a hard interview**: Use AI for practice and feedback, but still do human mock interviews — because human mocks best simulate real pressure and nuance.

## Contrarian Takes
- **Conventional**: Non-technical people should not try to build real products or ship code. → **Their view**: AI makes it realistic for non-technical PMs to build significant products, and the barrier is mostly fear and workflow — because the right prompts, tools, and review process can replace a lot of traditional gatekeeping.
- **Conventional**: AI coding tools are mainly about generating code quickly. → **Their view**: The real unlock is planning, exploration, review, and learning — because rushing into code creates bugs and weak decisions.
- **Conventional**: One AI tool should be enough if it is good enough. → **Their view**: You should use multiple models and tools for different strengths and let them review each other — because specialization improves quality and speed.
- **Conventional**: AI assistance weakens PM craft by outsourcing thinking and creating slop. → **Their view**: Used intentionally, AI can make you a better PM by giving you more reps, better feedback, and faster learning — because the danger is passive use, not AI itself.
- **Conventional**: Junior roles are disappearing, so it is a bad time to start early in your career. → **Their view**: It is the best time to be a junior because AI lets you learn faster and build independently — because the learning loop is now much shorter.
- **Conventional**: AI should replace human preparation for interviews and other high-stakes work. → **Their view**: AI is a strong prep partner, but human mocks are still essential — because real human interaction still best simulates the actual environment.

## Notable Quotes
> “If people walk away thinking how amazing you are, you failed. And if people walk away and open their computer and start building, you've succeeded.”

> “I want you to challenge me. I don't want you to be a people pleaser.”

> “It's the best time to be a junior.”