# Metrics

## Overview
Metrics are the operating system for product and business decisions. The best teams use them to understand user value, identify bottlenecks, allocate resources, and decide when to explore new opportunities versus double down on what already works. Good metrics should reflect real customer behavior, not vanity movement.

## Key Frameworks

### Explore and Exploit (Albert Cheng)
- **When to use**: When deciding whether to search for new growth opportunities or scale a proven insight.
- **Steps**:
  1. Explore broadly with tests and behavioral analysis.
  2. Look for surprising patterns in user behavior.
  3. Identify a breakthrough insight.
  4. Exploit by concentrating resources on that insight.
  5. Share the learning across teams.
  6. Watch for saturation and return to exploration when tests stop producing signal.
- **Example**: Chess.com found that most users reviewed games after wins, not losses. They redesigned the post-game experience and saw higher reviews, subscriptions, and retention.

### Growth as Connecting Users to Product Value (Albert Cheng)
- **When to use**: When defining growth work and prioritizing across the user journey.
- **Steps**:
  1. Map acquisition, activation, engagement, and retention.
  2. Define user value at each stage.
  3. Organize teams around helping users reach value faster.
  4. Reduce friction between users and value.
  5. Reassess as user needs change.
- **Example**: Grammarly increased monetization by sampling premium value inside the free experience.

### Freemium Sampling / Reverse Free Trial in Real Time (Albert Cheng)
- **When to use**: When free users undervalue paid features because they only see a narrow slice of the product.
- **Steps**:
  1. Measure what free users actually see and ignore.
  2. Find where free experience underrepresents value.
  3. Sample premium features inside the free workflow.
  4. Intermix free and paid value.
  5. Paywall after users have felt the premium benefit.
- **Example**: Grammarly interspersed premium tone and clarity suggestions into the free product, nearly doubling upgrade rates.

### Gamification Pillars: Core Loop, Metagame, Profile (Albert Cheng)
- **When to use**: When building habit-forming products that depend on repeated engagement.
- **Steps**:
  1. Tighten the core loop.
  2. Add a metagame with longer-term goals.
  3. Build a profile that reflects progress and investment.
  4. Make the three reinforce each other.
- **Example**: Duolingo combined lessons, streaks, leaderboards, and progress profiles.

### Experimentation System First (Albert Cheng)
- **When to use**: When you want experimentation to scale beyond isolated tests.
- **Steps**:
  1. Start with a growth model.
  2. Instrument the product well.
  3. Use tooling that fits your scale.
  4. Build observability and repositories for cross-experiment learning.
  5. Share wins to build momentum.
- **Example**: Chess.com’s goal of 1,000 experiments a year was meant to force better tooling, observability, and team participation.

### Goal Detangling to Avoid “Toddler Soccer” (Ami Vora)
- **When to use**: When too many teams are chasing the same top-line metric.
- **Steps**:
  1. Start from the company outcome and customer journey.
  2. Break the top-line metric into input metrics or surfaces.
  3. Assign distinct goals to different teams.
  4. Show how each goal ladders to the company outcome.
  5. Check that metrics still reflect customer value.
- **Example**: Instead of every team chasing GMV, split goals by visits, conversion, and reorder behavior.

### Discover-Discuss-Decide Separation (Annie Duke)
- **When to use**: When group decisions are getting distorted by loud voices or live brainstorming.
- **Steps**:
  1. Collect inputs independently.
  2. Share them before the meeting.
  3. Use the meeting to discuss disagreements.
  4. Decide outside the meeting.
- **Example**: For roadmap planning, each person ranks features before the meeting, then the group discusses differences.

### Make the Implicit Explicit (Annie Duke)
- **When to use**: When decisions rely on intuition, such as hiring, investing, or forecasting.
- **Steps**:
  1. Surface hidden criteria.
  2. Define them explicitly.
  3. Turn them into a rubric.
  4. Record judgments and forecasts.
  5. Review outcomes later.
- **Example**: First Round rated market, founder, and product on a 1–7 scale and forecasted Series A outcomes.

