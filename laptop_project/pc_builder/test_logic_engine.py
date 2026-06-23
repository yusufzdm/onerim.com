"""
Unit tests for low-tier chipset exclusion and NVMe-first storage in
PCBuilderLogic.optimize_build.

These tests run fully in-memory: every DB boundary (_query_inventory,
_select_platform, _get_cheapest_ram_by_ddr, _select_psu,
_select_compatible_case and the offers-enrichment collection) is stubbed,
so NO live MongoDB / backend is required.

Run with:
    cd laptop_project && .venv/bin/python -m unittest pc_builder.test_logic_engine -v
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Proje kök dizinini path'e ekle (logic_engine de aynısını yapar)
sys.path.insert(0, str(Path(__file__).parent.parent))

from pc_builder.logic_engine import (  # noqa: E402
    PCBuilderLogic,
    LOW_TIER_CHIPSETS,
    GPU_HEAVY_USE_CASES,
)

NVME_RAW = {
    "tech.form_factor": {"$regex": r"^M\.2", "$options": "i"},
    "tech.interface": {"$regex": "PCIe", "$options": "i"},
}
CHIPSET_NIN = {"tech.chipset": {"$nin": list(LOW_TIER_CHIPSETS)}}


def make_logic():
    """Bare instance — __init__ is a no-op but __new__ avoids any surprise."""
    return PCBuilderLogic.__new__(PCBuilderLogic)


class _Harness:
    """
    Collects every _query_inventory call and serves deterministic parts so that
    optimize_build runs end to end without a DB. Subclasses / tests tune the
    return shape via overrides.
    """

    # m2_slot entries are dicts with a "size" key (matches real MB tech shape;
    # optimize_build does s.get("size") on each slot).
    _DEFAULT_SLOTS = [{"size": "2280"}]

    def __init__(self, mb_m2_slots=None, mb_returns_none_when_filtered=False,
                 storage_none_when_filtered=False):
        self.calls = []
        self.mb_m2_slots = mb_m2_slots if mb_m2_slots is not None else list(self._DEFAULT_SLOTS)
        self.mb_none_filtered = mb_returns_none_when_filtered
        self.storage_none_filtered = storage_none_when_filtered

    def query(self, component_type, max_price=None, filters=None, cheapest=False,
              raw_match=None, exclude_low_profile=False):
        self.calls.append({
            "type": component_type,
            "max_price": max_price,
            "filters": filters,
            "cheapest": cheapest,
            "raw_match": raw_match,
            "exclude_low_profile": exclude_low_profile,
        })

        if component_type == "motherboard":
            if self.mb_none_filtered and raw_match is not None:
                return None
            return {
                "price": 2000, "name": "mb-stub", "form_factor": "ATX",
                "chipset": "Intel B760", "m2_slots": list(self.mb_m2_slots),
                "storage_devices": {"sata_6_gb_s": 4},
                "memory": {"ram_type": "DDR5", "slots": 4},
            }

        if component_type == "storage":
            if self.storage_none_filtered and raw_match is not None:
                return None
            return {"price": 1500, "name": "storage-stub", "form_factor": "M.2-2280"}

        if component_type == "cpu":
            return {"price": 3000, "name": "Intel Core i5 14400F", "socket": "LGA1700",
                    "tdp": 65}

        if component_type == "gpu":
            return {"price": 6000, "name": "gpu-stub", "tdp": 200}

        # generic
        return {"price": 1000, "name": f"{component_type}-stub"}

    def calls_for(self, ctype):
        return [c for c in self.calls if c["type"] == ctype]


def run_build(harness, budget=60000, use_case="gaming"):
    """Patch every DB boundary and run optimize_build with the given harness."""
    logic = make_logic()
    ram = {"price": 2500, "name": "ram-stub", "ram_type": "DDR5",
           "capacity": 32, "speed": 5600, "modules": {"quantity": 2},
           "form_factor": "DIMM"}
    psu = {"price": 1800, "name": "psu-stub", "wattage": 650}
    case = {"price": 1200, "name": "case-stub", "form_factor": "ATX",
            "supported_motherboard_form_factors": ["ATX"]}
    platform = {"socket": "LGA1700", "ddr_type": "DDR5", "platform_floor": 7000}

    # Offers-enrichment at the end of optimize_build calls
    # get_inventory_collection() unconditionally (live DB). Stub it; parts carry
    # no "url" so the per-part offer lookup loop is skipped regardless.
    class _FakeColl:
        def find_one(self, *a, **k):
            return None

        def find(self, *a, **k):
            return self

        def sort(self, *a, **k):
            return []

    with patch.object(logic, "_query_inventory", side_effect=harness.query), \
            patch.object(logic, "_select_platform", return_value=platform), \
            patch.object(logic, "_get_cheapest_ram_by_ddr", return_value=dict(ram)), \
            patch.object(logic, "_select_best_ram", return_value=dict(ram)), \
            patch.object(logic, "_select_psu", return_value=dict(psu)), \
            patch.object(logic, "_select_compatible_case", return_value=dict(case)), \
            patch("pc_builder.mongo_client.get_inventory_collection",
                  return_value=_FakeColl()):
        result = logic.optimize_build(budget=budget, use_case=use_case)
    return result


class TestLowTierChipsetsConstant(unittest.TestCase):
    def test_contains_known_low_tier_boards(self):
        self.assertIn("Intel H610", LOW_TIER_CHIPSETS)
        self.assertIn("AMD A520", LOW_TIER_CHIPSETS)

    def test_all_entries_are_strings(self):
        self.assertTrue(all(isinstance(c, str) for c in LOW_TIER_CHIPSETS))

    def test_gpu_heavy_use_cases_shape(self):
        self.assertEqual(
            GPU_HEAVY_USE_CASES,
            {"gaming", "rendering", "architecture", "design"},
        )


class TestMotherboardChipsetExclusion(unittest.TestCase):
    def test_floor_excludes_low_tier_for_gpu_heavy(self):
        """Gap 1: GPU-heavy -> floor MB query carries the $nin chipset raw_match."""
        h = _Harness()
        run_build(h, use_case="gaming")
        floor_calls = [c for c in h.calls_for("motherboard") if c["cheapest"]]
        self.assertTrue(floor_calls, "expected a cheapest motherboard floor query")
        self.assertEqual(floor_calls[0]["raw_match"], CHIPSET_NIN)

    def test_floor_excludes_low_tier_case_insensitive(self):
        """use_case.lower() guard: mixed-case 'Gaming' still applies the filter."""
        h = _Harness()
        run_build(h, use_case="Gaming")
        floor_calls = [c for c in h.calls_for("motherboard") if c["cheapest"]]
        self.assertEqual(floor_calls[0]["raw_match"], CHIPSET_NIN)

    def test_floor_no_chipset_filter_for_office(self):
        """Gap 2: non-GPU use_case -> no chipset raw_match on ANY motherboard query."""
        h = _Harness()
        run_build(h, use_case="office")
        for c in h.calls_for("motherboard"):
            self.assertIsNone(
                c["raw_match"],
                f"office build should not apply chipset filter, got {c['raw_match']}",
            )

    def test_floor_no_chipset_filter_for_general(self):
        h = _Harness()
        run_build(h, use_case="general")
        for c in h.calls_for("motherboard"):
            self.assertIsNone(c["raw_match"])

    def test_fallback_requery_without_chipset_filter(self):
        """Gap 3: filtered MB query returns None -> unfiltered fallback re-query fires."""
        h = _Harness(mb_returns_none_when_filtered=True)
        run_build(h, use_case="gaming")
        raws = [c["raw_match"] for c in h.calls_for("motherboard")]
        # A filtered attempt (raw_match set) AND an unfiltered fallback (None).
        self.assertTrue(any(rm is not None for rm in raws), "expected a filtered MB attempt")
        self.assertTrue(any(rm is None for rm in raws), "expected an unfiltered MB fallback")


class TestNvmeFirstStorage(unittest.TestCase):
    def test_nvme_raw_match_when_m2_slots_present(self):
        """Gap 4: GPU-heavy + MB.m2_slots -> storage query uses ^M.2 + PCIe raw_match."""
        h = _Harness(mb_m2_slots=[{"size": "2280"}, {"size": "2242"}])
        run_build(h, use_case="gaming")
        storage_raws = [c["raw_match"] for c in h.calls_for("storage")]
        self.assertIn(NVME_RAW, storage_raws)

    def test_sata_fallback_when_no_nvme(self):
        """Gap 5: NVMe query returns None -> fallback re-query without form_factor/interface."""
        h = _Harness(mb_m2_slots=[{"size": "2280"}], storage_none_when_filtered=True)
        run_build(h, use_case="gaming")
        storage_raws = [c["raw_match"] for c in h.calls_for("storage")]
        self.assertTrue(any(rm is not None for rm in storage_raws), "expected NVMe attempt")
        self.assertTrue(any(rm is None for rm in storage_raws), "expected SATA fallback")

    def test_no_nvme_filter_when_m2_slots_absent(self):
        """Negative guard: empty m2_slots -> no NVMe raw_match on storage queries."""
        h = _Harness(mb_m2_slots=[])
        run_build(h, use_case="gaming")
        for c in h.calls_for("storage"):
            self.assertIsNone(c["raw_match"])

    def test_no_nvme_filter_for_office(self):
        """Negative guard: non-GPU use_case never applies the NVMe filter."""
        h = _Harness(mb_m2_slots=[{"size": "2280"}])
        run_build(h, use_case="office")
        for c in h.calls_for("storage"):
            self.assertIsNone(c["raw_match"])


class TestBuildCompletesUnderFallbacks(unittest.TestCase):
    def test_build_still_produced_with_low_tier_and_sata_fallback(self):
        h = _Harness(mb_returns_none_when_filtered=True, storage_none_when_filtered=True)
        result = run_build(h, use_case="gaming")
        comps = result["selected_components"]
        self.assertIn("motherboard", comps)
        self.assertIn("storage", comps)


if __name__ == "__main__":
    unittest.main()
