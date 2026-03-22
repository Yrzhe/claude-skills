# Go-to-Market

## Overview
Go-to-market is the system for turning a product into revenue: choosing who to target, how to reach them, how to position and sell, and how to scale what works. The strongest advice across Lenny's guests is to treat GTM as an experiment-driven operating system, not a one-time launch plan. Good GTM aligns customer needs, channel strengths, sales motion, product experience, and company constraints.

For growth team hiring, onboarding optimization, and channel evaluation frameworks, see `topics/growth.md`. This file focuses on GTM motions, sales strategy, PLG vs SLG, launch, distribution, and B2B/B2C go-to-market decisions.

## Key Frameworks

### Curiosity Loops (Ada Chen Rekhi)
- **When to use**: When you need better input for an important GTM or positioning decision and want contextual advice rather than generic opinions.
- **Steps**:
  1. Form a specific, unbiased question that asks for rationale.
  2. Choose a mix of experts and people who know you well.
  3. Make the ask lightweight and easy to answer quickly.
  4. Collect responses and look for surprises, disagreements, and missing angles.
  5. Thank people and share how their input affected your decision.
- **Example**: Ada emailed 10-11 people with nine possible podcast topics and asked them to pick the top two or three and explain why.

### PLG Funnel vs. SLG Funnel (Hila Qu)
- **When to use**: When deciding how to add a product-led motion to a traditionally sales-led B2B business, or choosing between self-serve and sales-assisted GTM.
- **Steps**:
  1. Map the existing sales-led funnel: visitor to lead to MQL to sales qualification to closed deal.
  2. Map the product-led funnel: visitor to free signup to product usage to activation to self-serve conversion or sales-assisted conversion.
  3. Define where product usage replaces marketing engagement as the key leading indicator.
  4. Create two conversion paths: self-serve checkout for smaller deals and PQL/PQA handoff for higher-value accounts.
- **Example**: At GitLab, users could start free, then teams could trial. Smaller customers self-served; larger accounts were routed to sales based on usage and account fit.

### PLG Readiness Checklist (Hila Qu)
- **When to use**: Before committing to a PLG motion, especially if you are a sales-led company considering adding self-serve.
- **Steps**:
  1. Ensure you have a vehicle: free version, free trial, open-source product, or interactive demo.
  2. Reduce time to value so users can quickly experience meaningful product value.
  3. Build a self-serve checkout flow so users can buy without talking to sales.
  4. Establish a strong data foundation to understand usage behavior and correlate it with conversion and retention.
  5. Simplify pricing so users can understand and purchase without custom quoting.
- **Example**: Hila cited Amplitude's interactive demo as a way to get closer to PLG when full self-serve setup is hard.

### PQL/PQA Motion (Hila Qu)
- **When to use**: When combining PLG with sales to capture larger accounts more effectively.
- **Steps**:
  1. Track product usage signals that indicate strong intent or value realization.
  2. Combine those signals with account-fit criteria such as company size or target industry.
  3. Define product-qualified leads or accounts based on both usage and fit.
  4. Route those accounts to sales or customer success for white-glove outreach.
  5. Use the sales conversation to expand deal size beyond what self-serve alone would capture.
- **Example**: A large company using GitLab heavily during trial could trigger sales outreach, even if the buyer might otherwise have purchased on their own.

### Build in Public + Employee Socials (Elena Verna)
- **When to use**: When you are an early-stage or fast-growing company that can use shipping velocity and transparency to drive awareness, resurrection, and trust as a GTM channel.
- **Steps**:
  1. Ship frequently and visibly.
  2. Have founders and employees post about launches, learnings, and progress.
  3. Tier launches into major moments and smaller ongoing updates.
  4. Use social posting to keep the market aware that the product is evolving.
  5. Let users see that feedback turns into shipped product quickly.
- **Example**: Lovable uses founder-led and employee-led social posting on X and LinkedIn, alongside constant shipping, to maintain market awareness and bring users back.

### Give the Product Away as a Growth Loop (Elena Verna)
- **When to use**: When your product is novel and easier to understand through direct use than through explanation, making freemium distribution a GTM strategy.
- **Steps**:
  1. Remove barriers to first use with freemium access.
  2. Go beyond freemium by giving away credits for events, hackathons, and community-led activation.
  3. Treat usage giveaways as marketing spend, not margin leakage.
  4. Empower users and champions to distribute the product inside their own communities or companies.
  5. Monetize after users experience the product's value and want more usage.
