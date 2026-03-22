# Keith Coleman & Jay Baxter

**Keith Coleman: VP of Product / Product Lead for Community Notes; Jay Baxter: ML Lead / Founding ML Engineer and Researcher for Community Notes** | **X** | Expertise: product-management, ai-strategy, go-to-market, leadership

## Bio
Keith Coleman and Jay Baxter lead the team behind Community Notes, X’s crowdsourced system for adding neutral, high-trust context to misleading posts. Their perspective matters because they built a large-scale trust product that works in a polarized environment by combining product design, machine learning, and radical transparency.

They are especially valuable for anyone building products where legitimacy, neutrality, and public trust matter more than raw engagement. Their work shows how to design systems that can harness ordinary users, not just experts, to produce reliable outcomes at internet scale.

## Signature Frameworks

### Bridging-based agreement algorithm
- **When to use**: When you need trustworthy, neutral content in polarized environments where majority vote would be biased or manipulable.
- **Steps**:
  1. Let contributors propose notes on potentially misleading posts.
  2. Collect ratings from a broad contributor base.
  3. Model which users tend to disagree historically.
  4. Promote notes only when people who usually disagree both find them helpful.
  5. Filter out notes that also attract meaningful “incorrect” signals.
  6. Downweight ratings from contributors whose behavior conflicts with bridging-based consensus.
- **Example**: A note clarifying that a viral image is from a different year or country is shown only if people from opposing viewpoints both rate it as helpful.

### Thermal team model
- **When to use**: When building a high-ambiguity, zero-to-one product inside a large company that would otherwise be slowed by bureaucracy.
- **Steps**:
  1. Assign one clear founder-like owner.
  2. Give that owner one senior decision-maker outside the team.
  3. Staff a very small, fully dedicated cross-functional team.
  4. Let the team use its own planning and execution process.
  5. Fund the effort milestone by milestone.
  6. Preserve autonomy so iteration happens in days, not quarters.
- **Example**: Community Notes began with a tiny dedicated team across backend, frontend, ML, design, and research, with Keith as the clear driver.

### Proof-at-every-step product validation
- **When to use**: When introducing a controversial or counterintuitive product idea that stakeholders won’t trust without evidence.
- **Steps**:
  1. Test the concept with mockups.
  2. Run small-scale experiments to verify the task is doable.
  3. Pilot with a limited real-world contributor set.
  4. Measure quality before expanding.
  5. Use each success to justify the next stage.
  6. Keep quality thresholds conservative until trust is established.
- **Example**: The team tested Figma mockups, then MTurk-style experiments, then a 1,000-person public pilot before broader rollout.

### Open-source trust architecture
- **When to use**: When product legitimacy depends on public trust and accusations of hidden bias would undermine adoption.
- **Steps**:
  1. Open-source the ranking and scoring code.
  2. Publish ratings and note data regularly.
  3. Make the system reproducible, not just inspectable.
  4. Design it so outsiders can actually run it.
  5. Invite external audits and criticism.
  6. Treat transparency as a product feature.
- **Example**: Community Notes publishes code and daily data so outsiders can verify the algorithm; Jay notes it can be run with enough RAM.

## Core Advice
- **When majority voting would be biased**: optimize for agreement among people who usually disagree — because cross-divide agreement is a stronger signal of neutrality than raw popularity.
- **When building a zero-to-one initiative inside a large company**: create a tiny, fully dedicated cross-functional team with one owner and one sponsor — because speed and ownership beat bureaucracy.
- **When stakeholders are skeptical of a novel idea**: prove it in stages with increasingly realistic experiments — because evidence lowers resistance and reduces risk.
- **When output quality affects trust**: be conservative on thresholds, even if fewer items ship — because one bad output can do more damage than many missing ones.
- **When contributors may fear harassment or social pressure**: allow pseudonymous participation — because people contribute more honestly when protected from identity pressure.
- **When planning slows discovery work**: set goals by the next meaningful milestone, not rigid quarterly rituals — because product discovery is uneven and iterative.
- **When a small team is resource-constrained**: delete code and systems aggressively — because maintenance burden compounds and simplicity increases speed.
- **When staffing a mission-critical initiative**: let people self-select onto the team — because opt-in teams have stronger motivation and resilience.
- **When fighting misinformation at scale**: attach context directly to the content — because claim-specific, zero-click context is more discoverable and behavior-changing.
- **When tempted to equate scope with impact**: choose the role where you can build the most meaningful thing — because direct problem-solving often matters more than managing headcount.

## Contrarian Takes
- **Conventional**: Professional fact-checkers or journalists are required to evaluate misinformation. → **Their view**: ordinary users can produce high-quality context if the system rewards bridging disagreement — because neutrality is the key signal, not expert status.
- **Conventional**: Trust-and-safety systems should stay closed-source to prevent manipulation. → **Their view**: open-sourcing code and data increases trust and can still work — because transparency enables verification and external scrutiny.
- **Conventional**: Real-name identity improves quality and accountability. → **Their view**: pseudonymity can improve honesty and cross-partisan agreement — because it reduces harassment and social signaling pressure.
- **Conventional**: Bigger teams, more managers, and more process create more impact. → **Their view**: small, lean, founder-like teams often outperform — because ownership and iteration speed matter more.
- **Conventional**: Polarized topics have no shared facts. → **Their view**: there is often substantial agreement on verifiable facts even in polarized contexts — because Community Notes repeatedly finds cross-divide consensus.
- **Conventional**: The main misinformation fix is downranking or moderation. → **Their view**: visible context alone can dramatically reduce sharing — because users react to credible context at the point of consumption.

## Notable Quotes
> “We actually look for agreement from people who have disagreed in the past.”

> “We want all of humanity to participate.”

> “It’s the internet, it’s of the internet, that’s why it works.”