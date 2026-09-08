# Non-laws: statements that look like laws and are not

A tier-3 number is refused because nobody measured it on this packet. The three
statements here fail earlier and differently. Each is a **claim about structure**
that sounds like settled biochemistry, is repeated in textbooks and review
articles, and is either false or narrower than its phrasing.

They are recorded because the failure mode is invisible to every gate in the
tree. `check_constants.py` catches a number with no source. `check_pmids.py`
catches a source that names the wrong paper. Neither catches a correctly cited,
correctly typed sentence that is simply not true.

---

## 1. "PFK is the rate-limiting step of glycolysis"

**Status: not a law. Control is shared, and the summation theorem says so.**

Metabolic control analysis, built independently by Kacser & Burns and by Heinrich
& Rapoport in the early 1970s, defines the flux control coefficient of step *i*
as the fractional change in steady-state pathway flux *J* per fractional change
in that step's activity. The **summation theorem** is that these sum to one
across the system:

$$\sum_i C^{J}_{v_i} = 1 \qquad \sum_i C^{s}_{v_i} = 0$$

A genuine rate-limiting step would be a coefficient of one with every other step
at zero. That is a permitted special case, not the typical one. The whole point
of the framework was to retire the textbook single-bottleneck picture.

Two consequences the phrasing hides:

- A control coefficient is **not a property of the enzyme**. It is a property of
  the enzyme *in that network at that state*. Change a different enzyme, or the
  substrate supply, and the same step's coefficient moves.
- Control coefficients are only defined **at a stable steady state**. Off one,
  they are not merely unmeasured, they have no referent. See non-law 2.

**What may be said:** the pathway has a step whose elasticity to a named effector
is high at a stated operating point. **What may not:** a number like
$C^{J}_{\text{PFK}} = 0.7$ attached to a gram of anything. That coefficient is
state-specific and was not measured on the packet.

