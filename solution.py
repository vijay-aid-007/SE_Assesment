"""Standard library only."""
from __future__ import annotations

import heapq
import threading
from typing import Any, Hashable, Iterable, Sequence

# Section 1
class Node:
    """Doubly linked list node. __slots__ keeps per-node memory small."""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: Hashable = None, value: Any = None) -> None:
        self.key = key
        self.value = value
        self.prev: Node = self  # self-links, so the type is never None
        self.next: Node = self


class LRUCache:
    """Fixed-capacity LRU cache. Most recent item sits right after head;
    least recent sits right before tail.

    Space: O(capacity) for the dict plus one node per entry.
    """

    def __init__(self, capacity: int) -> None:
        """Time O(1). Raises ValueError if capacity <= 0."""
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._map: dict[Hashable, Node] = {}
        self._head = Node()  # sentinel: most-recent side
        self._tail = Node()  # sentinel: least-recent side
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove(self, node: Node) -> None:
        """Unlink a node. O(1): only touches its two neighbours."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node) -> None:
        """Insert right after head. O(1)."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _move_to_front(self, node: Node) -> None:
        """Mark a node as most recently used. O(1)."""
        self._remove(node)
        self._add_to_front(node)

    def get(self, key: Hashable) -> Any:
        """Return the value or -1 on a miss; a hit becomes most recent.
        Time O(1): one dict lookup plus pointer moves.
        """
        node = self._map.get(key)
        if node is None:  # test presence, never truthiness: values may be 0/None
            return -1
        self._move_to_front(node)
        return node.value

    def put(self, key: Hashable, value: Any) -> None:
        """Insert or update; evict the least recent item if full.
        Time O(1): dict ops plus pointer moves.
        """
        node = self._map.get(key)
        if node is not None:  # update: never evicts
            node.value = value
            self._move_to_front(node)
            return
        if len(self._map) >= self.capacity:  # evict FIRST, then insert
            lru = self._tail.prev
            self._remove(lru)
            del self._map[lru.key]  # the node stores its key for this reason
        node = Node(key, value)
        self._map[key] = node
        self._add_to_front(node)


# Section 2
Event = Sequence[float]  # (start, end) as a tuple or a 2-item list


def _validated_copy(events: Iterable[Event]) -> list[tuple[float, float]]:
    """Return a fresh list of (start, end) tuples; raise ValueError if
    start > end. The caller's list is never touched. Time O(n), space O(n)."""
    cleaned = []
    for start, end in events:
        if start > end:
            raise ValueError(f"start {start} is after end {end}")
        cleaned.append((start, end))
    return cleaned


def can_attend_all(events: Iterable[Event]) -> bool:
    """True if no event starts before the previous one ends.
    Time O(n log n) for the sort, space O(n) for the sorted copy."""
    ordered = sorted(_validated_copy(events))
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] < previous[1]:
            return False
    return True


def min_rooms_required(events: Iterable[Event]) -> int:
    """Minimum rooms so every event has one. Heap holds one end time per
    room in use. Time O(n log n): sort plus n heap ops of O(log n).
    Space O(n) in the worst case."""
    ordered = sorted(_validated_copy(events))
    end_times: list[float] = []
    peak = 0
    for start, end in ordered:
        if end_times and end_times[0] <= start:  # earliest room is free again
            heapq.heappop(end_times)
        heapq.heappush(end_times, end)
        peak = max(peak, len(end_times))
    return peak


# Section 3
def _room_label(index: int) -> str:
    """0 -> 'Room A', 25 -> 'Room Z', 26 -> 'Room AA'. O(log index)."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return "Room " + letters


def assign_rooms(events: Iterable[Event]) -> list[str]:
    """Room label per event, aligned with the input order.
    Time O(n log n), space O(n)."""
    cleaned = _validated_copy(events)
    order = sorted(range(len(cleaned)), key=lambda i: (cleaned[i], i))
    busy: list[tuple[float, int]] = []  # (end_time, room_id)
    free_ids: list[int] = []            # released rooms, lowest id first
    rooms_created = 0
    labels = [""] * len(cleaned)
    for i in order:
        start, end = cleaned[i]
        while busy and busy[0][0] <= start:
            heapq.heappush(free_ids, heapq.heappop(busy)[1])
        if free_ids:
            room = heapq.heappop(free_ids)
        else:
            room = rooms_created
            rooms_created += 1
        heapq.heappush(busy, (end, room))
        labels[i] = _room_label(room)
    return labels


class ThreadSafeLRUCache:
    """LRUCache behind one lock. get() reorders the list, so it needs the
    lock just as much as put() does. Same time and space as LRUCache."""

    def __init__(self, capacity: int) -> None:
        self._cache = LRUCache(capacity)
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> Any:
        """Return the value or -1, atomically with the reorder."""
        with self._lock:
            return self._cache.get(key)

    def put(self, key: Hashable, value: Any) -> None:
        """Insert or update, atomically with any eviction."""
        with self._lock:
            self._cache.put(key, value)


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    print(cache.get("a"))                    # 1 (a is now most recent)
    cache.put("c", 3)                        # evicts b
    print(cache.get("b"))                    # -1
    cache.put("z", 0)                        # evicts a (least recent)
    print(cache.get("a"), cache.get("c"), cache.get("z"))  # -1 3 0

    meetings = [(0, 30), (5, 10), (15, 20)]
    print(can_attend_all(meetings))          # False
    print(min_rooms_required(meetings))      # 2
    print(assign_rooms(meetings))            # ['Room A', 'Room B', 'Room B']



