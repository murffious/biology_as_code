# Meal fixtures — data attribution

These fixtures embed nutrient values from two external sources. Each fixture's own
`nutrition_provenance` block already names them; this file is the repository-level
attribution that ODbL requires.

## Open Food Facts — ODbL 1.0, attribution required

> Open Food Facts contributors — <https://world.openfoodfacts.org>
> Licensed under the **Open Database License (ODbL) v1.0**.

67 fixtures declare `OpenFoodFacts (fallback macros)`: OFF supplied macro values
where USDA FoodData Central had none.

**ODbL is share-alike.** Publicly using a *derived database* obliges you to offer
that derived database under ODbL. Attribution is required in every case. Whether
this fixture set is a derived database under ODbL, or a produced work using
insubstantial extracts, is **unresolved** — recorded as such rather than assumed
either way. The attribution above is required regardless.

Apache-2.0 governs the code in this repository. It does not reach these values.

## USDA FoodData Central — US public domain

> US Department of Agriculture, Agricultural Research Service.
> FoodData Central (Branded, SR Legacy, Foundation) — <https://fdc.nal.usda.gov>

Work of the US federal government (17 U.S.C. 105). Attribution is courtesy, not
obligation. Not to be used to imply USDA endorsement.

---

*Found by `check_third_party.py` on its first run, 2026-08-29. The fixtures had
recorded their own sources since July; nothing had ever read them. That is the
project's own thesis landing on the project: provenance that is written down but
never propagated is provenance nobody can act on.*

See `../../../../THIRD-PARTY-DATA.json` and `../../../../NOTICE`.
