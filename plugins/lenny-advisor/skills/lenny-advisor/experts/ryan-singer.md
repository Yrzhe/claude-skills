# Ryan Singer

**Product strategy and product development expert; creator of Shape Up** | **37signals (formerly Basecamp)** | Expertise: product-management, strategy, engineering-management, design

## Bio
Ryan Singer spent 17 years at 37signals building Basecamp and helped create Shape Up, a method for planning and shipping software that emphasizes clarity, constraints, and collaboration. His perspective matters because he has seen how product, design, and engineering can work together without relying on heavy process, endless estimation, or late-stage heroics.

## Signature Frameworks

### Shape Up
- **When to use**: When a team needs a more reliable way to ship meaningful product work without endless estimation, backlog churn, or sprint overrun.
- **Steps**:
  1. Start with an appetite: decide the maximum amount of time you are willing to spend.
  2. Frame the problem: narrow the opportunity to a specific, valuable problem worth solving.
  3. Shape the solution: collaboratively explore options until the idea is clear, bounded, and feasible within the appetite.
  4. Hand off a well-shaped concept to the build team so they can break it into tasks and implement with autonomy.
  5. If the work is no longer on track, stop reinvesting in the unclear version and return to shaping rather than extending blindly.
- **Example**: Instead of saying “build a calendar,” Basecamp framed the problem as helping users see empty spaces in their schedule, then shaped a solution around a two-month dot grid plus an agenda view.

### Framing
- **When to use**: When the initial request is too broad, fuzzy, or solution-shaped and you need to identify the real problem before shaping a solution.
- **Steps**:
  1. Start from the business or customer request.
  2. Negotiate down to the specific problem that matters.
  3. Identify the valuable slice of the opportunity.
  4. Define boundaries so the problem is small enough to shape.
- **Example**: The team did not frame the work as “calendar”; they framed it as “show empty spaces in the agenda view for customers who need to book time.”

### Live shaping session
- **When to use**: When you need to rapidly converge on a buildable idea with product, design, and engineering in the same room.
- **Steps**:
  1. Bring the right people together: product, design, and a senior engineer who knows the system.
  2. Whiteboard or sketch the idea at a low-to-medium fidelity level.
  3. Actively try to break each idea from technical and customer-value angles.
  4. Explore multiple approaches instead of getting stuck on one path.
  5. Use the session to surface unknowns, trade-offs, and hidden complexity before committing.
- **Example**: For the calendar feature, the group explored a dot-grid month view, a scrolling agenda view, navigation, and creation flows until they had a version everyone could understand and build.

### Breadboarding / fat-marker sketching
- **When to use**: When you need to communicate the mechanics of a feature clearly without jumping to high-fidelity design too early.
- **Steps**:
  1. Sketch the core flow and moving parts.
  2. Show how the user moves from one state to another.
  3. Represent logic and transitions clearly enough for engineers to understand.
  4. Avoid polished visuals that obscure the underlying mechanics.
- **Example**: Ryan described a shaped calendar as a simple diagram showing the two-month grid, agenda view, navigation, and create button—not a final Figma mockup.

### Kickoff implementation mapping
- **When to use**: When a shaped project is handed to the build team and you want to verify the team understands the scope before coding.
- **Steps**:
  1. Take the shaped concept and have builders translate it into major implementation chunks.
  2. Use a small fixed number of boxes to force clarity.
  3. Let senior engineers coach junior engineers on implementation choices.
  4. Use the mapping exercise to detect over-scope early.
- **Example**: Ryan suggested drawing nine boxes for the nine major implementation chunks; if the team cannot fit it into nine or fewer, it is probably too big.

