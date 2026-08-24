# Decoupling Hera-bench from Frappe — Step-by-Step Guide

This document is the canonical guide for how `hera-bench` was decoupled from
upstream `frappe/bench` and rebranded as the version-1 CLI for the HeraOS
ecosystem. It doubles as an audit/re-apply checklist, so it intentionally
mentions the legacy names — exclude this file when grepping for leftovers.

---

## 0. Naming decisions (the mapping table)

Every change in this rebrand follows this table:

| Old (upstream) | New (Hera) | Where |
| --- | --- | --- |
| `frappe-bench` (dist/project name) | `hera-bench` | `pyproject.toml`, `bench/__init__.py` `PROJECT_NAME`, PyPI, badges, systemd unit names |
| `frappe` (framework app / python module) | `hera` | `apps/hera`, `python -m hera.utils.bench_helper`, gunicorn `hera.app:application` |
| `FRAPPE_*` constants/env vars | `HERA_*` | `FRAPPE_VERSION`→`HERA_VERSION`, `FRAPPE_DOCKER_BUILD`→`HERA_DOCKER_BUILD`, `FRAPPE_KEY`→`HERA_KEY`, `FRAPPE_BRANCH`→`HERA_BRANCH` |
| `frappe_*` functions/keys | `hera_*` | `run_frappe_cmd`→`run_hera_cmd`, `is_frappe_app`→`is_hera_app`, `is_valid_frappe_branch`→`is_valid_hera_branch`, `get_current_frappe_version`→`get_current_hera_version`, `set_frappe_version`→`set_hera_version`, config key `frappe_user`→`hera_user` |
| `github.com/frappe/bench` | `github.com/RoyalGroupofCompanies/hera-bench` | code, docs, CI, pyproject URLs |
| `github.com/frappe/frappe` | `github.com/RoyalGroupofCompanies/hera` | default framework repo, tests, easy-install |
| `github.com/frappe/frappe_docker` | `github.com/RoyalGroupofCompanies/hera_docker` | `easy-install.py` docker assets |
| `github.com/frappe/*` (fonts, wiki, healthcare, erpnext, bench_manager examples) | `github.com/RoyalGroupofCompanies/*` | helper scripts, docs |
| `frappe.io`, `docs.frappe.io`, `frappeframework.com`, `discuss.frappe.io`, `frappecloud.com` | GitHub repo/docs/discussions URLs (marketing blocks removed) | README, issue templates, code comments |
| `frappe-bench-*` systemd units | `hera-bench-*` | `bench/config/templates/systemd/` + `bench/config/systemd.py` |
| `/etc/frappe_bench_dir`, `/etc/sudoers.d/frappe` | `/etc/hera_bench_dir`, `/etc/sudoers.d/hera` | `bench/cli.py`, `bench/utils/__init__.py` |
| `frappe_selinux` role | `hera_selinux` | `bench/playbooks/roles/`, `site.yml` |
| `frappe_spec_collector.py` | `hera_spec_collector.py` | `bench/commands/` (shell-completion collector) |
| CLI command / python package `bench` | **unchanged** | `pip install Hera-bench`, then run `bench ...` |

Why keep the `bench` package/command? It keeps this v1 a drop-in replacement:
existing muscle memory (`bench init`, `bench get-app`, …), scripts, and the
internal directory layout stay valid while all upstream branding is gone.

---

## 1. Code rebrand (what was changed, step by step)

The transformation applied these steps in exactly this order — specific URLs
first, generic tokens last, so nothing gets double-rewritten:

1. **URL rules (specific → generic)**
   - `github.com/frappe/frappe_docker` → `github.com/RoyalGroupofCompanies/hera_docker`
   - `github.com/frappe/bench` → `github.com/RoyalGroupofCompanies/hera-bench`
   - `github.com/frappe/frappe` → `github.com/RoyalGroupofCompanies/hera`
   - remaining `github.com/frappe/` → `github.com/RoyalGroupofCompanies/`
   - `docs.frappe.io/*`, `frappeframework.com/docs/*`, `frappe.io/docs/*` → `github.com/RoyalGroupofCompanies/hera-bench/tree/develop/docs`
   - `frappe.io/bench` → repo URL, `discuss.frappe.io` → repo discussions
   - `pypi.org/pypi/frappe-bench/json` → `pypi.org/pypi/hera-bench/json` (the self-update version check in `bench/utils/__init__.py`)
2. **Token rules (case variants with alphanumeric boundaries)**
   - `FRAPPE` → `HERA`, `Frappe` → `Hera`, `frappe` → `hera`
   - Boundary rule: the token matches inside `run_frappe_cmd`, `__frappe__`,
     `hera.app:application`, service filenames, etc., but never inside a
     longer alphanumeric word (so e.g. `frappecloud.com` was left for manual
     removal as marketing content).
