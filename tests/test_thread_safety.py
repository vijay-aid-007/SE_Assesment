"""ThreadSafeLRUCache tests: API parity plus multi-threaded stress."""
import random
import sys
import threading
import unittest

from solution import LRUCache, ThreadSafeLRUCache


def assert_structure_is_sound(test, safe_cache):
    """Walk the list: links agree both ways, and it matches the dict."""
    inner = safe_cache._cache
    keys = []
    previous, node = inner._head, inner._head.next
    while node is not inner._tail:
        test.assertIs(node.prev, previous)
        keys.append(node.key)
        test.assertLessEqual(len(keys), inner.capacity, "list longer than capacity")
        previous, node = node, node.next
    test.assertIs(node.prev, previous)
    test.assertEqual(len(keys), len(set(keys)))
    test.assertEqual(set(keys), set(inner._map))


def run_threads(workers):
    errors = []
    barrier = threading.Barrier(len(workers))

    def guarded(work):
        try:
            barrier.wait()
            work()
        except Exception as exc:  # collected, then asserted on by the caller
            errors.append(exc)

    threads = [threading.Thread(target=guarded, args=(w,)) for w in workers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return errors


class TestThreadSafeLRUCache(unittest.TestCase):
    def setUp(self):
        self._old_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)  # force frequent thread switches

    def tearDown(self):
        sys.setswitchinterval(self._old_interval)

    def test_invalid_capacity_raises_value_error(self):
        with self.assertRaises(ValueError):
            ThreadSafeLRUCache(0)

    def test_single_thread_matches_plain_cache(self):
        rng = random.Random(7)
        plain, safe = LRUCache(3), ThreadSafeLRUCache(3)
        for _ in range(2000):
            key = rng.randint(0, 6)
            if rng.random() < 0.5:
                plain.put(key, key * 10)
                safe.put(key, key * 10)
            else:
                self.assertEqual(plain.get(key), safe.get(key))

    def test_falsy_values_survive(self):
        cache = ThreadSafeLRUCache(2)
        cache.put("a", 0)
        cache.put("b", None)
        self.assertEqual(cache.get("a"), 0)
        self.assertIsNone(cache.get("b"))

    def test_mixed_operations_keep_cache_consistent(self):
        cache = ThreadSafeLRUCache(16)

        def worker(thread_id):
            rng = random.Random(thread_id)
            for n in range(4000):
                key = rng.randint(0, 40)
                if rng.random() < 0.5:
                    cache.put(key, (key, thread_id, n))
                else:
                    value = cache.get(key)
                    if value != -1 and value[0] != key:
                        raise AssertionError(f"key {key} returned {value}")

        errors = run_threads([lambda i=i: worker(i) for i in range(8)])
        self.assertEqual(errors, [])
        assert_structure_is_sound(self, cache)

    def test_no_lost_writes_when_capacity_is_large(self):
        threads, per_thread = 8, 500
        cache = ThreadSafeLRUCache(threads * per_thread)

        def worker(thread_id):
            for n in range(per_thread):
                cache.put((thread_id, n), thread_id * per_thread + n)

        errors = run_threads([lambda i=i: worker(i) for i in range(threads)])
        self.assertEqual(errors, [])
        for thread_id in range(threads):
            for n in range(per_thread):
                self.assertEqual(cache.get((thread_id, n)),
                                 thread_id * per_thread + n)
        assert_structure_is_sound(self, cache)

    def test_eviction_pressure_never_exceeds_capacity(self):
        cache = ThreadSafeLRUCache(4)

        def worker(thread_id):
            for n in range(3000):
                cache.put((thread_id, n), n)

        errors = run_threads([lambda i=i: worker(i) for i in range(8)])
        self.assertEqual(errors, [])
        self.assertEqual(len(cache._cache._map), 4)
        assert_structure_is_sound(self, cache)


if __name__ == "__main__":
    unittest.main()