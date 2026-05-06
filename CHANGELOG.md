# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- New zensical pages: `developer/encoding.md`, `user/faq.md`, `user/recipes.md`, `user/troubleshooting.md`. Substantial expansion of existing pages (`developer/architecture.md`, `index.md`, `user/configuration.md`, `user/getting-started.md`, `user/using-sqids.md`).
- Documentation badge in the README badge row, linking to the zensical site at `jsenecal.github.io/netbox-sqids/`.

### Changed

- Release tooling: migrated from `bumpver` to `bump-my-version` (the maintained `bump2version` fork). The new tool honors `tag_name = "v{new_version}"` (which `bumpver` silently ignored, hardcoding bare-version tags). Release flow becomes `bump-my-version bump <part> && git push --follow-tags` -- `bump-my-version` does not auto-push. Manual `[Unreleased] -> [X.Y.Z]` promotion before each bump remains required (no tool reliably handles date-templated promotion across day boundaries).
- `docs.yml` workflow: added `workflow_dispatch` trigger and a self-trigger so docs deploys can be re-run on demand.
- `ci.yml`: skip workflow on PRs/pushes that only touch docs, changelog, license, Renovate/Dependabot config, or sibling workflow files (`docs.yml`, `publish.yml`, `release-drafter.yml`, `pr-title.yml`). Test matrix bumped from NetBox 4.5.7/4.5.8 to 4.5.8/4.5.10; Codecov upload gate aligned to the latest patch.

## [0.1.1] - 2026-04-28

### Added

- Canonical normalize-toolkit: `release-drafter.yml`, `pr-title.yml`, `.github/release-drafter.yml`, `.pre-commit-config.yaml`, `.git-template/hooks/commit-msg`, `uv.lock`, LICENSE file (Apache 2.0).

### Changed

- `release.yml` -> `publish.yml`. Trigger switched from `push: tags: ['v*']` to `release: types: [published]`. Build/publish split: `build` (unprivileged) -> `publish-to-pypi` (`environment: pypi` with `id-token: write`). Drops the in-workflow GitHub Release creation step (release-drafter now drafts notes from PR titles; user clicks Publish in the UI).
- `ci.yml`: switched to `uv` with caching; matrix expanded to Python 3.12-3.14 x NetBox 4.5.7/4.5.8; added migrations + makemigrations check + system check + build smoke; codecov upload via OIDC. Removed the inline `docs` job (duplicated `docs.yml`).
- `pyproject.toml`: split `zensical` out of `[dev]` into its own `[docs]` extra; `extend-exclude` for migrations; ignore `N806` globally; explicit `[tool.ruff.format]`; bumpver `CHANGELOG.md` file pattern; added Documentation URL; added Python 3.14 classifier; added test per-file ignores (`S106`, `E402`, `F841`).

## [0.1.0] - 2026-04-08

### Added

- Computed `sqid` property on every NetBox model via `SqidDescriptor`
- Custom 33-character alphabet (excludes B, I, O for visual clarity)
- `resolve_sqid()` function to decode SQIDs back to model instances
- Browser redirect view at `/plugins/sqids/<sqid>/`
- API redirect view at `/api/plugins/sqids/<sqid>/`
- Monkey-patched short URLs (`/s/<sqid>/` and `/api/s/<sqid>/`) configurable via `monkeypatched_url_prefix`
- Configurable minimum SQID length and word blocklist
- Zensical documentation site with user and developer guides
- CI workflow with test matrix (Python 3.12/3.13, NetBox 4.5.7)
- GitHub Pages documentation deployment

[0.1.0]: https://github.com/jsenecal/netbox-sqids/releases/tag/v0.1.0