## Decision Guide
- If your tests are producing fewer significant results, consider **Explore and Exploit** because you may have saturated a local optimum — per **Albert Cheng**
- If free users do not convert because they do not understand the paid product, consider **Freemium Sampling** because firsthand exposure changes perceived value — per **Albert Cheng**
- If retention is weak, prioritize **retention work before paywalls or paid acquisition** because the business is easier to scale when users form habits — per **Albert Cheng**
- If dormant users are a large part of your base, invest in **resurrection experiences** because returning users can be a major growth lever — per **Albert Cheng**
- If you do not know what users naturally share, instrument **sharing hotspots** because it is easier to amplify organic behavior than invent it — per **Albert Cheng**
- If beginners feel discouraged early, redesign onboarding to **protect confidence** because early negative reinforcement hurts habit formation — per **Albert Cheng**
- If experimentation is immature, start with **one simple A/B test** because capability compounds only after teams get an initial win — per **Albert Cheng**
- If a crisis changes user needs overnight, use **Wartime Product Management** because the roadmap must reset around mission-critical problems — per **Alex Hardiman**
- If you are building in a trust-sensitive domain, combine **editorial judgment with algorithmic scale** because engagement alone is not a sufficient quality signal — per **Alex Hardiman**
- If your organization is stepping on itself with overlapping goals, use **metric decomposition** because distinct team metrics reduce conflict and improve accountability — per **Ami Vora**
- If a meeting is full of disagreement, use **curiosity-over-ego** because the other person may hold information you do not have — per **Ami Vora**
- If leaders are drowning in detail, use **recommendation-first reviews** because executives should calibrate on principles, not absorb every fact — per **Ami Vora**

## Expert Consensus
- Metrics should measure real user value, not just activity or vanity movement.
- Good metrics systems connect company outcomes to specific user journeys and team responsibilities.
- Teams should use metrics to learn faster, not just to report performance.
- Strong organizations separate exploration from exploitation and know when to switch modes.
- The best metric reviews produce decisions, principles, and accountability, not information overload.

## Points of Debate
- **Growth as metric optimization** (conventional view): Growth teams should maximize conversion, revenue, and engagement directly.  
  **Growth as value connection** (Albert Cheng): Growth should help users reach product value faster, which creates more durable business outcomes.

- **Engagement-first ranking** (conventional view): Algorithms should optimize for clicks and usage.  
  **Editorially informed ranking** (Alex Hardiman): In trust-sensitive products, expert judgment should shape the metrics and signals used by algorithms.

- **Top-line metric ownership** (conventional view): All teams should align on one north-star metric.  
  **Goal detangling** (Ami Vora): One shared metric can create crowding and confusion; teams need distinct input metrics tied to the journey.

- **More strategy, less execution** (conventional view): Senior leaders should spend most of their time on strategy.  
  **Execution-first strategy loop** (Ami Vora): Strategy only matters if it ships; execution creates the feedback needed to improve strategy.

- **Executive decision-making by presentation** (conventional view): Teams should bring all the data and let leaders decide.  
  **Recommendation-first reviews** (Ami Vora): Teams should do the analysis and bring a clear recommendation so leaders can add context and pattern matching.

## Key Metrics & Benchmarks
- **Only 8% of U.S. workers use AI daily** — Gallup poll
- **Zapier sales reps save 10 hours per week on lead research** — Zapier
- **Duolingo went from 100 courses in 12 years to 150 courses in 12 months** — Duolingo
- **Intercom saw about a 20% year-over-year durable improvement in merged pull requests** — Intercom
- **Duolingo gave every employee $300 to try AI tools, courses, and subscriptions** — Duolingo
- **Zapier’s live demos attract over 60 employees every week** — Zapier
- **86% of companies said community is critical to their mission** — 2021 CMX Community Industry Report
- **69% of companies planned to increase community investment** — 2021 CMX Community Industry Report
- **80% of startups were investing in community** — First Round
- **28% of startups said community was their moat** — First Round
- **Duolingo runs 2,600 events every month with a community team of three people** — Duolingo
- **83% of Salesforce customer questions are answered by other customers** — Salesforce
- **CMX Slack has 4,200 members and 14% MAU** — CMX
- **CMX Hub Facebook group has 11,800 members and 18% MAU** — CMX
- **Google has over 1,000 Google Developer Groups worldwide** — Google

## Notable Quotes
- “Growth should be defined as connecting users to the value of the product.” — Albert Cheng
- “Fascinating, you have to tell me more why you think that.” — Ami Vora
- “I hear you; nevertheless, this is the path we’re taking.” — Annie Duke