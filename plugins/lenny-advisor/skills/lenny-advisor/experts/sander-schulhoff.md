# Sander Schulhoff

**Founder / researcher in prompt engineering and AI red teaming** | **Learn Prompting / HackAPrompt** | Expertise: prompt-engineering, ai-red-teaming, llm-security, agentic-ai

## Bio
Sander Schulhoff is an early prompt-engineering pioneer who built one of the first prompt engineering guides before ChatGPT launched. He now leads Learn Prompting and HackAPrompt, works with frontier AI labs on model security, and co-authored *The Prompt Report*, a major survey of prompting techniques.

His perspective matters because he sits at the intersection of practical prompting, rigorous research, and adversarial testing. If you care about making LLMs more reliable, harder to jailbreak, or safer in agentic workflows, he is especially worth listening to.

## Signature Frameworks

### Few-shot prompting
- **When to use**: When you want an LLM to imitate a style, format, or task pattern and examples are easier to show than describe.
- **Steps**:
  1. Collect a few high-quality examples of the desired input-output pattern.
  2. Paste the examples into the prompt in a common format the model has seen often.
  3. Provide the new input and ask the model to follow the demonstrated pattern.
- **Example**: Paste a few of your previous emails and ask the model to write a new email in that same style.

### Decomposition
- **When to use**: When a task is complex, ambiguous, or requires multiple checks before a final answer.
- **Steps**:
  1. Ask the model not to answer immediately.
  2. Have it identify the subproblems that must be solved first.
  3. Solve each subproblem one by one, potentially with tools or separate agents.
  4. Combine the sub-results into a final answer.
- **Example**: For a car return-policy chatbot, first determine whether the person is a customer, what car they checked out, the checkout date, and whether the return window is still valid.

### Self-criticism / self-refinement
- **When to use**: When you want a free quality boost on outputs that can be reviewed for correctness or completeness.
- **Steps**:
  1. Ask the model to produce an initial answer.
  2. Ask it to critique its own response for errors, gaps, or weaknesses.
  3. Ask it to revise the answer using its own critique.
- **Example**: Generate an answer, then ask, “Can you go and check your response?” and finally, “Great criticism, implement that.”

### Context-rich prompting
- **When to use**: When the model needs background information to make better judgments, classifications, or recommendations.
- **Steps**:
  1. Include relevant background about the task, domain, user, or organization.
  2. Put the most reusable context near the top of the prompt.
  3. Keep only the information that materially changes the model’s decision-making.
- **Example**: For medical coding, include coded examples plus reasoning; for entrapment detection, paste research definitions and even the professor’s original email to dramatically improve performance.

### Ensembling / mixture of reasoning experts
- **When to use**: When accuracy matters and you can afford multiple model calls or multiple prompt variants.
- **Steps**:
  1. Run the same problem through multiple prompts, roles, or models.
  2. Optionally vary tools or access levels across the runs.
  3. Compare the outputs and select the most common or most reliable answer.
- **Example**: Ask a soccer historian, an English professor, and an internet-enabled model how many trophies Real Madrid has, then take the consensus answer.

## Core Advice

- **When you want to get better at prompting quickly**: do lots of trial and error with real chatbot interactions instead of relying mainly on courses or reading — because hands-on experimentation teaches prompting better than passive learning.
- **When you need a model to imitate a style or format**: use few-shot examples rather than trying to describe the style abstractly — because examples are easier for the model to learn from than vague instructions.
- **When you are formatting examples for a prompt**: use a common, familiar format such as XML or simple Q/A labeling — because formats that appear frequently in training data tend to work better empirically.
- **When a task is too hard to solve in one pass**: ask the model to list the subproblems first, then solve them one by one — because breaking a task into smaller parts improves performance and often helps the human think through the problem too.
- **When you want higher-quality outputs on a task that can be reviewed**: have the model critique its own answer and then revise it — because self-criticism can produce a free performance boost in some situations.
- **When the model needs domain knowledge, user history, or organizational specifics**: provide rich background information, especially at the top of the prompt — because more relevant context can massively improve output quality and top-loaded context is easier to reuse.
- **When you are building a product that uses the same prompt many times per day**: invest much more in prompt quality and robustness than you would in casual chat use — because small failures or improvements scale across many unseen outputs.
- **When you are using modern reasoning models like o3**: do not rely on explicit “think step by step” prompting as much — because those models already do reasoning by default.
- **When you are using older non-reasoning models like GPT-4 or GPT-4o for accuracy-sensitive tasks**: still ask for explicit reasoning or step-by-step thinking if you need robustness — because those models can skip reasoning unless explicitly instructed.
- **When you are tempted to use role prompting for factual accuracy**: skip it; use roles mainly for style or expressive tasks instead — because role prompting does not reliably improve accuracy-based tasks on modern models.
- **When you are trying to defend an AI product from prompt injection**: do not depend on prompt-only defenses like “ignore malicious instructions” or separators around user input — because these defenses do not work in practice.
- **When you need to secure a narrow, well-defined behavior in a model**: use safety-tuning or fine-tuning on targeted malicious examples rather than generic guardrails — because training on the specific harmful patterns you care about is more effective.

## Contrarian Takes

- **Conventional**: Prompt engineering is becoming obsolete as models get better. → **Their view**: Prompt engineering is still very relevant and will remain so — because new models still benefit from better prompting, especially at scale and in product settings.
- **Conventional**: Role prompting makes models smarter or more accurate. → **Their view**: Role prompting does not help accuracy-based tasks on modern models — because studies show no statistically meaningful effect, though it can help with style.
- **Conventional**: Threats, rewards, or “someone will die if you don’t answer” prompts improve performance. → **Their view**: These tricks generally do not work on modern models — because there is no strong large-scale evidence and they are mostly folklore from earlier eras.
- **Conventional**: Prompt injection can be solved with better prompts or a good guardrail layer. → **Their view**: Prompt injection is not solvable in a strong sense; it can only be mitigated — because prompt-based defenses and many guardrails fail.
- **Conventional**: AI security is like classical cybersecurity: find the bug, patch it, and you’re done. → **Their view**: You cannot patch a brain the way you patch software — because models generalize, and new jailbreak variants keep working.
- **Conventional**: AI red teaming is mostly about catastrophic alignment failures. → **Their view**: A major near-term issue is harmful information leakage and agentic misuse — because those are the practical risks showing up now.

## Notable Quotes

> “Prompt engineering is absolutely still here.”

> “You can patch a bug, but you can’t patch a brain.”

> “It’s not solvable. It’s mitigatable.”