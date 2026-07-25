# Claim schema — the CanonicalClaim standard

The shape every wild claim normalizes to. The claims agent emits it; the CC0 shapes
in [`schemas/aca.ttl`](https://github.com/murffious/biology_as_code/blob/main/schemas/aca.ttl)
and [`schemas/claim-shape.ttl`](https://github.com/murffious/biology_as_code/blob/main/schemas/claim-shape.ttl)
validate it.

```text
CanonicalClaim {
  claim_id                          // stable hash(subject, predicate, outcome) — dedupe key
  source { platform, url, author, posted_at, reach, raw_text }
  subject {                         // normalized to the food graph
    surface: "spirulina"
    canonical: "Spirulina (Arthrospira platensis)"
    ontology_id: "FDC:… · NCBI:1156"
    form: null                      // whole food? extract? — usually unstated
  }
  intervention { dose, frequency, duration, specified: bool }   // false ⇒ red flag
  atomic_claims: [{
    predicate           // chelates | removes | crosses | is-only | prevents …
    outcome { surface, canonical, ontology_id }
    site                // brain | organs | gut | bloodstream
    assertion_strength  // hedged | strong | absolute | superlative
    claim_type          // causal | mechanistic | superlative | safety
    grade               // from the evidence proof graph
    evidence_basis      // one line: what actually supports/refutes
    graph_ref           // → the proof tree
  }]
  red_flags: [...]
  scoped_restatement    // the honest version the coach speaks
  net_grade
  status                // auto-published | needs-review
}
```

> **Design law: compose, don't invent.** Every slot normalizes to an ontology the
> field already trusts. We author exactly one thing — a small assessment vocabulary
> for our verdicts — and keep it orthogonal (OBO discipline: never duplicate a term
> that exists elsewhere). This is what makes the schema interoperable by construction
> and therefore adoptable.
>
> **On identifiers below:** prefixes are real and verified; the exact numeric
> accessions are *illustrative* — resolve each against the OLS (Ontology Lookup
> Service) or BioPortal before use. Never ship a guessed accession.

## 1. Standards this schema stands on

| Layer | Standard | Role |
|---|---|---|
| Core statement | **Biolink Model** | subject–predicate–object "core triple" |
| Food / product | **FoodOn** (+ USDA FDC, LanguaL, NCBITaxon for organism) | food entity normalization |
| Compound / nutrient | **ChEBI** (+ PubChem CID), **CDNO** | chemical + dietary-component normalization |
| Disease / condition | **MONDO** (+ DOID, MeSH, ICD-11, SNOMED CT) | outcome normalization + literature linkage |
| Phenotype / trait / biomarker | **HPO**, **EFO**, **FOBI** | measurable-outcome normalization |
| Anatomy / site | **UBERON** | e.g. brain, blood–brain barrier |
| Units | **UO** (+ UCUM) | dose and effect units |
| Relation semantics | **RO** | predicate grounding under Biolink |
| Evidence type | **ECO** | type of each evidence line |
| Study design | **OBI** | RCT, cohort, in-vitro, etc. |
| Evidence organization + confidence | **SEPIO** pattern | evidence lines supporting a claim |
| Certainty | **GRADE** (coded) | High / Moderate / Low / Very-low |
| Claim envelope | **Nanopublication** (assertion / provenance / publication-info) | citable, immutable, versioned, FAIR |
| Provenance / versioning | **PROV-O** + **PAV** + Dublin Core | who / when / how / version |
| Web-discoverable verdict | **schema.org ClaimReview** | fact-check markup |
| Our one extension | **ACA** (Assay Claim Assessment) | attack types + verdict scale, plugs into ECO/SEPIO |

## 2. The one thing we author — ACA

A tiny, orthogonal vocabulary (~20 terms). It exists only because no standard names
"stress-test attack" or "Busted". Everything else is imported.

```text
ACA:Verdict            ⊑ (annotation on a Claim)
  ACA:Busted  ACA:Plausible  ACA:Confirmed
ACA:Attack             ⊑ (an assessment step; each references an ECO evidence type it interrogates)
  ACA:AtomizationAttack  ACA:HumanEvidenceAttack  ACA:DoseFormAttack
  ACA:MechanismVsOutcomeAttack  ACA:EffectSizeAttack  ACA:ConfoundingAttack
  ACA:SuperlativeAttack  ACA:ReplicationAttack
ACA:survivedAttack / ACA:failedAttack   (Claim → ACA:Attack)
ACA:rubricVersion (string)              (verdict → semver)
```

Released under CC0 as [`schemas/aca.ttl`](https://github.com/murffious/biology_as_code/blob/main/schemas/aca.ttl).

## 3. Master schema — the spirulina claim, normalized end-to-end

JSON-LD. The `@context` binds prefixes; the body is one nanopublication with three
named graphs.

```jsonc
{
  "@context": {
    "biolink": "https://w3id.org/biolink/vocab/",
    "FOODON": "http://purl.obolibrary.org/obo/FOODON_",
    "CHEBI":  "http://purl.obolibrary.org/obo/CHEBI_",
    "MONDO":  "http://purl.obolibrary.org/obo/MONDO_",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "ECO":    "http://purl.obolibrary.org/obo/ECO_",
    "OBI":    "http://purl.obolibrary.org/obo/OBI_",
    "UO":     "http://purl.obolibrary.org/obo/UO_",
    "RO":     "http://purl.obolibrary.org/obo/RO_",
    "sepio":  "http://purl.obolibrary.org/obo/SEPIO_",
    "ACA":    "https://w3id.org/assay/aca/",
    "prov":   "http://www.w3.org/ns/prov#",
    "pav":    "http://purl.org/pav/",
    "np":     "http://www.nanopub.org/nschema#",
    "schema": "https://schema.org/"
  },

  "claim_id": "assay:claim/6f1a…c9",           // content hash(subject|predicate|object_norm)
  "np:hasAssertion": {
    "subject": {
      "label": "spirulina",
      "food": "FOODON:03411347",                // illustrative — resolve via OLS
      "organism": "NCBITaxon:1126",             // Arthrospira platensis
      "xref": ["USDA_FDC:170495"],
      "form": null, "intervention": { "dose": null, "unit": "UO:…", "specified": false }
    },
    "atomic_claims": [
      {
        "atom_id": "…#a1",
        "predicate": "biolink:affects",         // "chelates/removes" ⇒ decreases-abundance-of
        "predicate_detail": "RO:0002212",       // negatively regulates (illustrative)
        "object": { "label": "heavy metals", "chemical": "CHEBI:5631",
                    "site": "UBERON:0000955" }, // brain
        "assertion_strength": "absolute",
        "aca:verdict": "ACA:Busted"
      }
    ],
    "aca:verdict": {
      "label": "ACA:Busted", "grade": "GRADE:VeryLow",
      "aca:rubricVersion": "1.0.0",
      "aca:survivedAttack": ["ACA:ConfoundingAttack"],
      "aca:failedAttack": ["ACA:HumanEvidenceAttack","ACA:MechanismVsOutcomeAttack",
                           "ACA:SuperlativeAttack","ACA:ReplicationAttack"],
      "scoped_restatement": "Antioxidant-rich; protects organs from metal damage in animals; one arsenic+zinc extract trial in humans. No evidence it clears metals from a healthy brain."
    },
    "sepio:hasEvidenceLine": [
      { "eco:evidenceType": "ECO:0000180",       // in-vitro / animal model evidence (illustrative)
        "obi:studyDesign": "OBI:0000471", "direction": "weak-support" }
    ]
  },

  "np:hasProvenance": {
    "prov:wasDerivedFrom": { "schema:url": "https://x.com/…", "reach": 921000 },
    "prov:wasGeneratedBy": { "pipeline": "assay", "pav:version": "1.0.0" }
  },

  "schema:ClaimReview": {                                 // emitted for web discovery
    "@type": "ClaimReview",
    "claimReviewed": "Spirulina removes heavy metals from your brain; only food to cross the BBB.",
    "reviewRating": { "@type": "Rating", "ratingValue": 1, "bestRating": 5, "alternateName": "Busted" },
    "author": { "@type": "Organization", "name": "Assay" }
  }
}
```

## 4. Why this composition wins adoption

- **Interoperable by construction** — a Translator / Monarch / Neo4j user ingests it
  with no mapping; every node already resolves to a shared IRI.
- **Citable at claim granularity** — the nanopublication envelope gives each claim a
  stable, versioned, FAIR identity.
- **Discoverable** — the ClaimReview block surfaces verdicts in search, tying into the
  global fact-check graph.
- **Credible** — you inherit the review discipline of OBO Foundry rather than asking
  anyone to trust a bespoke vocabulary.
- **Minimal surface you own** — ACA is ~20 terms. Small enough to maintain, orthogonal
  enough to be accepted.

## 5. Adoption checklist

- [ ] Publish ACA OWL (CC0); request OBO Foundry review.
- [ ] Register schema + corpus on **BioPortal** and **FAIRsharing**.
- [ ] Validate claim objects against the SHACL/ShEx shape (`schemas/claim-shape.ttl`).
- [ ] Mint nanopublications to the nanopub network; expose a ClaimReview feed.
- [ ] Add a resolver: `claim_id` → JSON-LD + human page.
