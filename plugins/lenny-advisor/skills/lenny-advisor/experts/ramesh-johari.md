# Ramesh Johari

**Stanford professor; startup advisor; former research scientist and data science leader at oDesk/Upwork** | **Stanford University** | Expertise: marketplaces, data science, experimentation, causal inference

## Bio
Ramesh Johari studies how marketplaces actually work: how matching, incentives, trust, and data interact to create liquidity and value. His perspective matters because he combines rigorous academic thinking with hands-on experience building and advising marketplace businesses, especially from his time at oDesk/Upwork.

He is especially useful when teams need to understand whether they are truly building a marketplace, how to use data science to improve it, and how to run experiments that produce real learning rather than just short-term metric wins.

## Signature Frameworks

### The marketplace data science flywheel
- **When to use**: When building or optimizing a marketplace and you need a mental model for where data creates value.
- **Steps**:
  1. Find potential matches across the two sides of the market.
  2. Make the match by ranking, triaging, or recommending the best counterpart.
  3. Learn from the match through ratings, feedback, and passive signals.
  4. Feed the new information back into future matching and discovery.
- **Example**: On Airbnb, the platform helps guests find listings, helps rank which listings to show, and then uses reviews and behavior signals to improve future matching.

### Start with the friction, not the marketplace label
- **When to use**: When evaluating a new startup idea that might become a marketplace later.
- **Steps**:
  1. Identify the specific transaction cost or trust problem users face.
  2. Solve that problem in the simplest way possible, even if it is not yet a true marketplace.
  3. Use the initial wedge to create liquidity or trust on one side.
  4. Only later decide whether the business should evolve into a marketplace/platform.
- **Example**: UrbanSitter began by solving the friction of paying babysitters with credit cards, then expanded into trusted introductions and sitter discovery.

### Scaled liquidity test
- **When to use**: When deciding whether you are truly operating a marketplace or just a startup with one-sided traction.
- **Steps**:
  1. Ask whether you have many buyers and many sellers on the platform.
  2. If you only have one side scaled, treat that as a choice point rather than a marketplace conclusion.
  3. Use the strong side to attract the weak side through subsidies, incentives, or distribution.
  4. If neither side is scaled, focus on scaling one side first instead of calling it a marketplace.
- **Example**: Uber used free-ride coupons and event-based subsidies to build rider demand on top of a driver base in a new city.

### Prediction vs decision-making
- **When to use**: When a data team is building models and you want them to create business value rather than just accurate forecasts.
- **Steps**:
  1. Use machine learning to predict outcomes or rank options.
  2. Translate the prediction into a decision the business can actually make.
  3. Ask whether the decision changes outcomes, not just whether it correlates with past behavior.
  4. Prefer causal questions over purely predictive ones when choosing actions.
- **Example**: A model that predicts which job applicant is most likely to be hired is useful, but the real question is whether ranking applicants that way leads to better hires and better business outcomes.

### Experimentation as learning, not winning
- **When to use**: When running A/B tests in a marketplace or product organization.
- **Steps**:
  1. Define the hypothesis and what you want to learn before launching the test.
  2. Avoid judging experiments only by winners and losers.
  3. Run tests long enough to answer the question, but not so long that you become overly conservative.
  4. Use results to update organizational beliefs, not just to produce quarterly wins.
- **Example**: A badging experiment may not increase bookings immediately, but it can still teach you how attention and inventory are being reallocated.

### Quantified decision-making
- **When to use**: When experiment results are incomplete, noisy, or too short-term to capture the full business effect.
- **Steps**:
  1. Combine experiment data with leadership judgment and prior beliefs.
  2. Acknowledge that some important effects are hard to measure directly.
  3. Use the data to narrow the range of plausible outcomes.
  4. Make the bet based on both evidence and informed belief.
- **Example**: For Superhost, short-term booking impact may have looked flat, but leadership could still weigh the likely retention and host-satisfaction benefits.

### Bayesian accumulation of learning
- **When to use**: When your company runs many experiments and you want past learning to improve future decisions.
- **Steps**:
  1. Capture prior knowledge from previous experiments and business experience.
  2. Combine that prior with the new experiment result.
  3. Use the updated belief to inform future tests and decisions.
  4. Reward teams for contributing useful information, even when a test does not produce a win.
