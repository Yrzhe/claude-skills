# Cross-Disciplinary Analogy Templates

A library of 30+ structural templates from outside business that frequently apply to product / growth / behavioral data. Use this as a *starting point* for the analogy track. Do not pick a template just because it's listed — it must pass the 4 acceptance tests in `interpret-analogy-track.md`.

Organized by abstract structure. When the analyst names the structure of a finding (Step 1 of the analogy loop), find candidate templates here.

---

## Power laws / cumulative advantage

| Template | Source field | Structural signature |
|---|---|---|
| **Preferential attachment** (Barabási-Albert) | network science | nodes with degree k attract new edges with probability ∝ k → power-law degree distribution |
| **Matthew effect** (Merton) | sociology of science | citations beget citations; reputation compounds |
| **Pareto distribution** | economics | top X% holds Y% of total; X<<Y (e.g., 20/80) |
| **Yule process** | macroevolution | diversification proportional to current diversity |
| **Polya urn** | probability | success probability rises with prior successes; path-dependent |

---

## Decay / saturation / diminishing returns

| Template | Source field | Structural signature |
|---|---|---|
| **Niche saturation** | ecology | new entrants diminish per-capita resources; carrying capacity K |
| **Logistic / sigmoid curve** | population biology / chemistry | early exponential → mid linear → late saturation |
| **Information-theoretic novelty decay** | info theory | repeated signal carries diminishing bits; surprise → 0 |
| **Habituation** | neuroscience / behavior | response amplitude decreases with stimulus repetition |
| **Diminishing marginal utility** | economics | each additional unit of X delivers less value |
| **Negative feedback loop** | control theory | system output suppresses further output |

---

## Critical periods / lock-in / path dependence

| Template | Source field | Structural signature |
|---|---|---|
| **Critical period** (Lorenz, Hubel-Wiesel) | developmental biology | window in which input shapes long-term structure; window closes |
| **Imprinting** | ethology | early stimulus permanently fixes a preference |
| **Hysteresis** | physics / materials | system state depends on history, not just current input |
| **QWERTY-style lock-in** | path dependence econ | early arbitrary choice persists due to switching cost |
| **Hopfield basin of attraction** | dynamical systems | state converges to nearest attractor; basin shape matters |

---

## Phase transitions / threshold effects

| Template | Source field | Structural signature |
|---|---|---|
| **Percolation threshold** | statistical physics | abrupt connectivity transition at critical density |
| **Boiling-point analogy** | thermodynamics | continuous input → discontinuous state change at T_c |
| **Tipping point** (Granovetter) | sociology | individual thresholds aggregate into collective shifts |
| **Synchronization** (Kuramoto) | nonlinear dynamics | coupled oscillators lock above coupling threshold |
| **Self-organized criticality** (Bak) | complexity | system tunes itself to critical point; power-law avalanches |

---

## Selection / evolution

| Template | Source field | Structural signature |
|---|---|---|
| **R/K selection** | evolutionary ecology | many-cheap (r) vs few-expensive (K) reproductive strategies |
| **Replicator dynamics** | evolutionary game theory | strategy frequency changes proportional to relative fitness |
| **Red Queen** (Van Valen) | coevolution | must keep adapting just to stay in place |
| **Punctuated equilibrium** (Eldredge-Gould) | paleontology | long stasis interrupted by rapid change bursts |
| **Convergent evolution** | biology | independent lineages arrive at similar solutions to similar pressures |

---

## Search / exploration / optimization

| Template | Source field | Structural signature |
|---|---|---|
| **Explore-exploit tradeoff** | reinforcement learning / foraging | tension between gathering info and using known-good options |
| **Multi-armed bandit** | sequential decision | regret minimization across uncertain options |
| **Simulated annealing** | optimization | high-randomness early; cool to convergence |
| **Hill-climbing trap** | optimization | local optimum prevents global discovery without restart |
| **Optimal foraging** (MacArthur-Pianka) | ecology | leave a patch when marginal value drops to environment average (Charnov's marginal value theorem) |

---

## Coordination / collective behavior

| Template | Source field | Structural signature |
|---|---|---|
| **Tragedy of the commons** | resource economics | individually rational use depletes shared resource |
| **Schelling segregation** | sociology | local mild preferences → global stark sorting |
| **Information cascades** | social epistemics | individuals follow predecessors' choices, ignoring private info |
| **Stigmergy** | collective biology (ant trails) | individual behavior modifies environment, which guides others |
| **Coordination game equilibria** | game theory | multiple stable equilibria; one is socially better |

---

## Information / signal

| Template | Source field | Structural signature |
|---|---|---|
| **Costly signaling** (Spence) | economics | only honest signals are expensive enough to deter fakers |
| **Lemons problem** | info economics | asymmetric info collapses market quality |
| **Bayesian belief updating** | probability | prior + likelihood → posterior; weight is precision-of-evidence |
| **Free energy / surprise minimization** (Friston) | neuroscience | systems minimize prediction error |
| **Stochastic resonance** | nonlinear physics | adding noise can improve signal detection in threshold systems |

---

## Spatial / geographic

| Template | Source field | Structural signature |
|---|---|---|
| **Gravity model** | geography / trade | interaction ∝ size_A × size_B / distance² |
| **Central place theory** | urban econ | hierarchical service-provision spacing |
| **Diffusion of innovations** (Rogers) | sociology | adopters spread spatially via social contact |

---

## How to use this list

1. **Don't browse the whole list** — first name the abstract structure of your finding, then look only in that section
2. **One good analogy beats three weak ones** — present one, defended
3. **Check the 4 acceptance tests in `interpret-analogy-track.md`** before shipping
4. **Most of these templates have famous primary sources** — name them when you cite ("preferential attachment, Barabási-Albert 1999"); a senior analyst is literate, not improvising

---

## Adding to this library

If a real analysis surfaces a structural pattern not covered here, add it. Format: name | source field | structural signature in one line. Keep this file < 200 lines so it stays scannable.
