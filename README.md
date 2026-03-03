# Release builder

This repository contains a collection of [GitHub composite actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)
used for rolling releases in our projects.

The release builder automatically generates changelogs from merged pull requests since your last release tag. PR titles are collected and formatted into release notes - no manual changelog maintenance required.

## 🎯 Controlling Release Versions

**Any PR merged between release tags can control the next release version by including keywords in the PR title.**

### How It Works

The release builder scans all merged PRs between the last release tag and HEAD. If any PR title contains version keywords, the next release will use that version type:

- **`[minor]`, `(minor)`, or `#minor`** → Next release will be a **minor version bump** (e.g., `1.2.3` → `1.3.0`)
- **`[major]`, `(major)`, or `#major`** → Next release will be a **major version bump** (e.g., `1.2.3` → `2.0.0`)
- **No keywords** → Defaults to **patch version bump** (e.g., `1.2.3` → `1.2.4`)

### Examples

To force a minor release, include `[minor]` in your PR title:
- ✅ `Add new authentication feature [minor]`
- ✅ `Implement user dashboard (minor)`
- ✅ `Update API endpoints #minor`

**Important:**
- Keywords are case-insensitive
- `[major]` takes precedence over `[minor]` if both appear
- Only one PR with `[minor]` is needed to trigger a minor release for all PRs in that batch
- The keyword can appear anywhere in the PR title

### Example Scenario

