# Ronny Kohavi

**Advisor, instructor, and experimentation expert; former VP and Technical Fellow of Relevance at Airbnb** | **Airbnb (former), Microsoft (former), Amazon (former)** | Expertise: A/B testing, experimentation platforms, product analytics, decision science

## Bio
Ronny Kohavi is one of the most influential voices in online controlled experiments and A/B testing. He has led experimentation and relevance teams at Airbnb, Microsoft, and Amazon, and his work has shaped how large product organizations make decisions with data.

His perspective matters because he focuses not just on whether experiments work, but on whether the entire experimentation system is trustworthy, scalable, and aligned with long-term business value. He is especially valuable when teams need to build an experimentation culture, avoid misleading metrics, or make better product decisions under uncertainty.

## Signature Frameworks

### Test-everything experimentation culture
- **When to use**: When a product team wants to avoid shipping unvalidated changes and build a reliable learning loop.
- **Steps**:
  1. Put every code change or feature into an experiment.
  2. Treat even small bug fixes as potentially impactful.
  3. Expect most ideas to fail and normalize that outcome.
  4. Use experiments to learn from both winners and surprising losers.
  5. Document and share learnings so the organization remembers them.
- **Example**: At Bing, even a small change to ad title layout was tested and turned out to increase revenue by about 12%.

### Overall Evaluation Criterion (OEC)
- **When to use**: When optimizing a product metric could create short-term gains but harm long-term user value.
- **Steps**:
  1. Define the true business objective beyond a single metric like revenue.
  2. Add countervailing metrics that protect user experience and long-term value.
  3. Frame the problem as a constrained optimization problem.
  4. Use metrics such as churn, task success rate, time to successful click, or downstream satisfaction.
  5. Ensure the OEC is causally predictive of lifetime value.
- **Example**: For search ads, Bing used revenue plus guardrails like churn and time to find a successful result rather than optimizing revenue alone.

### One-factor-at-a-time redesign
- **When to use**: When a team wants to launch a major redesign or large bundle of changes.
- **Steps**:
  1. Decompose the redesign into the smallest possible set of factors.
  2. Test one factor at a time when possible.
  3. If a full redesign is unavoidable, allocate a small portion of effort to high-risk bets and expect failure.
  4. Learn from each step and adjust before adding more changes.
  5. Avoid shipping large bundles of unvalidated changes.
- **Example**: Ronny argued that large redesigns often fail and that teams should instead test smaller increments and only launch the parts that prove positive.

### Institutional learning loop
- **When to use**: When an organization runs many experiments and needs to retain knowledge over time.
- **Steps**:
  1. Store experiment history in a searchable system.
  2. Document both successes and failures.
  3. Hold quarterly reviews of the most surprising experiments.
  4. Focus on surprising winners and surprising losers, not just positive results.
  5. Use the archive to check whether similar ideas were already tested.
- **Example**: At Microsoft, teams could search thousands of past experiments by keyword, and Ronny advocated quarterly meetings to review the most interesting outcomes.

### Trustworthy experimentation pipeline
- **When to use**: When building or evaluating an experimentation platform that teams must rely on for decisions.
- **Steps**:
  1. Ensure the platform can safely abort bad launches quickly.
  2. Validate experiment integrity before trusting results.
  3. Detect sample ratio mismatch and other data-quality issues.
  4. Avoid misleading real-time significance monitoring.
  5. Make the final scorecard trustworthy enough that teams can act on it confidently.
- **Example**: Ronny described how early Optimizely-style real-time p-value monitoring inflated false positives and damaged trust.

### Variance reduction for faster experiments
- **When to use**: When you need statistically reliable results faster or with fewer users.
- **Steps**:
  1. Identify metrics with high variance or skew.
  2. Cap extreme values when appropriate.
  3. Use pre-experiment data to adjust estimates.
  4. Apply variance-reduction methods to lower required sample size.
  5. Keep estimates unbiased while improving speed.
- **Example**: For skewed revenue metrics, capping very large purchases can help speed up detection; Ronny also mentioned CUPED as a pre-experiment adjustment method.

