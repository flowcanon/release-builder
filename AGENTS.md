# Agent Guide

## Project overview

A collection of GitHub composite actions for automated rolling releases. The actions form a pipeline: build a changelog from merged PRs, bump the version, create a release PR, and optionally notify Slack.

## Repository structure

```
build-changelog/    # Generates changelog and calculates next version from merged PRs
package-version/    # Bumps version in package.json, pyproject.toml, or VERSION file
pull-request/       # Creates a release PR with updated CHANGELOG.md
slack-message/      # Sends/updates Slack notifications for release status
.github/workflows/  # Dogfood workflow — this repo uses its own actions
```

Each directory contains an `action.yml` (the composite action definition) and supporting scripts (Python).

## Release pipeline

The actions are designed to run in this order:

1. **build-changelog** — Finds merged PRs since the last git tag, generates release notes, determines version bump type (major/minor/patch) from PR title keywords, calculates the next semantic version.
2. **package-version** — Writes the new version to the project's version file.
3. **pull-request** — Updates CHANGELOG.md and creates a release PR via `peter-evans/create-pull-request`. Includes a guard against duplicate PRs and stale tags.
4. **slack-message** *(optional)* — Posts a pending/success/failure notification to Slack.

Tagging is handled externally (e.g., `salsify/action-detect-and-tag-new-version`) by detecting when the version file changes after a release PR merges.

## Conventions

- **Inputs and outputs use kebab-case** (e.g., `next-version`, `previous-version`, `has-prs`). GitHub Actions normalizes these, but always use kebab-case in workflow references.
- **Version tags are prefixed with `v`** (e.g., `v2.1.0`).
- **PR title keywords** control version bumps: `[minor]`, `(minor)`, `#minor`, `[major]`, `(major)`, `#major`. Case-insensitive. Major takes precedence over minor.
- **Python scripts** in `build-changelog/` and `slack-message/` handle text processing. They read from stdin or environment variables and write to stdout.

## Upgrading from v1 to v2

### Breaking changes

1. **Inputs and outputs renamed from snake_case to kebab-case**
   - `has_prs` → `has-prs`
   - `next_version` → `next-version`
   - `previous_version` → `previous-version`
   - `next_version` (input) → `next-version`
   - `previous_version` (input) → `previous-version`
   - `notes` and `release` are unchanged

2. **`build-changelog` requires full git history**
   - The checkout step must use `fetch-depth: 0` so all tags and history are available for changelog generation.

3. **`actions/checkout` bumped to v4**
   - Not strictly required by release-builder, but v2 examples and workflows use `actions/checkout@v4`.

### Migration checklist

- [ ] Update all `flowcanon/release-builder/*@v1` references to `@v2`
- [ ] Update `actions/checkout@v3` to `actions/checkout@v4`
- [ ] Add `fetch-depth: 0` to the checkout step before `build-changelog`
- [ ] Rename job output mappings from snake_case to kebab-case (e.g., `has_prs:` → `has-prs:`)
- [ ] Update all `needs.*.outputs.*` references to use kebab-case
- [ ] Update all action input names to kebab-case (e.g., `next_version:` → `next-version:`)

### Example diff

```yaml
# Before (v1)
- uses: actions/checkout@v3

- id: changelog
  uses: flowcanon/release-builder/build-changelog@v1

outputs:
  has_prs: ${{ steps.changelog.outputs.has_prs }}
  next_version: ${{ steps.changelog.outputs.next_version }}

# After (v2)
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- id: changelog
  uses: flowcanon/release-builder/build-changelog@v2

outputs:
  has-prs: ${{ steps.changelog.outputs.has-prs }}
  next-version: ${{ steps.changelog.outputs.next-version }}
```

## Working on this repo

- The `v2` branch is the main branch.
- This repo dogfoods its own actions — see `.github/workflows/release.yml`.
- The `VERSION` file tracks the current version (used by `salsify/action-detect-and-tag-new-version` to auto-tag).
- `fetch-depth: 0` is required in any workflow using `build-changelog` so git history and tags are available.
