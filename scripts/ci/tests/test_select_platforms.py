import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "select_platforms.py"
spec = importlib.util.spec_from_file_location("select_platforms", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ALL_PLATFORMS = {
    "vs",
    "vpp",
    "alpinevs",
    "broadcom",
    "mellanox",
    "marvell-prestera-arm64",
    "marvell-prestera-armhf",
    "nvidia-bluefield",
    "aspeed-arm64",
}


def mapping():
    return {
        "all_platforms": sorted(ALL_PLATFORMS),
        "rules": [
            {"paths": ["platform/broadcom/**"], "platforms": ["broadcom"]},
            {"paths": ["platform/marvell-prestera/**"], "platforms": ["marvell-prestera-arm64", "marvell-prestera-armhf"]},
            {"paths": ["rules/**", "Makefile", "slave.mk"], "platforms": "all"},
        ],
    }


def test_broadcom_change_selects_only_broadcom():
    result = module.select_platforms(["platform/broadcom/example.mk"], mapping())
    assert result == {"broadcom"}


def test_marvell_change_selects_both_architectures():
    result = module.select_platforms(["platform/marvell-prestera/example.mk"], mapping())
    assert result == {"marvell-prestera-arm64", "marvell-prestera-armhf"}


def test_shared_change_selects_all_platforms():
    result = module.select_platforms(["rules/config"], mapping())
    assert result == ALL_PLATFORMS


def test_unknown_change_selects_all_platforms():
    result = module.select_platforms(["new-unknown-file.txt"], mapping())
    assert result == ALL_PLATFORMS
