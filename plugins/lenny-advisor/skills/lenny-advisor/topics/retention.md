# Retention

## Overview
Retention is about getting users to come back because they repeatedly experience product value. It matters because durable growth usually comes from improving activation, habit formation, and repeat use—not just acquiring more users. Across the experts, retention is treated as a product, onboarding, and lifecycle problem that should be measured, modeled, and improved systematically.

## Key Expert Perspectives

- **Elena Verna** (Lovable, ex-Miro, Dropbox): Adjacent User Theory for expanding retention to new segments; Product-Market Fit Treadmill for maintaining retention in fast-moving markets; Growth Loops where retention feeds acquisition. See `experts/elena-verna.md`.
- **Bangaly Kaba** (YouTube, ex-Instagram, Facebook): Understand-Identify-Execute for diagnosing retention problems before shipping fixes; Adjacent User Theory for why new cohorts retain worse. See `experts/bangaly-kaba.md`.
- **Albert Cheng** (Chess.com, Grammarly): Explore and Exploit for finding retention breakthroughs; gamification pillars; freemium sampling to drive paid retention.
- **Adam Fishman** (ex-Patreon, Wyzant): Onboarding as the first retention lever; productizing manual interventions.

## Key Frameworks

### Adjacent User Theory (Bangaly Kaba, Elena Verna)
- **When to use**: When power users retain well but newer or broader cohorts show declining retention, signaling the product does not fit the next wave of users.
- **Steps**:
  1. Define the current core user and why they retain.
  2. Identify the next adjacent user already touching the product.
  3. Observe how their behavior and retention differ from core users.
  4. Use the product from their perspective with a fresh account.
  5. Adapt onboarding, activation, or use cases to fit their needs.
- **Example**: At Instagram, users in new markets had different phones and lower tech familiarity, and retention degraded even without product changes. The product needed to fit the adjacent user better. (Bangaly Kaba)

### Product-Market Fit Treadmill (Elena Verna)
- **When to use**: When operating in fast-moving categories (especially AI) where retention can decay as customer expectations shift and competitive alternatives emerge.
- **Steps**:
  1. Assume product-market fit is temporary, not durable.
  2. Track changes in model capabilities and customer expectations continuously.
  3. Make forward-looking product bets before the next shift arrives.
  4. Recapture product-market fit repeatedly, then scale in short bursts.
  5. Avoid assuming that past retention guarantees future retention.
- **Example**: At Lovable, Elena says the team has to "recapture product market fit every three months" because both LLM capabilities and user expectations keep shifting.

### Onboarding as Promise Delivery (Adam Fishman)
- **When to use**: When improving activation, early retention, or first-time user experience.
- **Steps**:
  1. Treat onboarding as the first proof that the product delivers on its market promise.
  2. Focus on the universal surface every user sees.
  3. Use onboarding to learn who the user is and whether they are a good fit.
  4. Optimize for habit formation and downstream retention, not just completion.
  5. Revisit onboarding only when you have new customer or product insights.
- **Example**: At Patreon, onboarding improvements and human-guided interventions increased creators’ first- and second-month revenue by 25%.

### Human Intervention to Productized Defaults (Adam Fishman)
- **When to use**: When manual onboarding or sales-assist is working and you want to scale it.
- **Steps**:
  1. Identify high-potential users from onboarding signals.
  2. Route them to humans who can help them succeed.
  3. Observe what those humans do repeatedly.
  4. Turn those behaviors into product defaults, recommendations, and guardrails.
  5. Keep choice, but make the right path easier.
- **Example**: Patreon used human help for creators with strong external audiences, then productized the learnings into opinionated defaults like recommended tier counts and pricing.

### Proxy Metrics for Onboarding Experiments (Adam Fishman)
- **When to use**: When retention outcomes take too long to measure directly.
- **Steps**:
  1. Find an early behavior that predicts long-term success.
  2. Use it as the primary experiment metric.
  3. Validate it with qualitative review of who is progressing.
  4. Balance conversion against retention, not conversion alone.
- **Example**: Patreon used velocity to first patron and first $100 processed as early indicators of creator success.

### Explore and Exploit (Albert Cheng)
- **When to use**: When retention work has plateaued or you need to decide between new hypotheses and scaling a known win.
- **Steps**:
  1. Explore broadly to find the right problem or insight.
  2. Identify a breakthrough from experiments or user behavior.
  3. Exploit by concentrating resources on that insight.
  4. Share the learning across adjacent surfaces.
  5. Return to exploration when tests stop producing meaningful signal.
- **Example**: Chess.com found users reviewed games after wins more than losses, then redesigned the post-game experience, increasing reviews by 25%, subscriptions by 20%, and retention.

### Growth as Connecting Users to Product Value (Albert Cheng)
- **When to use**: When defining retention work across the user journey.
- **Steps**:
  1. Map acquisition, activation, engagement, and retention.
  2. Define value at each stage.
  3. Remove friction between users and value.
  4. Design experiments that help users reach value faster.
  5. Reassess value as user needs evolve.
- **Example**: Grammarly increased perceived value by sampling premium suggestions in the free experience.

### Freemium Sampling / Reverse Free Trial in Real Time (Albert Cheng)
- **When to use**: When free users undervalue the paid product.
- **Steps**:
  1. Measure what free users see and ignore.
  2. Find where the free experience underrepresents value.
  3. Sample premium features inside the free workflow.
  4. Intermix free and paid value.
  5. Paywall after users have felt the premium benefit.
