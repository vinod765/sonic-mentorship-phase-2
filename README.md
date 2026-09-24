# SONiC Mentorship Phase 2

This repository is a minimal prototype and documentation set for the problem statement:

"Enable selective commit-gating tests by mapping changed paths to the minimum relevant builds/tests; avoid running tests for untouched platforms."

It focuses on two features:

1. Path-based selective build selection
2. Failure isolation on retry

The goal is to explain the design clearly and provide a local demo that can be shown during a mentor review without requiring a full SONiC image build in a local environment.

## Problem being solved

When a PR changes only a specific part of the repository, the build/test system should not trigger all platform jobs. Instead:

- Changed files should map to the minimum relevant platforms.
- If a platform job fails, the reviewer should rerun only that failed platform.
- A manual full rerun should still be available for verification.

## Repository purpose

This repository is intentionally a small prototype, not a fork of the full SONiC build system.

It documents:

- which upstream SONiC files are relevant
- how the path-to-platform mapping should work
- how the selective build decision is made
- how retry isolation works conceptually
- how to demo the feature locally in a mentor meeting

## Core design

### Feature 1: Path-based selective build

Instead of always running the full platform matrix, the pipeline should inspect changed files and map them to relevant platforms.

Examples:

- `platform/broadcom/**` -> `broadcom`
- `platform/mellanox/**` -> `mellanox`
- `platform/marvell-prestera/**` -> `marvell-prestera-arm64`, `marvell-prestera-armhf`
- `rules/**` or `Makefile` -> all platforms
- unknown or unmapped files -> all platforms for safety

This is implemented in the prototype selector script.

### Feature 2: Retry isolation

There are two retry modes:

- `/retest failed` -> rerun only job(s) that previously failed
- `/retest all` -> rerun every platform job

This is not the same as the existing `scripts/run_with_retry` found in the real SONiC build tree. That existing script retries a single command, while this problem needs platform-level retry isolation.

## Files created in this prototype

### `scripts/ci/platform-path-map.yml`

Stores the path-to-platform mapping.

Purpose:

- Central place for mapping rules
- Easy to adjust without changing Python logic
- Lets maintainers add or remove platform mappings cleanly

### `scripts/ci/select_platforms.py`

This is the decision-making script.

Purpose:

- Reads the changed files between base and head
- Loads the mapping file
- Chooses the minimum affected platforms
- Prints selected and skipped platforms
- Emits Azure-style output variables in a format suitable for pipeline use

Important: this script does not build SONiC. It only decides which platform jobs should run.

### `scripts/ci/tests/test_select_platforms.py`

Unit tests covering:

- Broadcom-only change
- Marvell change selecting both Arch variants
- Shared change selecting all platforms
- Unknown file fallback selecting all platforms

### `scripts/ci/demo_retest.py`

A lightweight local simulator for the retry behavior.

Purpose:

- Show the difference between `/retest failed` and `/retest all`
- Provide a local mentor demo without requiring Azure or full SONiC builds
- Visually prove which platform jobs would rerun

## Files relevant from the upstream SONiC repository

These are the existing upstream files that matter for the actual implementation in the real SONiC repo.

### `azure-pipelines.yml`

Why it matters:

- Main PR pipeline entry point
- Defines the overall stage layout
- Should be updated to include a detect-changes stage before platform build jobs

### `.azure-pipelines/azure-pipelines-build.yml`

Why it matters:

- Contains the platform build groups and build options
- This file already groups platform jobs like broadcom, vs, mellanox, etc.
- This is the natural place to pass selected platform filters

### `.azure-pipelines/azure-pipelines-image-template.yml`

Why it matters:

- Builds and configures platform jobs
- Contains the actual platform make commands
- This is where the selected job executes the real build commands

### `.azure-pipelines/azure-pipelines-job-groups.yml`

Why it matters:

- Expands each platform into an Azure job
- Already supports `jobFilters`
- This is the file to target when controlling whether a job runs or is skipped

### `scripts/run_with_retry`

Why it matters:

- Already retries a single command in the real build system
- Useful for transient command-level failures
- It is distinct from the feature here, which is retrying only failed platform jobs

## How the real workflow works in the actual SONiC repo

### Initial PR build flow

1. A PR is opened or updated.
2. Azure Pipelines starts.
3. A detect-changes stage inspects the changed files.
4. The selector chooses the minimum affected platform list.
5. Only the selected platform jobs are allowed to run.
6. Untouched platform jobs are skipped.
7. Existing platform make commands execute for the selected jobs only.

### Retry failed flow

1. Reviewer comments `/retest failed`.
2. A command listener sees the comment.
3. It reads the previous Azure run for the PR.
4. It identifies which platform jobs failed.
5. A new run is queued with only those failed platforms.
6. Successful platform jobs are skipped in the rerun.

### Full rerun flow

1. Reviewer comments `/retest all`.
2. A command listener queues a new Azure run.
3. Every platform job is included.
4. All builds rerun even if previous runs already passed.

## Local demonstration plan for a mentor meeting

This prototype is designed to be demonstrated locally without running a full SONiC image build.

### Demo 1: path selection

Run:

```bash
python3 scripts/ci/select_platforms.py --base upstream/master --head HEAD --dry-run
```

This prints selected and skipped platforms.

### Demo 2: Broadcom-only selection

Create a temporary change under `platform/broadcom/` and rerun the selector.

Expected output:

```text
Selected platforms:
  broadcom
```

### Demo 3: shared change selects all platforms

Create a change under `rules/` and rerun the selector.

Expected output:

```text
Selected platforms:
  vs
  vpp
  alpinevs
  broadcom
  mellanox
  marvell-prestera-arm64
  marvell-prestera-armhf
  nvidia-bluefield
  aspeed-arm64
```

### Demo 4: retry logic

Run:

```bash
python3 scripts/ci/demo_retest.py failed --failed broadcom,nvidia-bluefield
```

Expected output:

```text
Platforms that would run:
  broadcom
  nvidia-bluefield
```

Then run:

```bash
python3 scripts/ci/demo_retest.py all
```

Expected output:

```text
Platforms that would run:
  vs
  vpp
  alpinevs
  broadcom
  mellanox
  marvell-prestera-arm64
  marvell-prestera-armhf
  nvidia-bluefield
  aspeed-arm64
```

## How to run local tests

```bash
python3 -m pip install --user pyyaml pytest
pytest -q scripts/ci/tests/test_select_platforms.py
```

This verifies the path-selection logic before integrating it into Azure.

## Summary

This repository packages the core prototype for:

- selective path-aware platform selection
- failure isolation on retry
- explanation of which upstream SONiC Azure files are relevant
- a local demo strategy suitable for a mentor review

It is intentionally focused and compact.

## Next step

The next engineering step in the real SONiC repo would be to connect the selector output into the Azure job conditions in:

- `azure-pipelines.yml`
- `.azure-pipelines/azure-pipelines-build.yml`
- `.azure-pipelines/azure-pipelines-image-template.yml`
- `.azure-pipelines/azure-pipelines-job-groups.yml`

These are the actual files that control which real platform builds run.
