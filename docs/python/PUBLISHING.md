# Publishing setup (intent-gated — not enabled until you act)

**Status:** Workflow files are ready. **Nothing is uploaded until you deliberately publish.**

Normal `git push` to `main` only runs **CI** (tests). It does **not** publish to PyPI.

---

## What “intent to publish” means

| Action you take | What happens |
|-----------------|--------------|
| Push commits / open PR | CI only — **no** PyPI |
| Actions → **Publish** → `confirm=PUBLISH` + `testpypi` | Builds, then TestPyPI (if env + publisher set) |
| Actions → **Publish** → `confirm=PUBLISH` + `pypi` | Builds, then PyPI (if env + publisher set) |
| Create **GitHub Release** on tag `v0.1.0` (etc.) | Builds, then PyPI (if env + publisher set) |
| Dispatch with `confirm` ≠ `PUBLISH` | Build job **aborts** — no upload |

---

## One-time setup (you do this in the browser)

### A. GitHub Environments (no secrets required for OIDC)

1. Open: `https://github.com/murffious/biology_as_code/settings/environments`
2. **New environment** → name: `pypi`  
   - Optional but recommended: **Required reviewers** (you) so production needs approval.
3. **New environment** → name: `testpypi`  
   - Optional: no reviewer for dry runs.

Do **not** add `PYPI_API_TOKEN` if using Trusted Publisher (OIDC).

### B. PyPI Trusted Publisher (pending)

1. Log in: https://pypi.org  
2. Account → **Publishing** → **Add a new pending publisher** (or project → Publishing after first release).
3. Fill:

| Field | Value |
|-------|--------|
| PyPI Project Name | `biology-as-code` |
| Owner | `murffious` |
| Repository name | `biology_as_code` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

4. Save. It stays **pending** until the first successful OIDC publish from that workflow.

### C. TestPyPI (optional, recommended first)

1. https://test.pypi.org → same **Add pending publisher**
2. Same fields, but **Environment name:** `testpypi`
3. Project name still `biology-as-code`

---

## When you are ready to publish (later)

### Preferred dry run (TestPyPI)

1. Ensure TestPyPI pending publisher + GitHub env `testpypi` exist.
2. GitHub → **Actions** → **Publish** → **Run workflow**
3. `target` = `testpypi`
4. `confirm` = `PUBLISH` (exactly)
5. Run → wait for green
6. Check: `pip install -i https://test.pypi.org/simple/ biology-as-code==0.1.0`

### Production PyPI

**Option 1 — manual**

1. Actions → Publish → `target=pypi`, `confirm=PUBLISH`
2. Approve environment if reviewers required

**Option 2 — release tag**

```bash
# Only when you mean it:
git tag v0.1.0
git push origin v0.1.0
# Then GitHub → Releases → Draft a new release from v0.1.0 → Publish release
```

Bump version in `pyproject.toml` + `data/VERSION_MANIFEST.json` + `CHANGELOG.md` **before** tagging a new version.

---

## Local check (never uploads)

```bash
bash scripts/release_check.sh
# or: python -m build && twine check dist/*
```

---

## Safety summary

| Enabled now? | |
|--------------|--|
| CI on push | Yes (tests only) |
| Auto-publish on push to main | **No** |
| Publish without `PUBLISH` confirm (dispatch) | **No** |
| Publish without Release or dispatch | **No** |
| Actual upload today | **Not run by us — waiting on you** |
