"""
Unit tests for the text_search fallback in hybrid_search.

Regression cover for the bug: technical filters (socket, memory_type, wattage)
were applied to the `inventory` collection — which has no such fields — so any
filtered fallback search returned 0 results ("AM5 soketli Ryzen bulamadım"
although stock exists). The fix makes text_search components-centric: technical
filters hit `components` (where socket/ram_type/wattage live), then an inventory
join supplies stock/price/offers.

These tests run fully in-memory: the DB boundary (get_db) is stubbed with a fake
collection that records the aggregation pipeline it receives, so NO live MongoDB
is required. Mock pattern mirrors test_logic_engine.py.

Run with:
    cd laptop_project && venv/bin/python -m unittest pc_builder.test_hybrid_search -v
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from pc_builder import hybrid_search as hs  # noqa: E402


def _stages(pipeline, op):
    """Return all stage dicts in `pipeline` that contain the given operator key."""
    return [s for s in pipeline if op in s]


def _first_match(pipeline):
    """The first $match stage — in text_search this is the components $match."""
    matches = _stages(pipeline, "$match")
    return matches[0]["$match"] if matches else None


def _post_lookup_match(pipeline):
    """The $match stage that appears AFTER the inventory $lookup (stock/price gate)."""
    seen_lookup = False
    for s in pipeline:
        if "$lookup" in s:
            seen_lookup = True
        elif "$match" in s and seen_lookup:
            return s["$match"]
    return None


class _FakeCollection:
    """Records pipelines passed to aggregate(); returns a canned non-empty result
    so text_search treats the first attempt as a hit (no regex-drop fallback)."""

    def __init__(self, result=None):
        self.pipelines = []
        self.find_filters = []
        self._result = result if result is not None else [
            {"component_id": "x", "name": "AMD Ryzen 5 7600 AM5", "socket": "AM5",
             "price": 8269, "offers": [{"retailer": "r", "price": 8269, "url": "u"}]}
        ]

    def aggregate(self, pipeline):
        self.pipelines.append(pipeline)
        return list(self._result)

    def find(self, flt, projection=None):
        self.find_filters.append(flt)
        return self

    def limit(self, n):
        return list(self._result)


class _FakeDB:
    def __init__(self, components):
        self._components = components

    def __getitem__(self, name):
        if name == "components":
            return self._components
        raise AssertionError(
            f"text_search must query 'components', not {name!r} — "
            "technical filters belong on the components collection."
        )


class TextSearchFilterPlacementTest(unittest.TestCase):
    def _run(self, query, ctype, filters=None, max_price=None, result=None):
        comp = _FakeCollection(result=result)
        with patch.object(hs, "get_db", return_value=_FakeDB(comp)):
            out = hs.text_search(query, ctype, max_price=max_price, filters=filters)
        # text_search only queries components (see _FakeDB.__getitem__ guard).
        self.assertTrue(comp.pipelines, "expected an aggregation against components")
        return out, comp.pipelines[0]

    # (a) socket lands on the components match, NOT the inventory/post-lookup gate
    def test_socket_filter_on_components_match_not_inventory(self):
        _, pipe = self._run("ryzen", "cpu", filters={"socket": "AM5"})
        comp_match = _first_match(pipe)
        self.assertEqual(comp_match.get("component_type"), "cpu")
        self.assertEqual(
            comp_match.get("socket"), "AM5",
            "socket must be matched on the components collection",
        )
        # The post-lookup (inventory) match must gate stock/price only — never socket.
        post = _post_lookup_match(pipe) or {}
        self.assertNotIn(
            "socket", post,
            "socket must NOT be applied to the inventory/post-lookup match",
        )
        self.assertTrue(post.get("in_stock"), "stock gate expected post-lookup")

    # (b) socket filter does not zero out results (regression for the live bug)
    def test_socket_filter_does_not_drop_results(self):
        out, _ = self._run("ryzen", "cpu", filters={"socket": "AM5"})
        self.assertTrue(out, "socket-filtered search must return the joined results")
        self.assertEqual(out[0]["socket"], "AM5")

    # query regex targets components name/metadata.name (inventory has no `name`)
    def test_query_regex_targets_components_name_fields(self):
        _, pipe = self._run("ryzen", "cpu", filters={"socket": "AM5"})
        comp_match = _first_match(pipe)
        or_clauses = comp_match.get("$or") or []
        regex_fields = {k for clause in or_clauses for k in clause}
        self.assertIn("name", regex_fields)
        self.assertIn("metadata.name", regex_fields)

    # the inventory join exists and pulls from the inventory collection
    def test_pipeline_joins_inventory(self):
        _, pipe = self._run("ryzen", "cpu", filters={"socket": "AM5"})
        lookups = _stages(pipe, "$lookup")
        self.assertTrue(lookups)
        self.assertEqual(lookups[0]["$lookup"]["from"], "inventory")

    # memory_type maps to top-level ram_type for RAM modules
    def test_memory_type_maps_to_ram_type_for_memory(self):
        _, pipe = self._run("ram", "memory", filters={"memory_type": "DDR5"})
        comp_match = _first_match(pipe)
        self.assertEqual(comp_match.get("ram_type"), "DDR5")
        self.assertNotIn("memory_type", comp_match)
        # memory pipeline also excludes SO-DIMM (laptop RAM)
        self.assertIn("form_factor", comp_match)

    # memory_type maps to NESTED memory.ram_type for motherboards
    def test_memory_type_maps_to_nested_for_motherboard(self):
        _, pipe = self._run("anakart", "motherboard",
                            filters={"socket": "AM5", "memory_type": "DDR5"})
        comp_match = _first_match(pipe)
        self.assertEqual(comp_match.get("socket"), "AM5")
        self.assertEqual(comp_match.get("memory.ram_type"), "DDR5")
        self.assertNotIn("memory_type", comp_match)
        self.assertNotIn("ram_type", comp_match)

    # max_price is enforced post-lookup (price lives on inventory)
    def test_max_price_applied_post_lookup(self):
        _, pipe = self._run("ryzen", "cpu", filters={"socket": "AM5"}, max_price=9000)
        post = _post_lookup_match(pipe) or {}
        self.assertEqual(post.get("price"), {"$lte": 9000})
        self.assertNotIn("price", _first_match(pipe),
                         "price must not be on the components match")

    # empty result on the regex attempt triggers a regex-drop fallback that keeps filters
    def test_empty_regex_attempt_falls_back_keeping_filters(self):
        comp = _FakeCollection(result=[])  # always empty -> both attempts empty
        with patch.object(hs, "get_db", return_value=_FakeDB(comp)):
            hs.text_search("zzz-no-match", "cpu", filters={"socket": "AM5"})
        # Two aggregate attempts: with regex, then without regex but same filters.
        self.assertEqual(len(comp.pipelines), 2)
        first, second = _first_match(comp.pipelines[0]), _first_match(comp.pipelines[1])
        self.assertIn("$or", first, "first attempt carries the query regex")
        self.assertNotIn("$or", second, "fallback drops the regex")
        self.assertEqual(second.get("socket"), "AM5",
                         "fallback must keep technical filters")

    # ignore_stock (reference mode): components find(), no inventory join, no price
    def test_ignore_stock_reference_mode_no_join(self):
        comp = _FakeCollection(result=[{"name": "Intel Core i7 4770", "socket": "LGA 1150"}])
        with patch.object(hs, "get_db", return_value=_FakeDB(comp)):
            out = hs.text_search("4770", "cpu", ignore_stock=True)
        self.assertFalse(comp.pipelines, "reference mode must not run an aggregate join")
        self.assertTrue(comp.find_filters, "reference mode uses a components find()")
        self.assertEqual(comp.find_filters[0].get("component_type"), "cpu")
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