## Core Advice
- **When you face a new feature or code change**: Put it into an experiment instead of shipping it directly — because even small changes and bug fixes can have surprising, unintended effects on revenue or user behavior.
- **When you are considering a big, high-risk idea**: Allocate some experimentation budget to it, but expect most such bets to fail — because high-risk ideas can produce home runs, but Ronny’s rule of thumb is that roughly 80% will fail.
- **When you want to improve revenue**: Do not optimize revenue alone; define an OEC with guardrails for user experience and long-term value — because pure revenue optimization can encourage harmful tactics like adding more ads or spamming users.
- **When you are planning a redesign**: Break it into smaller changes and test incrementally rather than launching everything at once — because large redesigns often fail, and incremental testing helps isolate what actually works.
- **When you are early-stage and have limited traffic**: Start building the experimentation culture and platform, but do not expect meaningful A/B testing until you have tens of thousands of users — because below that scale, most metrics lack enough power.
- **When you have around 200,000 users**: Treat that as the point where experimentation becomes much more powerful and worth scaling aggressively — because at that scale, you can detect smaller effects and make experimentation a core operating system.
- **When an experiment result looks unusually good or bad**: Assume it may be wrong and investigate before celebrating or shipping — because Twyman’s law and sample ratio mismatch checks show that extreme results are often caused by bugs or data issues.
- **When you see a statistically significant result with p < 0.05**: Do not interpret it as a 95% chance the treatment is better; consider replication and a lower threshold like 0.01 for higher-stakes decisions — because the common interpretation of p-values is wrong, and false positive risk can be much higher than 5%.
- **When your experiment platform is immature**: Invest in automation and self-serve analysis so teams do not need a data scientist for every readout — because the marginal cost of experimentation should approach zero if the platform is mature enough.
- **When you are trying to speed up experimentation**: Improve the platform so results are available quickly, and use variance reduction techniques to reduce sample size — because faster scorecards and lower-variance metrics shorten the time to decision without sacrificing validity.
- **When you are deciding whether to ship a flat result**: Do not ship unless there is a legal or other unavoidable requirement — because shipping flat adds code complexity and maintenance cost without delivering value.
- **When your organization resists experimentation**: Start with a launch-heavy team like Bing, prove value there, and let successful experimentation spread through cross-pollination — because visible wins and internal mobility help change culture more effectively than abstract arguments.

## Contrarian Takes
- **Conventional**: Experimentation leads to only tiny, incremental optimization and prevents innovation. → **Their view**: You cannot experiment too much; experimentation is compatible with big bets if you intentionally allocate some portfolio to high-risk, high-reward ideas — because small changes can have huge effects, and experiments also reveal when radical ideas fail so teams can move on faster.
- **Conventional**: A statistically significant p-value means there is a 95% chance the treatment is better. → **Their view**: That interpretation is wrong; p-values do not tell you the probability that treatment beats control — because you need Bayes’ rule and a prior success rate to estimate false positive risk, which can be much higher than 5%.
- **Conventional**: If a redesign is well thought out and the team believes in it, it should be launched as a whole. → **Their view**: Large redesigns are usually more likely to fail; do them incrementally or expect to lose — because bundling many changes makes it hard to know what worked, and most individual ideas fail anyway.
- **Conventional**: Real-time p-value monitoring makes experimentation faster and more efficient. → **Their view**: Real-time significance peeking inflates false positives and destroys trust — because stopping when p-values cross a threshold repeatedly increases type I error materially.
- **Conventional**: Revenue is the right primary metric to optimize. → **Their view**: Revenue alone is the wrong objective; you need a long-term OEC tied to lifetime value and user experience — because pure revenue optimization can create short-term gains that damage churn, satisfaction, and long-term growth.
- **Conventional**: If a team has already invested months in a project, it should probably ship to avoid wasting work. → **Their view**: Sunk cost should not justify shipping a bad or flat result — because maintenance cost and user harm matter more than recouping past effort.

## Notable Quotes
> “I'm very clear that I'm a big fan of test everything, which is any code change that you make, any feature that you introduce has to be in some experiment.”

> “The key word is lifetime value, which is you have to define the OEC such that it is causally predictive of the lifetime value of the user.”

> “If the result looks too good to be true, your normal movement of an experiment is under 1% and you suddenly have a 10% movement, hold the celebratory dinner.”