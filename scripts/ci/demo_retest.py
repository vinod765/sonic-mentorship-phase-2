#!/usr/bin/env python3

import argparse

ALL_PLATFORMS = [
    "vs",
    "vpp",
    "alpinevs",
    "broadcom",
    "mellanox",
    "marvell-prestera-arm64",
    "marvell-prestera-armhf",
    "nvidia-bluefield",
    "aspeed-arm64",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["failed", "all"])
    parser.add_argument("--failed", default="")
    args = parser.parse_args()

    if args.command == "all":
        selected = ALL_PLATFORMS
    else:
        failed = [p.strip() for p in args.failed.split(",") if p.strip()]
        selected = [p for p in ALL_PLATFORMS if p in failed]

    print("Platforms that would run:")
    for p in selected:
        print(f"  {p}")

    print()
    print("Platforms that would be skipped:")
    for p in ALL_PLATFORMS:
        if p not in selected:
            print(f"  {p}")


if __name__ == "__main__":
    main()