## Core Advice
- **When a project keeps dragging and never seems to end**: set a fixed appetite and shape the work to fit it — because a fixed time budget forces hard trade-offs early and prevents endless one-more-sprint behavior.
- **When a request is broad like “build a calendar” or “build a dashboard”**: negotiate the problem down to a specific customer need before discussing solutions — because broad requests create ever-expanding scope and make it impossible to shape something finishable.
- **When you want the team to work autonomously during a time box**: do more shaping up front so the build team has enough clarity to make decisions without constant escalation — because autonomy only works when the team understands the problem, the solution shape, and the trade-offs.
- **When engineers keep saying they do not have enough context**: bring engineering into shaping instead of handing them a PRD or Figma file after the fact — because the people who understand the system can surface hidden complexity before the project starts.
- **When a feature seems simple on the surface**: open up the code, architecture, or workflow early to look for hidden branches, dependencies, and time bombs — because many projects fail because the surface-level UI hides complicated backend or integration realities.
- **When your team is junior or mixed in experience**: add more detail and coaching in the shaped concept, then gradually reduce guidance as the team proves capability — because detail is a dial; junior builders often need more direction to avoid getting lost and hiding confusion.
- **When a senior builder wants to influence the fundamental approach**: include that person in shaping rather than trying to over-specify the implementation for them later — because people are most effective when they contribute where their judgment matters most.
- **When you are tempted to use high-fidelity Figma as the output of planning**: use low-to-medium fidelity sketches or breadboards that communicate mechanics, not polished visuals — because high-fidelity mockups create false confidence and often collapse when engineering reality appears.
- **When a project is too large to fit the appetite**: cut the project down by scope before starting; do not ask the team to “figure it out” after committing — because you cannot put 10 pounds of work into a 5-pound bag and expect a meaningful finish.
- **When a project is not on track near the end of the time box**: do not just extend the deadline; move back into shaping to understand what was missed — because extending time without clarity creates morale damage and debt; re-shaping helps reveal the real unknowns.
- **When your team is spending too much time in rituals and not enough time solving problems**: reduce process overhead by replacing recurring ceremony with a clearer shaping-and-build flow — because many teams are overloaded with meetings because the work itself is insufficiently defined.
- **When product work is stuck because the team cannot see the end**: use a pilot project with a meaningful but bounded problem to test Shape Up before rolling it out broadly — because a pilot lets the team learn the method on a real problem without forcing a full organizational conversion.

## Contrarian Takes
- **Conventional**: Estimate the project first, then define the scope to fit the estimate. → **Their view**: Start with the appetite—the maximum time you are willing to spend—and shape the scope to fit that budget. — because estimating a fuzzy concept hides unknowns; a fixed appetite forces the team to confront trade-offs and feasibility early.
- **Conventional**: A detailed PRD or polished Figma file is the best way to hand off work to engineering. → **Their view**: Those artifacts are often too early and too detached from engineering reality; shaping should happen with engineers in the room. — because without engineering input, the plan often breaks on first contact with implementation constraints.
- **Conventional**: If a project is late, just cut scope at the end to preserve the deadline. → **Their view**: If the project is not on track, do not pretend the cut-down version is the same project; go back to shaping or cancel/rethink it. — because late scope cuts often destroy morale and leave the team with a half-finished, low-value outcome.
- **Conventional**: More process and more tickets create more control and predictability. → **Their view**: Ticket shredding can reduce ownership and obscure the real problem; a well-shaped whole idea gives builders more autonomy and better outcomes. — because people do better when they understand the whole and can make their own implementation decisions.
- **Conventional**: Shape Up is a rigid, all-or-nothing operating model. → **Their view**: You can adopt only the parts that solve your specific problem; it is a toolkit, not a religion. — because different teams have different constraints, and the method should be adapted to the actual pain point.
- **Conventional**: Basecamp’s way of working is the universal model for all companies. → **Their view**: Basecamp was unusually unique: every designer coded, founders stayed close to the work, and there was no sales org competing for engineering time. — because many teams need adaptations to make Shape Up work in real life.

## Notable Quotes
- “We are not going to start something unless we can see the end from the beginning.”
- “You can't put 10 pounds of crap in a five pound bag.”
- “The shaping step is crucial.”