"""
Unit tests for BudgetAwareToolNode state handling (Bug 1 regression).

selected_components has NO reducer in AgentState, so whatever the node returns
becomes the new state ("last value wins"). These tests pin the carry-forward
contract:
  * search_* turns (non-state-changing) MUST preserve the existing build
  * select_component merges a single part onto the existing build
  * optimize_build REPLACES the build (fresh system, no leakage)
  * modify_build merges its result and is injected with the current build

Fully in-memory: tool DB access (safe_search, select_component's inventory
lookup, modify_build via logic.modify_build) is stubbed; NO live MongoDB.

Run with:
    cd laptop_project && venv/bin/python -m unittest pc_builder.test_graph_state -v
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import AIMessage  # noqa: E402
from pc_builder.graph import BudgetAwareToolNode, _STATE_CHANGING_TOOLS  # noqa: E402
from pc_builder.tools import ALL_TOOLS  # noqa: E402


def full_build():
    """8-category build dict as it would live in state after optimize_build."""
    return {c: {"name": f"{c}-part", "price": 1000, "socket": "LGA 1700"}
            for c in ["cpu", "gpu", "motherboard", "memory", "storage",
                      "case", "psu", "cooler"]}


def _ai(tool_name, args, call_id="c1"):
    return AIMessage(content="", tool_calls=[
        {"name": tool_name, "args": args, "id": call_id, "type": "tool_call"}])


def make_node():
    return BudgetAwareToolNode(ALL_TOOLS)


class TestSearchPreservesBuild(unittest.TestCase):
    def test_search_cpu_does_not_wipe_selected_components(self):
        """THE Bug 1 regression: a search_cpu turn must keep the existing build."""
        node = make_node()
        build = full_build()
        state = {"messages": [_ai("search_cpu", {"query": "ryzen"})],
                 "target_budget": 69000, "selected_components": dict(build)}
        with patch("pc_builder.tools.safe_search",
                   return_value=[{"name": "Ryzen 5 8400F", "price": 5000, "socket": "AM5"}]):
            out = node(state)
        self.assertEqual(sorted(out["selected_components"].keys()), sorted(build.keys()))
        self.assertEqual(len(out["selected_components"]), 8)

    def test_search_turn_with_empty_state_stays_empty(self):
        """No prior build + search turn -> still empty (no crash, no fabrication)."""
        node = make_node()
        state = {"messages": [_ai("search_gpu", {"query": "4060"})],
                 "target_budget": 50000, "selected_components": {}}
        with patch("pc_builder.tools.safe_search", return_value=[{"name": "RTX 4060", "price": 15000}]):
            out = node(state)
        self.assertEqual(out["selected_components"], {})


class TestSelectComponentMerges(unittest.TestCase):
    def test_select_component_adds_onto_existing_build(self):
        node = make_node()
        build = full_build()
        new_cpu = {"name": "New CPU", "price": 5000, "component_id": "cid-1", "socket": "AM5"}
        state = {"messages": [_ai("select_component",
                 {"component_type": "cpu", "component_json": json.dumps(new_cpu)})],
                 "target_budget": 69000, "selected_components": dict(build)}

        class _Coll:
            def find_one(self, *a, **k):
                return {"component_id": "cid-1"}

        class _DB:
            def __getitem__(self, _):
                return _Coll()

        with patch("pc_builder.mongo_client.get_db", return_value=_DB()):
            out = node(state)
        # All 8 still present, cpu updated to the new one
        self.assertEqual(len(out["selected_components"]), 8)
        self.assertEqual(out["selected_components"]["cpu"]["name"], "New CPU")


class TestOptimizeReplaces(unittest.TestCase):
    def test_optimize_build_replaces_old_build(self):
        """A fresh optimize_build must REPLACE (not merge) — no stale leakage."""
        node = make_node()
        stale = {"gpu": {"name": "OLD-GPU-should-not-survive", "price": 9999}}
        fresh = {"selected_components": {"cpu": {"name": "Fresh CPU", "price": 5000},
                                         "gpu": {"name": "Fresh GPU", "price": 20000}},
                 "total_spend": 25000, "remaining_budget": 5000, "use_case": "gaming"}
        tool_output = "=== HAZIR BUILD ÖZETİ ===\n...\n\nJSON_DATA:\n" + json.dumps(fresh)
        state = {"messages": [_ai("optimize_build", {"budget": 30000, "use_case": "gaming"})],
                 "target_budget": 30000, "selected_components": dict(stale)}

        # Patch the bound tool's underlying call so no DB is touched.
        with patch("pc_builder.tools.logic.optimize_build", return_value=fresh):
            out = node(state)
        # Old GPU gone; only fresh parts remain
        names = {c["name"] for c in out["selected_components"].values()}
        self.assertNotIn("OLD-GPU-should-not-survive", names)
        self.assertEqual(sorted(out["selected_components"].keys()), ["cpu", "gpu"])


class TestModifyBuildNode(unittest.TestCase):
    def test_modify_build_is_state_changing(self):
        self.assertIn("modify_build", _STATE_CHANGING_TOOLS)

    def test_modify_build_receives_current_build_from_state(self):
        """The node injects current_build_json + budget + use_case; LLM only
        supplies category + constraint. Result merges onto state."""
        node = make_node()
        build = full_build()
        captured = {}

        def fake_modify(current_build, budget, category, constraint, use_case="general"):
            captured["current_build"] = current_build
            captured["budget"] = budget
            captured["use_case"] = use_case
            updated = dict(current_build)
            updated["cpu"] = {"name": "AMD Ryzen 5 8400F", "price": 6069, "socket": "AM5"}
            updated["motherboard"] = {"name": "AM5 board", "price": 10000, "socket": "AM5"}
            return {"selected_components": updated, "total_spend": 67000,
                    "remaining_budget": 2000, "use_case": use_case,
                    "platform": "AM5 / DDR5"}

        state = {"messages": [_ai("modify_build", {"category": "cpu", "constraint": "8400f"})],
                 "target_budget": 69000, "use_case": "gaming",
                 "selected_components": dict(build)}
        with patch("pc_builder.tools.logic.modify_build", side_effect=fake_modify):
            out = node(state)

        # Node injected the current build + budget + use_case
        self.assertEqual(captured["budget"], 69000)
        self.assertEqual(captured["use_case"], "gaming")
        self.assertEqual(sorted(captured["current_build"].keys()), sorted(build.keys()))
        # Result keeps all 8 categories, cpu + motherboard updated to AM5
        self.assertEqual(len(out["selected_components"]), 8)
        self.assertEqual(out["selected_components"]["cpu"]["name"], "AMD Ryzen 5 8400F")
        self.assertEqual(out["selected_components"]["motherboard"]["socket"], "AM5")
        # Tool output carries the HAZIR BUILD ÖZETİ block for the agent to copy
        self.assertIn("HAZIR BUILD ÖZETİ", out["messages"][0].content)


if __name__ == "__main__":
    unittest.main()