If you merge these PRs between releases:
1. "Fix bug in login" (no keyword → patch)
2. "Add new feature [minor]" (has keyword → minor)
3. "Fix another bug" (no keyword, but still minor due to #2)

The next release will be a **minor version bump** because at least one PR contained `[minor]`.

---

## Prerequisites

### Required Setup

1. **Version file** (if using `package-version` action) - Your repository needs one of: `package.json`/`package-lock.json` (npm), `pyproject.toml` (Python), or a plain `VERSION` file.

That's it. Both `CHANGELOG.md` and an initial release tag are **optional**:

- **No CHANGELOG.md?** The `pull-request` action creates one automatically, noting the tag from which the changelog was introduced.
- **No previous tag?** The version defaults to `0.0.0`, so your first release will be `0.0.1` (or `0.1.0`/`1.0.0` based on PR titles).

If you want to start from a specific version, create an initial tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Secrets

| Secret | Required For | Description |
|--------|--------------|-------------|
| `GITHUB_TOKEN` | All actions | Automatically provided by GitHub Actions |
| `SLACK_BOT_TOKEN` | `slack-message` | Slack bot token for posting notifications |
| `SLACK_CHANNEL` | `slack-message` | Slack channel ID for notifications |

### Repository Variables (Optional)

| Variable | Description |
|----------|-------------|
| `RELEASE_BUILDER_PENDING_ICON` | Icon URL for pending release status |
| `RELEASE_BUILDER_FAILURE_ICON` | Icon URL for failed release status |

## Actions

### build-changelog

Builds a changelog from PRs merged since the last release tag. The action automatically:
- Finds all merged PRs between the previous tag and HEAD
- Generates formatted release notes from PR titles
- Determines the next semantic version based on PR title conventions

No existing changelog content is required - notes are generated entirely from your merged PRs.

**Outputs:**

| Output | Description |
|--------|-------------|
| `has-prs` | Whether any PRs were found since the last release |
| `previous-version` | The previous release tag |
| `next-version` | The calculated next version |
| `notes` | The generated changelog notes |
| `release` | The release type (`major`, `minor`, or `patch`) |

**Semantic Versioning:**

The release type is determined by scanning PR titles for keywords:
- `[major]`, `(major)`, or `#major` - triggers a major version bump
- `[minor]`, `(minor)`, or `#minor` - triggers a minor version bump
- Otherwise defaults to `patch`

**How version detection works:**
- All merged PRs between the last release tag and HEAD are scanned
- If **any** PR title contains `[minor]`, `(minor)`, or `#minor`, the entire release batch becomes a minor version bump
- If **any** PR title contains `[major]`, `(major)`, or `#major`, the entire release batch becomes a major version bump (takes precedence over minor)
- Keywords are case-insensitive and can appear anywhere in the PR title
- If no keywords are found, defaults to patch version bump

**Usage:**

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- id: changelog
  uses: flowcanon/release-builder/build-changelog@v2
```

> **Note:** `fetch-depth: 0` is required so the action can access full git history for tag resolution.

---

### package-version

Updates the version field in your project's package file. Automatically detects the project type:
- **npm**: Updates `package.json` and `package-lock.json`
- **Python**: Updates `pyproject.toml`
- **VERSION file**: Writes the version to a plain `VERSION` file

**Inputs:**

| Input | Required | Description |
|-------|----------|-------------|
| `version` | Yes | The version string to set |

**Usage:**

```yaml
- uses: flowcanon/release-builder/package-version@v2
  with:
    version: ${{ needs.build_changelog.outputs.next-version }}
```

---

### pull-request

Creates a release pull request with an updated `CHANGELOG.md` file.

**Inputs:**

| Input | Required | Description |
|-------|----------|-------------|
| `next-version` | Yes | The version being released |
| `notes` | Yes | The changelog notes for this release |
| `previous-version` | Yes | The previous version tag |
| `release` | Yes | The release type (`major`, `minor`, or `patch`) |

**Usage:**

```yaml
- uses: flowcanon/release-builder/pull-request@v2
  with:
    next-version: ${{ needs.build_changelog.outputs.next-version }}
    notes: ${{ needs.build_changelog.outputs.notes }}
    previous-version: ${{ needs.build_changelog.outputs.previous-version }}
    release: ${{ needs.build_changelog.outputs.release }}
```

---

### slack-message

Sends Slack notifications about release status. Can send an initial "pending" message and update it with the final status.

**Inputs:**

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `channel-id` | Yes | - | The Slack channel ID to post to |
| `message-id` | No | - | Message timestamp to update (for status updates) |
| `status` | No | `pending` | Status of the release (`pending`, `success`, `failure`) |

**Outputs:**

| Output | Description |
|--------|-------------|
| `channel-id` | The channel ID (pass-through) |
| `message-id` | The message timestamp (for subsequent updates) |

**Required Environment Variables:**

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token for API access |
| `PROJECT_NAME` | Name of the project being released |
| `SLACK_BOT_TOKEN` | Slack bot token for posting messages |
| `TARGET_NAME` | Display name of the deployment target |
| `TARGET_URL` | URL of the deployment target |
| `RELEASE_PENDING_ICON` | (Optional) Icon URL for pending status |
| `RELEASE_FAILURE_ICON` | (Optional) Icon URL for failure status |

**Usage:**

```yaml
# Send initial pending message
- id: message
  uses: flowcanon/release-builder/slack-message@v2
  with:
    channel-id: ${{ env.SLACK_CHANNEL }}

# Update with final status
- if: always()
  uses: flowcanon/release-builder/slack-message@v2
  with:
    channel-id: ${{ steps.message.outputs.channel-id }}
    message-id: ${{ steps.message.outputs.message-id }}
    status: ${{ steps.deploy.conclusion }}
```

---

## Reusable Workflow (Recommended)

The easiest way to use release-builder is with the reusable workflow. It encapsulates the full pipeline with correct job ordering, preventing race conditions between tag detection and changelog building.

### Simple repo

```yaml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      force_pr:
        description: Force pull request
        type: boolean

concurrency:
  group: ${{ github.workflow }}
  cancel-in-progress: true

jobs:
  release:
    uses: flowcanon/release-builder/.github/workflows/release-pipeline.yml@v2
    with:
      force_pr: ${{ inputs.force_pr || false }}
```

### With deploy step

For repos that deploy on release, add a job that depends on the reusable workflow's outputs:

```yaml
jobs:
  release:
    uses: flowcanon/release-builder/.github/workflows/release-pipeline.yml@v2
    with:
      force_pr: ${{ inputs.force_pr || false }}

  deploy:
    if: needs.release.outputs.created-tag
    needs: release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./script/deploy
```

### Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `version-command` | string | `""` | Override for version detection (e.g., `poetry version --short`). Auto-detects from VERSION/package.json/pyproject.toml if empty. |
| `force_pr` | boolean | `false` | Force PR creation even if no PRs are found |

### Outputs

| Output | Description |
|--------|-------------|
| `created-tag` | The tag if one was created (truthy means a release shipped) |
| `current-version` | The current version from detect_release |

### Why use the reusable workflow?

When using composite actions directly, `detect_release` and `build_changelog` can run in parallel. If a PR title was renamed after the release PR was created, `build_changelog` may calculate a different version than what was tagged, opening a bogus release PR. The reusable workflow enforces `detect_release → build_changelog → create_pr` ordering, so `build_changelog` is skipped when a tag is created.

## Composite Actions

If you need more control (e.g., custom deploy steps between detection and changelog), you can use the composite actions directly. See the sections below.

## Example

This repository uses its own actions for releases. See [`.github/workflows/release.yml`](.github/workflows/release.yml) for a working implementation.

## License

See [LICENSE.md](LICENSE.md).
