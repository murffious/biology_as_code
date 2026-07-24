# Meals — do not duplicate here

**Single source of truth (SSOT)** for full meal fixtures:

```text
src/biology_as_code/data/fixtures/meals/
```

Those JSON files ship with `pip install biology-as-code`.

## How to use

```python
from biology_as_code.data.fixtures import list_meal_ids, load_meal, meal_to_food_payload_dict
from biology_as_code import simulate_meal, FoodPayload

meal_id = list_meal_ids()[0]
meal = load_meal(meal_id)
fields = meal_to_food_payload_dict(meal)
payload = FoodPayload(
    name=fields["name"],
    macros_g=fields["macros_g"],
    fiber_g=fields["fiber_g"],
    quality_score=fields["quality_score"],
)
r = simulate_meal(payload=payload)
print(r.absorbed_macros_g)
```

Or from a checkout:

```bash
ls src/biology_as_code/data/fixtures/meals/
```

## Related (different set)

| Path | What |
|------|------|
| `examples/foods/` | Small **teaching food packets** (spinach + oil, lentils + tea, …) — claim/gate demos, not full meal plans |
| `src/.../fixtures/meals/` | Full **meal** fixtures for dig (macros, ingredients, nutrition) |
| `examples/claims/` | Claim audit fixtures |

No product meal score / `kibo_score` in public meal fixtures.
