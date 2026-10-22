"""Scheduler tests: edge cases plus randomized checks against a brute force.

Zero-length convention under test: an event (t, t) conflicts only with events
that strictly contain t. Touching events and same-instant events never conflict.
"""
import copy
import random
import unittest

from solution import assign_rooms, can_attend_all, min_rooms_required


def conflicts(a, b):
    """Pairwise rule, written separately from the solution's sweep."""
    (a0, a1), (b0, b1) = a, b
    if a0 == a1 and b0 == b1:
        return False
    if a0 == a1:
        return b0 < a0 < b1
    if b0 == b1:
        return a0 < b0 < a1
    return a0 < b1 and b0 < a1


def brute_force_rooms(events):
    """Largest group of events that all need a room at one instant."""
    if not events:
        return 0
    best = 0
    for t in {x for event in events for x in event}:
        ordinary = sum(1 for s, e in events if s < e and s <= t < e)
        point = any(s == e == t for s, e in events)
        around = sum(1 for s, e in events if s < t < e)
        best = max(best, ordinary, around + 1 if point else 0)
    return best


class TestCanAttendAll(unittest.TestCase):
    def test_empty_and_single(self):
        self.assertIs(can_attend_all([]), True)
        self.assertIs(can_attend_all([(1, 2)]), True)

    def test_adjacent_events_are_fine(self):
        self.assertIs(can_attend_all([(9, 10), (10, 11), (11, 12)]), True)

    def test_overlap_detected(self):
        self.assertIs(can_attend_all([(9, 11), (10, 12)]), False)

    def test_nested_event_detected(self):
        self.assertIs(can_attend_all([(0, 30), (5, 10), (15, 20)]), False)

    def test_unsorted_input(self):
        self.assertIs(can_attend_all([(11, 12), (9, 10), (10, 11)]), True)
        self.assertIs(can_attend_all([(11, 13), (9, 10), (12, 14)]), False)

    def test_lists_and_floats(self):
        self.assertIs(can_attend_all([[9, 10], [10, 11]]), True)
        self.assertIs(can_attend_all([(0.5, 1.5), (1.5, 2.25)]), True)
        self.assertIs(can_attend_all([(0.5, 1.6), (1.5, 2.25)]), False)

    def test_zero_length_events(self):
        self.assertIs(can_attend_all([(5, 5)]), True)
        self.assertIs(can_attend_all([(5, 5), (5, 5)]), True)
        self.assertIs(can_attend_all([(5, 5), (5, 8)]), True)
        self.assertIs(can_attend_all([(3, 5), (5, 5)]), True)
        self.assertIs(can_attend_all([(3, 8), (5, 5)]), False)

    def test_invalid_event_raises(self):
        with self.assertRaises(ValueError):
            can_attend_all([(1, 2), (5, 3)])


class TestMinRoomsRequired(unittest.TestCase):
    def test_empty_and_single(self):
        self.assertEqual(min_rooms_required([]), 0)
        self.assertEqual(min_rooms_required([(1, 2)]), 1)

    def test_adjacent_events_share_a_room(self):
        self.assertEqual(min_rooms_required([(9, 10), (10, 11), (11, 12)]), 1)

    def test_classic_example(self):
        self.assertEqual(min_rooms_required([(0, 30), (5, 10), (15, 20)]), 2)

    def test_all_overlapping(self):
        self.assertEqual(min_rooms_required([(0, 10)] * 5), 5)

    def test_unsorted_and_nested(self):
        events = [(15, 20), (0, 30), (5, 10), (6, 8)]
        self.assertEqual(min_rooms_required(events), 3)

    def test_lists_and_floats(self):
        self.assertEqual(min_rooms_required([[0, 30], [5, 10], [15, 20]]), 2)
        self.assertEqual(min_rooms_required([(0.5, 1.5), (1.5, 2)]), 1)

    def test_zero_length_events_still_need_a_room(self):
        self.assertEqual(min_rooms_required([(5, 5)]), 1)
        self.assertEqual(min_rooms_required([(5, 5), (5, 5)]), 1)
        self.assertEqual(min_rooms_required([(5, 5), (5, 8)]), 1)
        self.assertEqual(min_rooms_required([(3, 8), (5, 5)]), 2)

    def test_return_types_are_exact(self):
        self.assertIs(type(min_rooms_required([])), int)
        self.assertIs(type(min_rooms_required([(1, 2)])), int)
        self.assertIs(type(can_attend_all([])), bool)

    def test_invalid_event_raises(self):
        with self.assertRaises(ValueError):
            min_rooms_required([(5, 3)])


class TestCallerInputIsNotMutated(unittest.TestCase):
    def test_functions_leave_input_alone(self):
        for func in (can_attend_all, min_rooms_required, assign_rooms):
            with self.subTest(func=func.__name__):
                events = [(15, 20), (0, 30), [5, 10]]
                snapshot = copy.deepcopy(events)
                func(events)
                self.assertEqual(events, snapshot)


class TestAssignRooms(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(assign_rooms([]), [])

    def test_classic_example(self):
        self.assertEqual(assign_rooms([(0, 30), (5, 10), (15, 20)]),
                         ["Room A", "Room B", "Room B"])

    def test_output_aligned_with_input_order(self):
        self.assertEqual(assign_rooms([(0, 2), (0, 1), (1, 3)]),
                         ["Room B", "Room A", "Room A"])

    def test_adjacent_events_reuse_room_a(self):
        self.assertEqual(assign_rooms([(9, 10), (10, 11), (11, 12)]),
                         ["Room A"] * 3)

    def test_zero_length(self):
        self.assertEqual(assign_rooms([(5, 5)]), ["Room A"])
        self.assertEqual(assign_rooms([(5, 5), (5, 8)]), ["Room A", "Room A"])

    def test_labels_continue_past_z(self):
        labels = assign_rooms([(0, 1)] * 27)
        self.assertEqual(len(set(labels)), 27)
        self.assertIn("Room Z", labels)
        self.assertIn("Room AA", labels)

    def test_invalid_event_raises(self):
        with self.assertRaises(ValueError):
            assign_rooms([(5, 3)])


class TestRandomizedAgainstBruteForce(unittest.TestCase):
    @staticmethod
    def random_events(seed):
        rng = random.Random(seed)
        events = []
        for _ in range(rng.randint(0, 10)):
            start = rng.randint(0, 10)
            events.append((start, start + rng.randint(0, 4)))
        return events

    def test_min_rooms_matches_brute_force(self):
        for seed in range(2000):
            events = self.random_events(seed)
            self.assertEqual(min_rooms_required(events),
                             brute_force_rooms(events), f"seed={seed} {events}")

    def test_can_attend_all_matches_pairwise_check(self):
        for seed in range(2000):
            events = self.random_events(seed)
            expected = not any(conflicts(a, b) for i, a in enumerate(events)
                               for b in events[i + 1:])
            self.assertEqual(can_attend_all(events), expected,
                             f"seed={seed} {events}")

    def test_assign_rooms_is_valid_and_minimal(self):
        for seed in range(2000):
            events = self.random_events(seed)
            labels = assign_rooms(events)
            self.assertEqual(len(labels), len(events))
            self.assertEqual(len(set(labels)), min_rooms_required(events),
                             f"seed={seed} {events}")
            for i, a in enumerate(events):
                for j in range(i + 1, len(events)):
                    if labels[i] == labels[j]:
                        self.assertFalse(conflicts(a, events[j]),
                                         f"seed={seed} {events} {labels}")


if __name__ == "__main__":
    unittest.main()