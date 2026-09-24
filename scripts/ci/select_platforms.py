#!/usr/bin/env python3

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: python3 -m pip install pyyaml", file=sys.stderr)
    raise


def changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatch(path, pattern)


def select_platforms(paths: list[str], mapping: dict) -> set[str]:
    all_platforms = set(mapping["all_platforms"])
    selected = set()

    for path in paths:
        matched = False
        for rule in mapping.get("rules", []):
            if any(matches(path, pattern) for pattern in rule.get("paths", [])):
                matched = True
                rule_platforms = rule.get("platforms", [])
                if rule_platforms == "all" or "all" in rule_platforms:
                    selected.update(all_platforms)
                else:
                    selected.update(rule_platforms)

        if not matched:
            print(f"Unmapped path detected: {path}")
            print("Selecting all platforms for safety.")
            return all_platforms

    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--mapping", default="scripts/ci/platform-path-map.yml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--azure-output", action="store_true")
    args = parser.parse_args()

    with Path(args.mapping).open() as f:
        mapping = yaml.safe_load(f)

    all_platforms = list(mapping["all_platforms"])
    paths = changed_files(args.base, args.head)

    if not paths:
        selected = set(all_platforms)
    else:
        selected = select_platforms(paths, mapping)

    selected_list = [p for p in all_platforms if p in selected]
    skipped_list = [p for p in all_platforms if p not in selected]

    print("Changed paths:")
    for path in paths:
        print(f"  {path}")

    print()
    print("Selected platforms:")
    for platform in selected_list:
        print(f"  {platform}")

    print()
    print("Skipped platforms:")
    for platform in skipped_list:
        print(f"  {platform}")

    if args.azure_output:
        value = ",".join(selected_list)
        print(f"##vso[task.setvariable variable=SELECTED_PLATFORMS;isOutput=true]{value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