- **Example**: Lovable gives away credits for hackathons and user-led events, tracking LLM costs as marketing costs because they drive adoption and word of mouth.

### Human-in-the-loop Algorithm Design (Adriel Frederick)
- **When to use**: When building pricing, ranking, or ML-driven GTM systems where algorithmic decisions affect go-to-market outcomes.
- **Steps**:
  1. Define the product intent before optimizing.
  2. Decide what humans should control versus what algorithms should control.
  3. Identify judgment calls algorithms cannot reliably infer.
  4. Build interfaces that give humans the right information.
  5. Use algorithms to amplify human intent at scale.
  6. Continuously refine the split between people and machines.
- **Example**: Lyft pricing needed local human input for snowstorms, fuel changes, taxes, and competitive moves.

## Decision Guide
- If you need better input for a major GTM decision, consider **Curiosity Loops** because it surfaces contextual advice and blind spots — per **Ada Chen Rekhi**.
- If you are deciding between PLG and sales-led, use the **PLG Funnel vs. SLG Funnel** comparison because both motions can coexist — per **Hila Qu**.
- If you face pressure to "do PLG" because it is trendy, use the **PLG Readiness Checklist** first because PLG only works when the product has low enough entry friction — per **Hila Qu**.
- If you are combining PLG with enterprise sales, build a **PQL/PQA Motion** because sales should focus on accounts with both intent and revenue potential — per **Hila Qu**.
- If your product is hard to explain, consider **Give the Product Away** because direct use drives conversion and word of mouth — per **Elena Verna**.
- If you are early-stage and need awareness, consider **Build in Public** because shipping velocity and transparency can be a distribution channel — per **Elena Verna**.
- If you are building AI-assisted GTM workflows, use **Human-in-the-loop Design** because autonomy should increase only after trust is earned — per **Adriel Frederick**.
- If a GTM skill like networking or outreach feels uncomfortable, use **Eating Your Vegetables** because repeated exposure distinguishes discomfort from true dislike — per **Ada Chen Rekhi**.
- If growth slows, first revalidate **product-market fit** before chasing channels because market shifts can invalidate prior assumptions — per **Adam Grenier**.

## Expert Consensus
- GTM should be driven by customer value, not vanity metrics.
- Most B2B companies will eventually need both PLG and sales, not one or the other.
- New channels and motions should be tested with discipline and small scope.
- The best GTM strategies align the product experience with the sales motion.
- Data is the foundation of PLG; without it, free access is wasted.

## Points of Debate
- **PLG vs. SLG as primary motion** (Hila Qu, Elena Verna):
  - **PLG-first**: expands reach, lowers CAC, and lets the product sell itself.
  - **SLG-first**: captures larger deals faster and works when the product requires setup or enterprise buy-in.
  - **Emerging consensus**: most B2B companies need both, but the starting point depends on product complexity and deal size.
- **Use AI autonomously vs. keep humans in control** (Aishwarya Naresh Reganti + Kiriti Badam):
  - **More autonomy**: can scale faster.
  - **Human-in-the-loop**: safer and more reliable until the system proves itself.
- **Pursue hot new channels vs. stay focused on core channels** (Adam Grenier):
  - **Pursue new channels**: can create advantage if the channel and company are a strong fit.
  - **Stay focused**: safer when core channels are not yet working or the new channel is unstable.
- **Free product as GTM vs. free product as cost center** (Elena Verna):
  - **Cost center view**: giving away product is margin leakage.
  - **GTM view**: usage giveaways are marketing spend that drive adoption and word of mouth.

## Key Metrics & Benchmarks
- **GitLab**: PLG funnel with free personal accounts feeding team trials, self-serve checkout for SMB, and sales-assisted conversion for enterprise.
- **Amplitude**: interactive demo as a PLG entry point when full self-serve setup is hard.
- **Lovable**: tracks LLM credit giveaways as marketing costs, not product costs.
- **Lenny's Newsletter**: reached **1 million subscribers**, with Substack recommendations contributing roughly **500,000** of that growth.

## Notable Quotes
- "Advice should be treated as input, not instructions." — **Ada Chen Rekhi**
- "PLG I always say is actually fundamentally DLG, data led growth." — **Hila Qu**
- "The only way to create a word of mouth loop is just to blow their socks off." — **Elena Verna**