# FDA ingredients ↔ nutrient nodes overlap

Strict whole-phrase / synonym matching (score ≥ 80). Not legal advice.

## Match summary

- Matches: **1,609**
- Unique nutrient_ids: **88** (Tier A **56**, Tier B **32**)
- By inventory: `{'food_substances': 438, 'gras_notices': 216, 'fcn': 291, 'indirect_additives': 664}`
- By pack: `{'A': 1455, 'B': 154}`

## Synonym-level examples (score 100)

| Inventory | Substance | → nutrient_id | Pack |
|-----------|-----------|---------------|------|
| food_substances | 9,12-OCTADECADIENOIC ACID (48%) AND 9,12,15-OCTADECATRI | `linoleic_acid` | A |
| fcn | A mixture of the lithium salts of stearic acid (69.5 we | `arachidonic_acid` | A |
| fcn | A silver-zinc-sodium aluminosilicate zeolite containing | `zinc` | A |
| food_substances | ALPHA-TOCOPHEROL ACETATE | `vitamin_e` | A |
| food_substances | ALPHA-TOCOPHEROL ACID SUCCINATE | `vitamin_e` | A |
| food_substances | ALUMINUM NICOTINATE | `vitamin_b3` | A |
| food_substances | AMMONIUM PECTINATE | `pectin` | B |
| gras_notices | ARASCO (arachidonic acid-rich single-cell oil) | `arachidonic_acid` | A |
| gras_notices | ARASCO (arachidonic acid-rich single-cell oil) and DHAS | `dha` | A |
| food_substances | ASCORBIC ACID | `vitamin_c` | A |
| food_substances | ASCORBYL PALMITATE | `vitamin_c` | A |
| food_substances | ASCORBYL STEARATE | `vitamin_c` | A |
| food_substances | ASTAXANTHIN | `vitamin_a` | A |
| gras_notices | Algal oil (&ge;35% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;35% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;35% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;35% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;35% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;36% docosahexaenoic acid) from Schizochy | `dha` | A |
| gras_notices | Algal oil (&ge;40% docosahexaenoic acid) from Aurantioc | `dha` | A |
| gras_notices | Algal oil (&ge;40% docosahexaenoic acid) from Aurantioc | `dha` | A |
| gras_notices | Algal oil (&ge;45% docosahexaenoic acid from Schizochyt | `dha` | A |
| gras_notices | Algal oil (&ge;45% docosahexaenoic acid) from Aurantioc | `dha` | A |
| gras_notices | Algal oil (35% docosahexaenoic acid) from Schizochytriu | `dha` | A |
| gras_notices | Algal oil (36% docosahexaenoic acid) from Schizochytriu | `dha` | A |
| gras_notices | Algal oil (40% docosahexaenoic acid) derived from Schiz | `dha` | A |
| gras_notices | Algal oil (40% docosahexaenoic acid) from Schizochytriu | `dha` | A |
| gras_notices | Algal oil (50-60% docosahexaenoic acid) from Schizochyt | `dha` | A |
| gras_notices | Algal oil (55% docosahexaenoic acid) from Schizochytriu | `dha` | A |
| gras_notices | Alpha-linolenic acid diacylglycerol | `ala` | A |
| gras_notices | Alpha-tocopherol (fruit and vegetable derived) | `vitamin_e` | A |
| fcn | An aqueous solution of peroxyacetic acid (PAA) (CAS Reg | `oxalate` | B |
| gras_notices | Arachidonic acid rich oil from M. alpina strain I49-N18 | `arachidonic_acid` | A |
| food_substances | BETA-CAROTENE | `vitamin_a` | A |
| food_substances | BETAINE | `betaine` | A |

## Tier A ids hit

`ala`, `alanine`, `arachidonic_acid`, `arginine`, `aspartic_acid`, `betaine`, `caffeine`, `calcium`, `chloride`, `cholesterol`, `choline`, `chromium`, `copper`, `cystine`, `dha`, `energy`, `epa`, `fluoride`, `folate`, `glutamic_acid`, `glycine`, `iodine`, `isoleucine`, `leucine`, `linoleic_acid`, `lutein_zeaxanthin`, `lycopene`, `lysine`, `magnesium`, `manganese`, `methionine`, `molybdenum`, `phenylalanine`, `phosphorus`, `potassium`, `proline`, `selenium`, `serine`, `sodium`, `threonine`, `tryptophan`, `tyrosine`, `valine`, `vitamin_a`, `vitamin_b1`, `vitamin_b12`, `vitamin_b2`, `vitamin_b3`, `vitamin_b5`, `vitamin_b6`, `vitamin_b7`, `vitamin_c`, `vitamin_d`, `vitamin_e`, `vitamin_k`, `zinc`

## Tier B ids hit

`alginate`, `anthocyanins`, `astaxanthin`, `beta_glucan`, `capsaicinoids`, `carnitine`, `chlorophyll`, `cla`, `creatine`, `curcumin`, `ethanol`, `fucoidan`, `gos`, `hesperidin`, `hydroxytyrosol`, `inulin_fos`, `isoflavones`, `lactoferrin`, `myricetin`, `oxalate`, `pectin`, `phytate`, `phytosterols_total`, `piperine`, `psyllium_mucilage`, `quercetin`, `resveratrol`, `spermidine`, `tannins`, `taurine`, `total_polyphenols`, `tyramine`

Full list: `overlap_matches.csv`
