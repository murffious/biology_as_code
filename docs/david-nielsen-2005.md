# David & Nielsen 2005 — source map, not a second engine

Working note from a photographed copy of:

David, H. & Nielsen, J. (2005). Modelling of fungal metabolism.
In Vaidyanathan, S., Harrigan, G.G. & Goodacre, R. (eds.),
*Metabolome Analyses: Strategies for Systems Biology*, ch. 12, pp. 195–214.
Springer, Boston, MA. [doi:10.1007/0-387-25240-1_12](https://doi.org/10.1007/0-387-25240-1_12)

Companion to [gem-primer.md](gem-primer.md). Same altitude: genome-scale
reconstruction and flux balance. Not a FoodPacket walk.

## What the chapter is doing

It treats a GEM as an iterative loop (their Figure 1, p. 197):

- *in vivo* real network ↔ reconstructed network (*in silico*)
- reconstructed network → simulated behaviour
- simulated behaviour ↔ measured behaviour
- data integration in the middle

That loop is constraint-based modeling: build *S*, add bounds, choose an
objective (often maximal growth), let FBA fill fluxes, then go back to the
bench. Covert et al. (2001) and the later *S. cerevisiae* reconstruction
(Förster / Nielsen, 2003) sit on the same line.

The paragraph under Table 2 is the sentence that matches this package:
sequence homology is not function. The same annotated EC on two genomes does
not license the same physiological flux. Presence of a reaction is a separate
seat from how much carbon moves.

## Table 2 — printed URLs vs 2026

| Printed name | Printed URL | 2026 |
|---|---|---|
| EcoCyc | http://ecocyc.org | Live. *E. coli* K-12 literature GEM. EcoCyc.org; still versioned (29.x). Free. |
| MetaCyc | http://metacyc.org | Live. Experimentally curated multi-organism pathways inside BioCyc. |
| MPW | ergo.integratedgenomics.com/MPW | Public tool gone (Integrated Genomics / ERGO era). |
| KEGG | genome.ad.jp/kegg | Live as kegg.jp. Reference maps, different curation model than EcoCyc. |
| WIT | wit.mcs.anl.gov | Service gone; lineage continues in SEED / ModelSEED. |
| Biology WorkBench | workbench.sdsc.edu | SDSC service gone. |
| EMP | empproject.com | Historical enzyme/pathway archive; not a reconstruction engine. |

Use EcoCyc / MetaCyc / KEGG as **citation targets** for pathway identity on LAW
cards. Do not vendor them. Do not treat a KEGG map id as a measured meal flux.

## What this package does not take from the chapter

- An FBA solver or a second `simulate_meal` that emits flux mmol.
- COBRApy in the kernel (GPL-2.0 vs Apache-2.0; already listed adjacent in
  [related-projects.md](related-projects.md)).
- A CI gate that fails a PR when a GEM growth rate is off 5%.
- Filling OPEN amounts from an objective function.

A GEM answers which fluxes are *feasible* under an assumed objective. This
package names digestion and teaching paths and leaves magnitudes empty unless a
seat is declared. Complementary, not substitutable.
