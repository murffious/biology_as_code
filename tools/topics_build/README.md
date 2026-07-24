# Topics ontology build (dev only)

These scripts are **not** shipped in the `biology-as-code` wheel.

```bash
# from repo root
python tools/topics_build/build_from_list.py
```

Requires the frozen topic list input expected by `_classify_topics_impl.py`.
Writes `src/biology_as_code/data/kibo_core/data/topics_ontology.json`.
