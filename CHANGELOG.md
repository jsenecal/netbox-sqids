# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