Kacser H, Burns JA. The control of flux. Symp Soc Exp Biol. 1973;27:65-104.
[PMID 4148886](https://pubmed.ncbi.nlm.nih.gov/4148886/) ·
Heinrich R, Rapoport TA. A linear steady-state treatment of enzymatic chains.
Eur J Biochem. 1974;42(1):89-95.
[PMID 4830198](https://pubmed.ncbi.nlm.nih.gov/4830198/) ·
Reder C. Metabolic control theory: a structural approach. J Theor Biol.
1988;135(2):175-201. [PMID 3267767](https://pubmed.ncbi.nlm.nih.gov/3267767/)

---

## 2. "If $G-H$ is Hurwitz the steady state is stable"

**Status: sufficient, not necessary. Treating it as the whole test is wrong.**

In biochemical systems theory a pathway is written as an S-system, one power law
for all production of a pool and one for all consumption. Taking logs makes the
steady state a linear problem, and the Jacobian near it carries the structure

$$A_{ij} = \bar F_i\,(g_{ij}-h_{ij})$$

where $g,h$ are kinetic orders and $\bar F_i$ is the turnover flux through pool
*i*. The tempting shortcut is to read stability straight off the sign pattern of
$G-H$ and ignore the fluxes.

It does not hold in that direction. **The flux weights $\bar F_i$ rescale the
rows**, so $G-H$ being Hurwitz does not make $A(\bar X)$ Hurwitz. Sign-semistability
of $G-H$ *is* enough to give stability for all positive rate constants, which is
what makes the shortcut attractive and why it keeps being restated as though it
were the criterion.

There is an ordering here worth keeping, because it maps onto states this engine
already has. Existence comes before stability: the steady state solves
$(G-H)y = \ln(\beta/\alpha)$, so if $G-H$ is not invertible there is no isolated
interior steady state at all. A malformed question is not an unmeasured one.

| Situation | Engine state |
|---|---|
| No isolated interior steady state | `REFUSE` — category error, not a missing number |
| Seats undeclared, Jacobian not instantiated | `UNEVALUABLE` — never "stable by default" |
| Path absent by declaration | `REFUTED` |

**What may be said:** stability is a property of $(G-H, \bar F)$ **at a stated
state**. **What may not:** that a meal moves a kinetic order across a Hopf
bifurcation. That would mean inventing $\alpha, \beta, G, H$ from a barcode.

Savageau MA. Biochemical systems analysis. II. J Theor Biol. 1969;25(3):370-9.
[PMID 5387047](https://pubmed.ncbi.nlm.nih.gov/5387047/)

> **Open gap, deliberately not closed.** Savageau's *explicit local stability
> conditions* — Routh-Hurwitz applied to the log-space Jacobian — are usually
> credited to his 1976 book. The indexed candidate is *Biochemical systems
> analysis. 3. Dynamic solutions using a power-law approximation*, J Theor Biol
> 1970;26(2):215-26, [PMID 5434343](https://pubmed.ncbi.nlm.nih.gov/5434343/).
> PubMed carries no abstract for it and there is no open copy, so **this citation
> is candidate, not verified**. Settling it needs the full text. It is recorded
> as a gap rather than attached to a nearby paper that would look like a source
> and not be one.

---

## 3. "Metabolic control analysis and biochemical systems theory are equivalent"

**Status: containment, not equivalence — and the claim comes from one side.**

The two formalisms rest on the same power-law approximation, and their local
objects correspond: a kinetic order in biochemical systems theory *is* an
elasticity in control analysis,
$g_{ij} = \partial\ln v_i/\partial\ln X_j = \varepsilon^{v_i}_{X_j}$. That much is
solid, and it is why the two literatures describe the same biology.

"Equivalent" is stronger than the source supports. Sorribas and Savageau compared
the variants directly and concluded that metabolic control theory is a **special
case** of the implicit generalized-mass-action variant within biochemical systems
theory, that the explicit variants characterise a reference system more
completely than the implicit ones, and that the S-system representation is more
tractable and accurate than generalized mass action.

That is a claim of containment plus an advantage, not symmetry. It is also
**Savageau's own comparison**, and he was a party to the dispute about which
formalism subsumes which. Cite it as his analysis. The historical argument was
about aggregation and rhetoric rather than about two different chemistries.

**A specific thing not to do:** paste a flux-balance solution into a control
coefficient. A flux balance optimum is typically maximising *yield* under a hard
uptake bound, and yield control sums to zero while enzyme control on flux sums to
one. Different coefficient, different theorem.

Sorribas A, Savageau MA. A comparison of variant theories of intact biochemical
systems. I. Math Biosci. 1989;94(2):161-93.
[PMID 2520168](https://pubmed.ncbi.nlm.nih.gov/2520168/) ·
II. Flux-oriented and metabolic control theories. Math Biosci. 1989;94(2):195-238.
[PMID 2520169](https://pubmed.ncbi.nlm.nih.gov/2520169/) ·
Ingalls BP. Sensitivity analysis of stoichiometric networks. J Theor Biol.
2003;222(1):23-36. [PMID 12699732](https://pubmed.ncbi.nlm.nih.gov/12699732/)

---

## Why this page exists at all

Every identifier above resolved against PubMed on 2026-09-08, because the
alternative has a track record here: a resolve-and-diff pass on 2026-09-07 found
twelve of seventeen shipped identifiers naming a different paper, four of them
"corrections" that replaced one wrong id with another.

`tools/check_pmids.py` now prevents that specific failure. It cannot prevent
this one. A sentence can carry a perfectly resolved citation and still overstate
what the paper says, which is what happened in non-law 3 before it was checked.
The gap between "cited" and "true" is not automatable, so it is written down.

## See also

- [Metabolic constants](metabolic-constants.md) — the three tiers, and what may be encoded
- [Constitution](constitution.md) — `gate ≠ bound`, the four seats
