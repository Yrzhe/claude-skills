# Nicole Forsgren

**Partner at Microsoft Research; developer productivity and strategy researcher** | **Microsoft Research** | Expertise: developer productivity, DevOps, measurement, engineering strategy

## Bio
Nicole Forsgren is one of the most influential researchers in software delivery performance, known for creating and popularizing the DORA and SPACE frameworks. Her work matters because she bridges rigorous research with practical engineering strategy, helping teams improve speed, reliability, and developer wellbeing at the same time.

She has worked across IBM, academia, Chef, DORA, GitHub, Google, and Microsoft, giving her a rare cross-industry view of what actually drives high-performing engineering organizations. If you need to measure developer productivity without falling into vanity metrics, her perspective is especially valuable.

## Signature Frameworks

### DORA Four Keys
- **When to use**: Use when you want a simple, benchmarkable view of software delivery performance and a starting point for diagnosing speed vs. stability constraints.
- **Steps**:
  1. Measure lead time for changes.
  2. Measure deployment frequency.
  3. Measure mean time to restore.
  4. Measure change fail rate.
  5. Interpret speed and stability together rather than as tradeoffs.
  6. Use the metrics to identify whether the main constraint is technical capability, process, or business policy.
- **Example**: Elite performance was described as deploy on demand, lead time under a day, time to restore under an hour, and change fail rate between 0% and 15%.

### SPACE
- **When to use**: Use when you need to choose balanced metrics for complex, creative work such as developer productivity, incident management, or developer experience improvements.
- **Steps**:
  1. Define the problem or goal clearly before choosing metrics.
  2. Pick metrics across at least three of the five dimensions to keep balance.
  3. Measure satisfaction and wellbeing with periodic surveys.
  4. Measure performance outcomes relevant to the process or system.
  5. Measure activity counts, but avoid over-weighting them.
  6. Measure communication and collaboration.
  7. Measure efficiency and flow.
  8. Use the selected metrics together to avoid optimizing one dimension at the expense of others.
- **Example**: For improving pull requests, balance code-review time, protected time to work, and a satisfaction survey about the PR process instead of only counting alerts or PR volume.

### Measurement Journey: People Data + Systems Data
- **When to use**: Use when starting measurement from scratch or when existing telemetry is incomplete and you need a practical path to better insight.
- **Steps**:
  1. Start with people data: interviews, surveys, and qualitative feedback.
  2. Collect whatever system data already exists, even if imperfect.
  3. Use people data to identify the real problem and the language teams use.
  4. Use system data to scale measurement and validate patterns over time.
  5. Triangulate both sources; if they disagree, investigate rather than assume the system is right.
  6. Shift toward more system data as instrumentation matures, but keep periodic people data.
- **Example**: A team might see acceptable lead time in systems, but interviews reveal the process is a “Rube Goldberg machine” with heavy heroics that telemetry alone would never show.

### Four-Box Framework
- **When to use**: Use when you need to clarify a hypothesis, define a measurement plan, or separate a bad metric idea from a bad data source.
- **Steps**:
  1. Write the first concept in words.
  2. Write the outcome or second concept in words.
  3. Get agreement from stakeholders on the wording and meaning.
  4. Map each word-based concept to available data sources.
  5. Check whether the data is a true measure or only a proxy.
  6. If the analysis fails, diagnose whether the issue is the wording, the proxy, or the data quality.
- **Example**: For the hypothesis “customer satisfaction leads to return customers,” the top boxes are the words, and the bottom boxes are the data sources such as CSAT/NPS for satisfaction and website return visits or follow-up surveys for return customers.

### Decision Spreadsheet Framework
- **When to use**: Use when making high-stakes decisions such as job choice, location, or strategic prioritization and you want a transparent, weighted process.
- **Steps**:
  1. List all options.
  2. Define the criteria that matter.
  3. Assign relative weights to each criterion so they sum to 100%.
  4. Score each option against each criterion.
  5. Multiply scores by weights to get a total.
  6. Use the result as data-informed input, then apply judgment if needed.