3. **File/path renames (`git mv`)**
   - `bench/commands/frappe_spec_collector.py` → `bench/commands/hera_spec_collector.py`
   - `bench/config/templates/frappe_sudoers` → `bench/config/templates/hera_sudoers`
   - `bench/config/templates/systemd/frappe-bench-*.{service,target}` → `hera-bench-*`
   - `bench/playbooks/roles/frappe_selinux/` → `hera_selinux/` (incl. `hera_selinux.te` module name)
   - `docs/releasing_frappe_apps.md` → `docs/releasing_hera_apps.md`
4. **Hand edits the bulk pass can't safely do**
   - README top block (logo, badges, removed cloud-marketing + upstream-only links)
   - `bench/utils/__init__.py` `find_org()`: bare app names now resolve under the
     `RoyalGroupofCompanies` GitHub account instead of the upstream orgs
   - `.github/ISSUE_TEMPLATE/*`, `PULL_REQUEST_TEMPLATE.md` link targets
   - Historic upstream issue references in comments reworded to this repo

## 2. Workflow fixes (`.github/workflows/`)

> **Apply the workflow patch first.** GitHub rejects pushes that change
> workflow files from tokens without the `workflows` permission, so the
> workflow edits ship as a versioned patch instead of a direct change:
>
> ```bash
> git apply docs/patches/github-workflow-updates.patch
> git add .github/workflows && git commit -m "ci: retarget workflows to develop for Hera-bench"
> git push
> ```
>
> Run that once from your own account (which has workflow permissions).

- **Triggers**: upstream workflows fired on `main`/`v5.x`; this repo releases
  from **`develop`**, so `ci.yml`, `linters.yml`, `easy-install.yml` and
  `release.yml` now target `develop` (with `workflow_dispatch` kept).
- **`release.yml`**: publishes to PyPI via semantic-release using the
  `PYPI_USERNAME` / `PYPI_PASSWORD` repo secrets; `contents: write` permission
  added so semantic-release can push the version-bump commit and GitHub release.
- **`.releaserc`**: release branch set to `develop`; the `prepareCmd` sed now
  tolerates `-dev` suffixes when stamping `VERSION` in `bench/__init__.py`.
- **`.pre-commit-config.yaml`**: the `trailing-whitespace` hook's `files:` regex
  was `frappe.*` (matched nothing) — now `bench.*` so it covers the package.

## 3. Build & release

```bash
python3 -m pip install hatch twine
hatch build            # -> dist/hera_bench-1.0.0.tar.gz + .whl
twine check dist/*
twine upload dist/*    # with your PyPI API token (username: __token__)
```

Or just push to `develop` / run the **Release** workflow once these one-time
prerequisites are done:

1. **Create the ecosystem forks** (runtime dependencies of the tool):
   - `github.com/RoyalGroupofCompanies/hera` — fork of the framework with its python
     package renamed to `hera` (the CLI runs `-m hera.utils.bench_helper`)
   - `github.com/RoyalGroupofCompanies/hera_docker` — only needed for `easy-install.py`
   - Any default apps you want resolvable by bare name (they resolve under
     `RoyalGroupofCompanies/*`)
2. **PyPI**: register `hera-bench` (name verified available) and create an API
   token scoped to the project.
3. **GitHub secrets** (repo → Settings → Secrets and variables → Actions):
   - `PYPI_USERNAME` = `__token__`
   - `PYPI_PASSWORD` = `pypi-…` (the API token)
4. Trigger the Release workflow (or `git push origin develop`).

## 4. Verification checklist

- [ ] `grep -ri frappe . --exclude-dir=.git --exclude=decoupling-from-frappe.md` returns **0** matches
- [ ] `python -m compileall bench` clean
- [ ] `pip install -e . && bench --help` works
- [ ] unit tests that don't need the network pass
- [ ] `hatch build` + `twine check dist/*` pass
- [ ] `bench init` smoke-test against `RoyalGroupofCompanies/hera` once the fork exists

## 5. Known follow-ups (not code issues)

- CI jobs that clone the framework (`bench/tests/test_init.py`,
  production-setup tests, `easy-install.yml`) can only go green **after** the
  `RoyalGroupofCompanies/hera` (and for docker, `hera_docker`) forks exist.
- Existing benches created by the upstream tool store `frappe_user` in
  `common_site_config.json`; that key is now `hera_user` — treat v1 as a
  fresh-install tool, or migrate old configs by renaming the key.
- If the framework fork's docker build sets `FRAPPE_DOCKER_BUILD`, export
  `HERA_DOCKER_BUILD` instead (`bench/utils/bench.py` reads it).
