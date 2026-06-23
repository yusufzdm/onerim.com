"""
Unit tests for:
  * BudgetAwareToolNode state carry-forward (Bug 1 — selected_components wipe)
  * PCBuilderLogic.modify_build (holistic, neuro-symbolic part swap with
    mandatory platform cascade: CPU socket -> motherboard -> RAM/cooler/PSU)
  * _parse_modify_constraint constraint parsing

Fully in-memory: every DB boundary (_query_inventory, RAM/PSU helpers,
_enrich_with_offers, and the inventory collection used by select_component)
is stubbed, so NO live MongoDB / backend is required.

Run with:
    cd laptop_project && venv/bin/python -m unittest pc_builder.test_modify_build -v
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from pc_builder.logic_engine import PCBuilderLogic, _norm_socket  # noqa: E402


def make_logic():
    """Bare instance — __init__ is a no-op."""
    return PCBuilderLogic.__new__(PCBuilderLogic)


def intel_ddr5_build():
    """A complete, compatible LGA1700 / DDR5 gaming build (8 categories)."""
    return {
        "cpu": {"name": "Intel Core i5 12400F", "price": 7449, "socket": "LGA 1700", "tdp": 65},
        "gpu": {"name": "Palit RTX 5060 Ti 8GB", "price": 28174, "tdp": 180},
        "motherboard": {"name": "Gigabyte B760 DS3H DDR5 ATX", "price": 7299,
                         "socket": "LGA 1700", "memory": {"ram_type": "DDR5", "slots": 4},
                         "chipset": "Intel B760", "form_factor": "ATX",
                         "m2_slots": [{"size": "2280"}], "storage_devices": {"sata_6_gb_s": 4}},
        "memory": {"name": "ADATA DDR5-4800 32GB (2x16)", "price": 10345, "ram_type": "DDR5",
                   "capacity": 32, "modules": {"quantity": 2}, "form_factor": "DIMM"},
        "storage": {"name": "WD SN3000 1TB M.2-2280", "price": 5509, "form_factor": "M.2-2280"},
        "case": {"name": "MSI MAG FORGE 100M ATX", "price": 2762,
                 "supported_motherboard_form_factors": ["ATX"]},
        "psu": {"name": "MSI MAG A650BNL 650W", "price": 2708, "wattage": 650},
        "cooler": {"name": "MSI MAG COREFROZR AA13", "price": 1759,
                   "cpu_sockets": ["AM4", "AM5", "LGA1700"]},
    }


# ───────────────────────── Query harness ─────────────────────────

class _ModHarness:
    """Records every _query_inventory call and serves deterministic parts.

    Configurable so each test tunes which sockets/DDR types have stock.
    """

    def __init__(self, am5_cpu=True, am4_cpu=True, am5_ddr5_mb=True, am4_ddr4_mb=True,
                 am5_cooler=True, am4_cooler=True, gpu_amd=True):
        self.calls = []
        self.am5_cpu = am5_cpu
        self.am4_cpu = am4_cpu
        self.am5_ddr5_mb = am5_ddr5_mb
        self.am4_ddr4_mb = am4_ddr4_mb
        self.am5_cooler = am5_cooler
        self.am4_cooler = am4_cooler
        self.gpu_amd = gpu_amd

    def query(self, component_type, max_price=None, filters=None, cheapest=False,
              raw_match=None, exclude_low_profile=False):
        self.calls.append({"type": component_type, "max_price": max_price,
                           "filters": filters or {}, "cheapest": cheapest,
                           "raw_match": raw_match})
        f = filters or {}

        if component_type == "cpu":
            name_rx = (raw_match or {}).get("tech.name", {}).get("$regex", "") if raw_match else ""
            # Spesifik model "8400f" → AM5 Ryzen 8400F
            if name_rx and "8400" in name_rx.lower():
                return {"name": "AMD Ryzen 5 8400F 4.2 GHz 6-Core AM5",
                        "price": 6069, "socket": "AM5", "tdp": 65}
            if f.get("socket") == "AM5" and self.am5_cpu:
                return {"name": "AMD Ryzen 5 7600X AM5", "price": 8500, "socket": "AM5", "tdp": 105}
            if f.get("socket") == "AM4" and self.am4_cpu:
                return {"name": "AMD Ryzen 5 5600 AM4", "price": 4000, "socket": "AM4", "tdp": 65}
            return None

        if component_type == "motherboard":
            sock = f.get("socket")
            ddr = f.get("memory.ram_type")
            if sock == "AM5":
                if ddr in (None, "DDR5") and self.am5_ddr5_mb:
                    return {"name": "Asus PRIME B650-PLUS AM5 DDR5 ATX", "price": 10179,
                            "socket": "AM5", "memory": {"ram_type": "DDR5", "slots": 4},
                            "chipset": "AMD B650", "form_factor": "ATX",
                            "m2_slots": [{"size": "2280"}], "storage_devices": {"sata_6_gb_s": 4}}
                return None
            if sock == "AM4":
                # AM4 only has DDR4 boards in this harness
                if ddr == "DDR5":
                    return None
                if self.am4_ddr4_mb:
                    return {"name": "MSI B550 DDR4 ATX", "price": 3500, "socket": "AM4",
                            "memory": {"ram_type": "DDR4", "slots": 4}, "chipset": "AMD B550",
                            "form_factor": "ATX", "m2_slots": [{"size": "2280"}],
                            "storage_devices": {"sata_6_gb_s": 4}}
                return None
            return None

        if component_type == "cooler":
            sock = f.get("cpu_sockets")
            if sock == "AM5" and self.am5_cooler:
                return {"name": "Cooler AM5", "price": 1400, "cpu_sockets": ["AM5"]}
            if sock == "AM4" and self.am4_cooler:
                return {"name": "Cooler AM4", "price": 1200, "cpu_sockets": ["AM4"]}
            return None

        if component_type == "gpu":
            if self.gpu_amd:
                return {"name": "Asus TUF Radeon RX 9060 XT 16GB", "price": 21000, "tdp": 190}
            return {"name": "Generic GPU", "price": 15000, "tdp": 200}

        return None

    def calls_for(self, ctype):
        return [c for c in self.calls if c["type"] == ctype]


def run_modify(harness, build, budget=69000, category="cpu", constraint="8400f",
               use_case="gaming", ram_overrides=None, psu_override=None):
    """Patch every DB boundary and run modify_build."""
    logic = make_logic()
    ram_overrides = ram_overrides or {}

    def fake_best_ram(ddr_type, max_price, max_speed=None):
        if ddr_type in ram_overrides:
            return dict(ram_overrides[ddr_type])
        return {"name": f"{ddr_type} 32GB (2x16)", "price": 6000, "ram_type": ddr_type,
                "capacity": 32, "modules": {"quantity": 2}, "form_factor": "DIMM"}

    def fake_cheapest_ram(ddr_type):
        return {"name": f"{ddr_type} 16GB", "price": 3000, "ram_type": ddr_type,
                "capacity": 16, "modules": {"quantity": 2}, "form_factor": "DIMM"}

    psu_val = psu_override or {"name": "Corsair 650W", "price": 2500, "wattage": 650}

    with patch.object(logic, "_query_inventory", side_effect=harness.query), \
            patch.object(logic, "_select_best_ram", side_effect=fake_best_ram), \
            patch.object(logic, "_get_cheapest_ram_by_ddr", side_effect=fake_cheapest_ram), \
            patch.object(logic, "_select_psu", return_value=dict(psu_val)), \
            patch.object(logic, "_enrich_with_offers", return_value=None):
        result = logic.modify_build(current_build=build, budget=budget, category=category,
                                    constraint=constraint, use_case=use_case)
    return logic, result


# ───────────────────────── modify_build tests ─────────────────────────

class TestModifyBuildCpuToRyzen(unittest.TestCase):
    def test_cpu_to_8400f_cascades_motherboard_to_am5(self):
        """CPU -> 8400F (AM5): motherboard auto-changes to AM5, RAM kept (DDR5)."""
        h = _ModHarness()
        logic, res = run_modify(h, intel_ddr5_build(), constraint="8400f")
        m = res["selected_components"]
        self.assertIn("8400F", m["cpu"]["name"])
        self.assertEqual(_norm_socket(m["cpu"]["socket"]), "AM5")
        self.assertEqual(_norm_socket(m["motherboard"]["socket"]), "AM5")
        # MB DDR is DDR5 -> RAM unchanged
        self.assertEqual(m["memory"]["ram_type"], "DDR5")

    def test_preserves_unrelated_components(self):
        """GPU, storage, case, PSU are kept identical after a CPU swap."""
        base = intel_ddr5_build()
        h = _ModHarness()
        _, res = run_modify(h, base, constraint="8400f")
        m = res["selected_components"]
        for cat in ("gpu", "storage", "case", "psu"):
            self.assertEqual(m[cat]["name"], base[cat]["name"],
                             f"{cat} should be preserved unchanged")

    def test_total_within_budget(self):
        h = _ModHarness()
        _, res = run_modify(h, intel_ddr5_build(), budget=69000, constraint="8400f")
        self.assertLessEqual(res["total_spend"], 69000)

    def test_result_is_compatible(self):
        """The modified build passes check_compatibility (no socket/RAM errors)."""
        h = _ModHarness()
        logic, res = run_modify(h, intel_ddr5_build(), constraint="8400f")
        compat = logic.check_compatibility(res["selected_components"])
        self.assertTrue(compat["valid"], f"unexpected errors: {compat.get('errors')}")
        self.assertEqual(compat["errors"], [])

    def test_result_shape_matches_optimize(self):
        """Same schema as optimize_build: selected_components + total_spend +
        remaining_budget + platform."""
        h = _ModHarness()
        _, res = run_modify(h, intel_ddr5_build(), constraint="8400f")
        for key in ("selected_components", "total_spend", "remaining_budget",
                    "use_case", "platform"):
            self.assertIn(key, res)
        self.assertEqual(res["remaining_budget"], 69000 - res["total_spend"])

    def test_brand_only_ryzen_picks_am5(self):
        """constraint='ryzen' (no model) -> AM5 Ryzen + AM5 motherboard."""
        h = _ModHarness()
        _, res = run_modify(h, intel_ddr5_build(), constraint="ryzen")
        m = res["selected_components"]
        self.assertIn("Ryzen", m["cpu"]["name"])
        self.assertEqual(_norm_socket(m["cpu"]["socket"]), "AM5")
        self.assertEqual(_norm_socket(m["motherboard"]["socket"]), "AM5")


class TestModifyBuildDdrCascade(unittest.TestCase):
    def test_am4_constraint_converts_ddr5_to_ddr4(self):
        """CPU -> AM4 where only DDR4 boards exist: RAM converts DDR5 -> DDR4,
        capacity preserved."""
        h = _ModHarness(am5_cpu=False)  # force AM4 path via socket constraint
        logic, res = run_modify(h, intel_ddr5_build(), constraint="AM4", budget=60000)
        m = res["selected_components"]
        self.assertEqual(_norm_socket(m["cpu"]["socket"]), "AM4")
        self.assertEqual(_norm_socket(m["motherboard"]["socket"]), "AM4")
        self.assertEqual(logic._mobo_ddr(m["motherboard"]), "DDR4")
        self.assertEqual(m["memory"]["ram_type"], "DDR4")
        self.assertEqual(m["memory"]["capacity"], 32)  # kept capacity tier
        self.assertTrue(logic.check_compatibility(m)["valid"])


class TestModifyBuildCoolerCascade(unittest.TestCase):
    def test_incompatible_cooler_is_replaced(self):
        """Existing cooler that does NOT list the new socket gets re-selected."""
        build = intel_ddr5_build()
        build["cooler"] = {"name": "Intel-only cooler", "price": 1500,
                           "cpu_sockets": ["LGA1700"]}  # no AM5
        h = _ModHarness()
        _, res = run_modify(h, build, constraint="8400f")
        m = res["selected_components"]
        # New cooler must support AM5
        cooler_sockets = [_norm_socket(s) for s in m["cooler"].get("cpu_sockets", [])]
        self.assertIn("AM5", cooler_sockets)
        self.assertNotEqual(m["cooler"]["name"], "Intel-only cooler")

    def test_compatible_cooler_is_kept(self):
        """A cooler already listing AM5 is NOT swapped (cost-preserving)."""
        build = intel_ddr5_build()  # cooler lists AM4/AM5/LGA1700
        h = _ModHarness()
        _, res = run_modify(h, build, constraint="8400f")
        self.assertEqual(res["selected_components"]["cooler"]["name"],
                         "MSI MAG COREFROZR AA13")


class TestModifyBuildNonCpu(unittest.TestCase):
    def test_gpu_swap_preserves_cpu_and_platform(self):
        """Changing GPU does not touch CPU/motherboard/RAM."""
        base = intel_ddr5_build()
        h = _ModHarness()
        _, res = run_modify(h, base, category="gpu", constraint="amd")
        m = res["selected_components"]
        self.assertEqual(m["cpu"]["name"], base["cpu"]["name"])
        self.assertEqual(m["motherboard"]["name"], base["motherboard"]["name"])
        self.assertEqual(m["memory"]["name"], base["memory"]["name"])
        # GPU actually changed to an AMD/Radeon card
        self.assertIn("Radeon", m["gpu"]["name"])

    def test_gpu_swap_raises_psu_when_needed(self):
        """A higher-TDP GPU forces a PSU upgrade if the current PSU is too small."""
        base = intel_ddr5_build()
        base["psu"] = {"name": "Weak 400W", "price": 1500, "wattage": 400}
        h = _ModHarness(gpu_amd=False)  # generic 200W TDP GPU
        big_psu = {"name": "Corsair 750W", "price": 3000, "wattage": 750}
        _, res = run_modify(h, base, category="gpu", constraint="rtx",
                            psu_override=big_psu)
        m = res["selected_components"]
        self.assertGreaterEqual(int(m["psu"]["wattage"]), 650)


class TestModifyBuildGuards(unittest.TestCase):
    def test_no_match_keeps_build_unchanged(self):
        """If no CPU matches the constraint anywhere, build is returned unchanged
        with a warning (constraint never silently dropped)."""
        base = intel_ddr5_build()
        h = _ModHarness(am5_cpu=False, am4_cpu=False)
        # constraint with a model regex that the harness never returns
        _, res = run_modify(h, base, constraint="threadripper9999")
        m = res["selected_components"]
        self.assertEqual(m["cpu"]["name"], base["cpu"]["name"])
        self.assertTrue(res.get("warnings"))

    def test_empty_build_falls_back_to_optimize(self):
        """modify_build with empty current_build delegates to optimize_build."""
        logic = make_logic()
        sentinel = {"selected_components": {"cpu": {"name": "x", "price": 1}},
                    "total_spend": 1, "remaining_budget": 0, "use_case": "gaming"}
        with patch.object(logic, "optimize_build", return_value=sentinel) as opt:
            res = logic.modify_build(current_build={}, budget=50000, category="cpu",
                                     constraint="ryzen", use_case="gaming")
        opt.assert_called_once()
        self.assertEqual(res, sentinel)

    def test_missing_budget_derives_from_current_build_total(self):
        """budget=0 (state has no target_budget) -> ceiling derived from the
        current build total; the swap still completes and stays compatible."""
        h = _ModHarness()
        # budget=0 forces the fallback path inside modify_build
        logic, res = run_modify(h, intel_ddr5_build(), budget=0, constraint="8400f")
        m = res["selected_components"]
        self.assertEqual(_norm_socket(m["cpu"]["socket"]), "AM5")
        self.assertEqual(_norm_socket(m["motherboard"]["socket"]), "AM5")
        self.assertEqual(len(m), 8)
        self.assertTrue(logic.check_compatibility(m)["valid"])


# ───────────────────────── constraint parser ─────────────────────────

class TestParseConstraint(unittest.TestCase):
    def test_model_number(self):
        p = PCBuilderLogic._parse_modify_constraint("8400f")
        self.assertEqual(p["name_regex"], "8400f")
        self.assertIsNone(p["socket"])

    def test_brand_ryzen(self):
        p = PCBuilderLogic._parse_modify_constraint("işlemci ryzen olsun")
        self.assertEqual(p["brand"], "amd")
        self.assertIsNone(p["name_regex"])

    def test_socket_token(self):
        p = PCBuilderLogic._parse_modify_constraint("am4 olsun")
        self.assertEqual(p["socket"], "AM4")

    def test_brand_plus_model(self):
        p = PCBuilderLogic._parse_modify_constraint("intel i5-13400")
        self.assertEqual(p["brand"], "intel")
        self.assertIn("13400", p["name_regex"])

    def test_bare_tier_number_not_in_regex(self):
        # "ryzen 7 7700x" -> bare "7" (tier) atılır, yalnız gerçek model "7700x" kalır.
        # Aksi halde "7" neredeyse her CPU adıyla eşleşip yanlış (en ucuz) CPU seçilir.
        p = PCBuilderLogic._parse_modify_constraint("ryzen 7 7700x olsun")
        self.assertEqual(p["brand"], "amd")
        self.assertEqual(p["name_regex"], "7700x")

    def test_bare_short_number_dropped(self):
        # "ryzen 5" -> sadece marka; çıplak "5" model regex'i olmamalı (None).
        p = PCBuilderLogic._parse_modify_constraint("ryzen 5")
        self.assertEqual(p["brand"], "amd")
        self.assertIsNone(p["name_regex"])
        # RAM miktarı gibi 2 haneli çıplak sayı da model token sayılmaz.
        self.assertIsNone(PCBuilderLogic._parse_modify_constraint("gpu 16 gb")["name_regex"])

    def test_three_digit_pure_number_kept(self):
        # >=3 haneli saf sayı (4060) ve harf+rakam (i5) gerçek model token'ı sayılır.
        self.assertEqual(PCBuilderLogic._parse_modify_constraint("rtx 4060")["name_regex"], "4060")

    def test_brand_sockets_order(self):
        # Ryzen tries modern AM5 before AM4
        self.assertEqual(PCBuilderLogic._brand_sockets("amd")[0], "AM5")


if __name__ == "__main__":
    unittest.main()