- **Example**: Nicole used criteria like total comp, team, work-life balance, proximity to an airport, tech scene, and food scene to decide where to move or what job to take.

## Core Advice
- **When you face an unclear mandate like “improve developer experience”**: define exactly what you mean before starting work — because teams often spend months solving different problems because they were never aligned on the actual goal.
- **When you want engineering to move faster without sacrificing quality**: ship smaller changes more often and shorten the time between commit and production — because smaller batches reduce blast radius, make debugging easier, and improve both speed and stability.
- **When your org is using long change-approval waits to preserve stability**: replace arbitrary waiting periods with automated testing, good architecture, and fast feedback loops — because speed and stability move together, and batching changes often makes systems less stable.
- **When you need to diagnose why delivery is slow**: measure lead time, deployment frequency, MTTR, and change fail rate, then identify which capability is constraining you — because the four DORA metrics reveal whether the bottleneck is release cadence, recovery, or change quality.
- **When you are choosing metrics for a complex team process**: pick at least three SPACE dimensions instead of relying on a single metric — because balanced measurement prevents gaming and keeps you from optimizing one dimension while harming others.
- **When you are tempted to use easy-to-count engineering metrics**: avoid lines of code, commit counts, or pull request counts as primary productivity metrics — because these are activity metrics, not outcome metrics, and they can distort behavior without reflecting real value.
- **When you want to measure developer sentiment or wellbeing**: use periodic surveys rather than trying to instrument everything continuously — because satisfaction and wellbeing are important leading signals and are best captured directly from people.
- **When system telemetry and employee feedback disagree**: trust the disagreement as a signal and investigate both sources instead of assuming the dashboards are correct — because systems can miss hidden work, heroics, or missing code paths that people can surface.
- **When you are starting measurement from zero**: begin with interviews and surveys, then gradually add system instrumentation as the measurement program matures — because people data is faster to collect early; system data becomes more scalable later.
- **When you are trying to get leadership buy-in for developer productivity work**: translate developer pain into business value, reliability, and strategic outcomes — because executives often need a clear ROI or risk argument before prioritizing engineering experience work.
- **When you are rolling out productivity or DevEx changes**: run the effort both top-down and bottom-up, and use the vocabulary of both leaders and ICs — because adoption improves when leaders understand the business case and engineers feel the work is for them.
- **When you are making a difficult decision**: write down the options, criteria, and weights in a spreadsheet before deciding — because the exercise often reveals the answer and makes tradeoffs explicit.

## Contrarian Takes
- **Conventional**: Long change-approval waits improve stability. → **Their view**: Arbitrary waiting periods often make systems less stable because they batch changes into larger, riskier releases — because smaller, more frequent changes reduce blast radius and make recovery easier.
- **Conventional**: Developer productivity can be measured with simple activity counts like commits, pull requests, or lines of code. → **Their view**: Those are poor primary metrics because they measure activity, not productivity — because they are easy to instrument but can be gamed and do not capture satisfaction, flow, collaboration, or outcomes.
- **Conventional**: If telemetry says the system is fine, that should be enough. → **Their view**: People data is often more accurate than instrumentation for understanding real developer experience — because surveys and interviews reveal heroics, hidden friction, and missing work that systems cannot see.
- **Conventional**: AI tools mainly matter because they cut task time in half, which means you can reduce headcount. → **Their view**: AI productivity is not just about doing the same task faster; it changes the work itself and frees cognitive space for harder problems — because developers spend more time reviewing, learning, and managing trust/reliance.
- **Conventional**: Small companies and large companies need fundamentally different productivity benchmarks. → **Their view**: Company size was not a statistically significant differentiator in the DORA benchmarks — because both small and large companies can face similar delivery constraints.
- **Conventional**: You need perfect data before you can start measuring. → **Their view**: Start with rough, useful data and improve over time — because early measurement can rely on interviews and approximate hunches, then mature into more formal instrumentation.

## Notable Quotes
- “If you're on different pages, you're heading in completely different directions.”
- “When you move faster, you are more stable.”
- “The key to having a good strategy is knowing what not to do.”