- **Example**: Grammarly interspersed premium tone and clarity suggestions into the free product, nearly doubling upgrade rates.

### Gamification Pillars: Core Loop, Metagame, Profile (Albert Cheng)
- **When to use**: When building habit-forming products.
- **Steps**:
  1. Tighten the core loop.
  2. Add long-term goals through a metagame.
  3. Build a profile that reflects user progress.
  4. Make the three reinforce each other.
- **Example**: Duolingo combined lessons and streaks with leaderboards, progression, and a progress-rich profile.

### Understand, Identify, Execute (Bangaly Kaba)
- **When to use**: When retention is weak and the team is tempted to ship before understanding the problem.
- **Steps**:
  1. Understand the root cause first.
  2. Reserve roadmap space for understanding work.
  3. Use data, research, and instrumentation to de-risk the problem.
  4. Identify the right solution opportunities.
  5. Execute while continuing to learn.
- **Example**: Instagram first instrumented the signup funnel to see where users dropped off before making major changes.

## Decision Guide
- If **new users drop off early**, consider **Onboarding as Promise Delivery** because onboarding is the first retention lever — per **Adam Fishman**.
- If **manual support improves outcomes**, consider **Human Intervention to Productized Defaults** because human behavior can reveal scalable product patterns — per **Adam Fishman**.
- If **you need faster readouts on onboarding tests**, consider **Proxy Metrics for Onboarding Experiments** because long-term retention is too slow to wait for — per **Adam Fishman**.
- If **your retention work has hit diminishing returns**, consider **Explore and Exploit** because you may need a new insight, not another tweak — per **Albert Cheng**.
- If **users do not understand the product’s value**, consider **Growth as Connecting Users to Product Value** because retention improves when users reach value faster — per **Albert Cheng**.
- If **free users are not converting or retaining into paid behavior**, consider **Freemium Sampling / Reverse Free Trial in Real Time** because users need to experience premium value firsthand — per **Albert Cheng**.
- If **your product depends on repeated use**, consider **Gamification Pillars** because core loops and progression create habit — per **Albert Cheng**.
- If **the team is shipping lots of features but retention is flat**, consider **Understand, Identify, Execute** because the team may be solving the wrong problem — per **Bangaly Kaba**.
- If **you are deciding whether to optimize conversion or retention**, bias toward **retention and qualified activation** because raw conversion can attract poor-fit users — per **Adam Fishman**.
- If **you have a successful manual process**, consider **productizing it** because the best retention improvements often come from scaling what already works — per **Adam Fishman**.
- If **you are seeing strong power-user retention but weak new-user retention**, consider **Adjacent User Theory** because the next cohort likely needs a different experience — per **Bangaly Kaba** and **Elena Verna**.
- If **retention is decaying in a fast-moving market**, consider the **Product-Market Fit Treadmill** because past PMF does not guarantee future retention — per **Elena Verna**.
- If **your product is mature and reactivation matters**, consider **resurrection experiences** because returning users can be a major retention source at scale — per **Albert Cheng**.

## Expert Consensus
- Retention is driven by **delivering value quickly and repeatedly**, not by acquisition alone.
- **Onboarding matters disproportionately** because it shapes first impressions, activation, and habit formation.
- Teams should optimize for **qualified users and durable behavior**, not just top-of-funnel conversion.
- **Instrumentation and proxy metrics** are essential because retention feedback loops are often too slow.
- The best retention gains often come from **understanding user psychology and behavior**, then productizing what works.

## Points of Debate
- **Optimize conversion vs. optimize retention**
  - **Conversion-first view**: Reduce friction to get more users through onboarding.
  - **Retention-first view** (Adam Fishman, Albert Cheng): Add the right friction, qualify users, and optimize for downstream value and habit.
- **Manual vs. automated onboarding**
  - **Automation-first view**: Manual support does not scale.
  - **Productization view** (Adam Fishman): Manual intervention is valuable because it reveals the winning patterns to encode in product defaults.
- **More experimentation vs. more understanding**
  - **Ship-more view**: Faster testing means faster growth.
  - **Understand-first view** (Bangaly Kaba): Teams should reserve time for root-cause analysis or they will keep optimizing the wrong thing.
- **New-user retention vs. resurrection**
  - **New-user focus**: Acquisition and activation are the main growth levers.
  - **Lifecycle focus** (Albert Cheng): Mature products often get more leverage from existing-user retention and reactivation.

## Key Metrics & Benchmarks
- **Patreon**: onboarding improvements and human-guided interventions improved creators’ first- and second-month revenue by **25%**.
- **Patreon**: early proxy metrics included **velocity to first patron** and **first $100 processed**.
- **Chess.com**: changing the post-game review experience increased **game reviews by 25%**, **subscriptions by 20%**, and improved retention.
- **Grammarly**: sampling premium suggestions in the free experience **nearly doubled upgrade rates**.
- **Airbnb**: a market often needed about **300 listings with 100 reviewed listings** to see growth take off; **more than ten reviews** materially changed trust dynamics.
- **Duolingo**: runs **2,600 events per month** with a community team of three, showing how retention can be reinforced by community at scale.

## Notable Quotes
- “Onboarding is the first moment where the product must deliver on the brand promise.”
- “Growth should be defined as connecting users to the value of the product.”
- “Slow down to do understand work so you can speed up later with a higher win rate.”