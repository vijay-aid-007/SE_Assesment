"""LRUCache tests: hand-written edge cases plus a randomized cross-check."""
import random
import unittest
from collections import OrderedDict

from solution import LRUCache


class TestLRUCacheEdgeCases(unittest.TestCase):
    def test_empty_cache_misses(self):
        self.assertEqual(LRUCache(2).get("x"), -1)

    def test_put_then_get(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        self.assertEqual(cache.get("a"), 1)

    def test_capacity_one_evicts_on_every_new_key(self):
        cache = LRUCache(1)
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertEqual(cache.get("a"), -1)
        self.assertEqual(cache.get("b"), 2)

    def test_capacity_one_update_does_not_evict(self):
        cache = LRUCache(1)
        cache.put("a", 1)
        cache.put("a", 2)
        self.assertEqual(cache.get("a"), 2)

    def test_evicts_least_recently_used(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        self.assertEqual(cache.get("a"), -1)
        self.assertEqual((cache.get("b"), cache.get("c")), (2, 3))

    def test_get_marks_key_as_recent(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")
        cache.put("c", 3)  # b is now the oldest
        self.assertEqual(cache.get("b"), -1)
        self.assertEqual(cache.get("a"), 1)

    def test_update_on_full_cache_never_evicts_and_marks_recent(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 10)
        self.assertEqual((cache.get("a"), cache.get("b")), (10, 2))
        cache.put("a", 11)
        cache.put("c", 3)  # b is oldest again
        self.assertEqual(cache.get("b"), -1)
        self.assertEqual(cache.get("a"), 11)

    def test_falsy_values_are_hits(self):
        for value in (0, None, "", False, [], 0.0):
            with self.subTest(value=value):
                cache = LRUCache(2)
                cache.put("k", value)
                self.assertEqual(cache.get("k"), value)
                self.assertNotEqual(cache.get("k"), -1)

    def test_falsy_value_still_gets_evicted_in_order(self):
        cache = LRUCache(2)
        cache.put("a", 0)
        cache.put("b", None)
        cache.put("c", "")
        self.assertEqual(cache.get("a"), -1)
        self.assertIsNone(cache.get("b"))

    def test_keys_can_be_any_hashable(self):
        cache = LRUCache(10)
        keys = [(1, 2), 0, None, 3.5, frozenset({1}), ""]
        for i, key in enumerate(keys):
            cache.put(key, i)
        for i, key in enumerate(keys):
            self.assertEqual(cache.get(key), i)

    def test_evicted_key_can_be_added_again(self):
        cache = LRUCache(2)
        for key in "abc":
            cache.put(key, key)
        self.assertEqual(cache.get("a"), -1)
        cache.put("a", "again")  # evicts b
        self.assertEqual(cache.get("b"), -1)
        self.assertEqual((cache.get("a"), cache.get("c")), ("again", "c"))

    def test_large_capacity_keeps_everything(self):
        cache = LRUCache(1000)
        for i in range(1000):
            cache.put(i, i * 2)
        self.assertTrue(all(cache.get(i) == i * 2 for i in range(1000)))

    def test_invalid_capacity_raises_value_error(self):
        for capacity in (0, -1, -100):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    LRUCache(capacity)


class TestLRUCacheAgainstReferenceModel(unittest.TestCase):
    """Run the same random operations on LRUCache and an OrderedDict model."""

    def test_random_operations_match_ordered_dict(self):
        for capacity in (1, 2, 3, 7):
            for seed in range(100):
                rng = random.Random(seed)
                cache = LRUCache(capacity)
                model: OrderedDict = OrderedDict()
                for step in range(400):
                    key = rng.randint(0, 9)
                    if rng.random() < 0.5:
                        value = rng.choice([0, None, "", key, -5])
                        cache.put(key, value)
                        if key in model:
                            model.move_to_end(key)
                        elif len(model) >= capacity:
                            model.popitem(last=False)
                        model[key] = value
                    else:
                        expected = -1
                        if key in model:
                            model.move_to_end(key)
                            expected = model[key]
                        self.assertEqual(
                            cache.get(key), expected,
                            f"capacity={capacity} seed={seed} step={step}")


if __name__ == "__main__":
    unittest.main()