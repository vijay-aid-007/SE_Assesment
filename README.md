# Data Structures & Systems Design (SE Intern)

All the code is in `solution.py` and uses only the Python standard library. Tests are in `tests/`. The code blocks below are copied from `solution.py`, and each one comes after my explanation.

**What I assumed**
- `LRUCache(capacity)` raises `ValueError` if capacity is 0 or less. Keys can be anything hashable.
- Events are `(start, end)` tuples or 2-item lists. If start is after end, I raise `ValueError`. An empty list gives `True` and `0`.
- A zero-length event like `(5, 5)` still needs a room. It only clashes with an event running right through that moment, so `[(3, 8), (5, 5)]` needs 2 rooms.
- I sort a copy, so the caller's list is never changed.

## Problem 1: LRU Cache

### My approach

It works like a pile of books on a desk: the one I used last goes on top, and when the desk is full the bottom one goes.

I need to find a key fast and also know which key was used longest ago. A dictionary is good at the first. A list order is good at the second. So I use both: a dict from key to node, and a doubly linked list with the most recent at the front and the least recent at the back.

- `get`: find the node, move it to the front, return the value. Return -1 if the key is missing.
- `put` on an existing key: update the value and move it to the front.
- `put` on a new key when full: remove the last node, delete its key from the dict, then add the new node at the front.

```python
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
```

### Why these data structures

The dict finds a node in O(1), so I never search. The linked list moves or removes a node in O(1), because each node knows the node before and after it. An ordinary list would need O(n) to move an item.

Two small choices help. Dummy nodes at both ends mean I never check for an empty list. Each node stores its own key, so when I evict the last node I can delete it from the dict straight away.

## Problem 2: Event Scheduler

### My approach

Like a hotel desk: each meeting is a guest who needs a room, and a room that has been vacated can be given to the next guest.

I sort the events by start time. For `can_attend_all`, I go through them once and check that each one starts at or after the previous one ends. If one starts earlier, it returns `False`. Equal times are fine.

For `min_rooms_required`, I keep a min-heap of end times, one for each room in use. For each event, if the earliest end time is at or before the new start, that room is free, so I take it out. Then I add the new end time.

```python
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
```

### Why the room count works

The top of the heap is the room that frees up first. If even that room is still busy when the new event starts, every room is busy, so I need a new one. If it is free, I reuse it. So the heap only gets bigger when a new room is really needed, and its final size is the answer. Sorting by start means I never miss a room that is already free.

Another way is to sort the starts and the ends separately and walk both lists with two pointers. It is also O(n log n) and needs no heap. I used the heap because the same idea also lets me assign rooms.

## Final Discussion & Analysis

### Time & Space Complexity

`n` is the number of events and `C` is the cache capacity. A dict lookup is O(1) on average (the worst case is only with many hash collisions), so I write "avg". The whole cache uses O(C) space.

| Function | Time | Space | Why |
|---|---|---|---|
| `LRUCache.__init__` | O(1) | O(1) | Two dummy nodes and an empty dict. |
| `get` | O(1) avg | O(1) | One dict lookup and a few pointer changes. |
| `put` | O(1) avg | O(1) | A few dict operations, a few pointer changes, at most one new node. |
| `_remove`, `_add_to_front`, `_move_to_front` | O(1) | O(1) | Each one only touches nearby nodes. |
| `ThreadSafeLRUCache.get` / `put` | O(1) avg, plus waiting for the lock | O(1) | Same work as above, inside a lock. |
| `_validated_copy` | O(n) | O(n) | One pass that builds a new list. |
| `can_attend_all` | O(n log n) | O(n) | The sort takes O(n log n); the scan takes O(n). |
| `min_rooms_required` | O(n log n) | O(n) | The sort, then n heap pushes and pops at O(log n) each. |
| `assign_rooms` | O(n log n) | O(n) | The sort, then each event goes through two heaps once. |
| `_room_label` | O(log k) | O(log k) | The label for room number k has about log k letters. |

### Trade-offs: hash map plus doubly linked list

A hash map alone gives fast lookup but keeps no usage order, so finding the least recently used entry means scanning everything, which is O(n). A linked list alone keeps the order, but finding a key means walking the list, which is also O(n). Together, both steps are O(1).

The price is extra memory (two pointers per node on top of the dict entry) and more code, where pointer mistakes are easy to make. In real projects `OrderedDict` does the same job.

### Future Proofing: assigning room names

I would keep the same approach but also track which room each event gets. I keep two heaps: rooms in use as (end time, room id), and free room ids. For each event in start order, I move rooms that have ended from the first heap to the second, take the smallest free id (or make a new one), and push the new end time with that id. Ids turn into "Room A", "Room B" and so on. I keep each event's original index so the result lines up with the input. The number of rooms equals `min_rooms_required`, and it is still O(n log n).

```python
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
```

### Concurrency: making the LRU Cache thread-safe

I would put one lock around `get` and `put`, so only one thread changes the cache at a time. `get` needs it too, because it moves a node. For the same reason a read-write lock would not help: there are no read-only calls.

The downside is that threads wait for each other. To scale up, I could split the keys into shards, each with its own lock and its own LRU, though the order then only holds inside each shard. Across several machines I would use something like Redis.

```python
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
```

## How to run

Standard library only, no installs. Python 3.10 or newer.

```
python solution.py
python -m unittest discover -v
```

Run both from the folder that contains `solution.py`.