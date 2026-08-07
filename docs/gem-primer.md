# Primer: genome-scale metabolic models (GEMs)

Background reading for anyone coming to this project from nutrition rather than
systems biology. `biology-as-code` is **not** a GEM and does not run flux balance
analysis — but GEMs are the established modelling tradition this work sits next
to, and the vocabulary shows up constantly in the surrounding literature.

## What a GEM is

A **GEM** (genome-scale metabolic model, also called a genome-scale metabolic
reconstruction or network) is a mathematical model of an organism's entire known
metabolism, built from its genome.

It contains:

- All (or nearly all) known metabolic reactions the organism can perform
- The genes and proteins encoding the enzymes for those reactions, via **GPR**
  rules (gene–protein–reaction associations)
- Metabolites and their stoichiometry
- Compartments (cytosol, mitochondria, extracellular space, and so on)

The model is represented as a stoichiometric matrix — the **S-matrix** — and
analysed with constraint-based methods, most commonly **flux balance analysis
(FBA)**.

When people say "run a GEM" or "constrain the GEM with a diet," they mean: take
this genome-scale network of reactions, set bounds on the exchange reactions
based on the food a person ate plus any other physiological constraints, then
compute which fluxes through the network are possible.

## The main models you'll see referenced

| Model | What it is | Reference |
|-------|-----------|-----------|
| **Recon3D** | The main human GEM | Brunk et al., *Nat Biotechnol* 2018 — [PMID 29457794](https://pubmed.ncbi.nlm.nih.gov/29457794/) |
| **AGORA** | GEMs for 773 gut bacteria | Magnúsdóttir et al., *Nat Biotechnol* 2017 — [PMID 27893703](https://pubmed.ncbi.nlm.nih.gov/27893703/) |
| **AGORA2** | Expanded to 7,302 microorganisms | Heinken et al., *Nat Biotechnol* 2023 — [PMID 36658342](https://pubmed.ncbi.nlm.nih.gov/36658342/) |
| **Harvey / Harvetta** | Whole-body models (WBM) joining organ-level human GEMs via blood compartments, male and female | Thiele et al., *Mol Syst Biol* 2020 — [PMID 32463598](https://pubmed.ncbi.nlm.nih.gov/32463598/) |
| **VMH** | The Virtual Metabolic Human database hosting these GEMs plus metabolite, reaction, gene, and food data | Noronha et al., *Nucleic Acids Res* 2019 — [PMID 30371894](https://pubmed.ncbi.nlm.nih.gov/30371894/) |

Whole-body models are the reason this vocabulary matters to nutrition: they
integrate metabolism, physiology, and the gut microbiome into a single
personalisable object, which is the closest existing analogue to what a
mechanistic "what did this meal do" model needs.

## How this project relates

`biology-as-code` works at a different altitude. A GEM answers *which fluxes are
feasible across the whole network*; this package models *what happens to a meal*
through named, inspectable stages — digestion machines, gates and bounds, and
teaching pathway graphs — with provenance attached to every value.

The two are complementary rather than competing. The GEM tradition supplies the
mechanistic ceiling; the contribution here is the provenance discipline described
in [FDP-1](https://github.com/murffious/fdp-1) and the
[constitution](constitution.md), so that a number's origin and evidence grade
travel with it instead of being lost on the way into a model.