- **Example**: A failed experiment on a button color can still move the prior and influence how future experiments are interpreted.

### Design ratings for distributional fairness
- **When to use**: When building review or rating systems in a marketplace.
- **Steps**:
  1. Recognize that simple averages can disadvantage new participants.
  2. Account for rating inflation and reciprocity effects.
  3. Consider renorming labels or using expectation-based questions instead of raw stars.
  4. Use priors or other smoothing methods to avoid punishing newcomers for a single bad review.
- **Example**: A new seller with one negative review may be unfairly crushed by a raw average; a prior can soften that effect and keep them viable in the market.

## Core Advice
- **When you are starting a company that might become a marketplace**: Solve the underlying friction or trust problem first, even if the first product is not a marketplace at all — because marketplaces only make sense once there is enough liquidity on both sides.
- **When you do not yet have buyers and sellers both active**: Do not call yourself a marketplace yet; focus on scaling one side or solving a non-marketplace startup problem first — because the marketplace value proposition is not present without scaled liquidity.
- **When one side of your marketplace is strong and the other is weak**: Use the strong side to attract the weak side through subsidies, incentives, or distribution — because that creates the flywheel that eventually produces true marketplace liquidity.
- **When you are designing a marketplace data team**: Make sure the team is helping the business make decisions, not just producing predictions — because prediction is correlation, while business value comes from causal decisions.
- **When you are choosing what to optimize with data science**: Prioritize the highest-friction marketplace problem, such as search, pricing, or matching — because data science creates the most leverage where it reduces the biggest transaction-cost bottleneck.
- **When you are evaluating an experiment**: Ask what the test teaches you, not just whether it won — because many marketplace changes redistribute attention and inventory, so learning matters more than the immediate metric.
- **When your experimentation culture rewards only wins**: Shorten low-value tests and be willing to run riskier experiments that may fail but teach more — because overly conservative incentives reduce learning velocity.
- **When you are designing ratings and reviews**: Avoid relying only on raw averages; use priors, expectation-based questions, or other smoothing methods — because averages can unfairly punish new participants and amplify distortion.
- **When you are interpreting missing reviews**: Treat silence as data and analyze non-response, not just submitted ratings — because the absence of a review can predict downstream performance and satisfaction.
- **When you are tempted to over-automate data science with AI**: Use AI to expand the set of hypotheses and options, but keep humans in the loop to decide what matters — because AI increases possibilities, which makes judgment more important.
- **When you are moving fast on product or marketplace decisions**: Slow down enough to build a real mental model of how the market works — because speed without understanding leads to shallow roadmaps and weak decisions.

## Contrarian Takes
- **Conventional**: A marketplace founder is someone who starts a marketplace business from day one. → **Their view**: Almost no business starts as a marketplace; first you solve a specific friction, and only later might it become a marketplace — because without scaled liquidity on both sides, the core marketplace value proposition does not yet exist.
- **Conventional**: If a data model predicts well, it is a good decision tool. → **Their view**: Good prediction is not the same as good decision-making; the real question is causal impact — because a model can fit history without telling you whether an action improves outcomes.
- **Conventional**: Experimentation should be judged by winners and losers. → **Their view**: Experiments should be judged by learning, even when they do not produce a win — because marketplace changes often have redistribution effects that are informative even when short-term metrics are flat.
- **Conventional**: More experimentation automatically means better decisions. → **Their view**: Experimentation can become too conservative and too slow if incentives reward only quarterly wins — because teams then avoid risky but valuable tests.
- **Conventional**: Raw star averages are a fair and sufficient rating system. → **Their view**: Averages can be deeply unfair, especially to new participants, and can distort marketplace dynamics — because early reviews, reciprocity, and inflation make naive averaging misleading.
- **Conventional**: AI will automate away much of data science and reduce the need for humans. → **Their view**: AI expands the space of ideas so much that human judgment becomes more important — because the bottleneck shifts to deciding which hypotheses and experiments matter.

## Notable Quotes
> “Marketplaces are a little bit like a game of whac-a-mole.”

> “It's almost never about building a marketplace when you're building a marketplace.”

> “What AI has done for us is it's massively expanded the frontier of things we could think about our problem.”