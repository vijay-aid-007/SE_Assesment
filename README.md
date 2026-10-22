# Data Structures & Systems Design (SE Intern)

Two problems, solved in `solution.py` with extras in Section 3. Each explanation below is in my own words and comes before its code. The code blocks are short excerpts copied from `solution.py`.

**Assumptions**
- `capacity` is a positive integer; a value of 0 or less raises `ValueError`. Keys can be any hashable value.
- Events are `(start, end)` tuples or 2-item lists of ints or floats. `start > end` raises `ValueError`. An empty list gives `True` and `0`.
- A zero-length event `(t, t)` is valid and still needs a room. It conflicts only with an event that strictly contains `t`. Touching events and events at the same instant never conflict. So `[(5, 5)]` needs 1 room and `[(3, 8), (5, 5)]` needs 2.
- The caller's list is never changed; I sort a copy.

## Problem 1: LRU Cache

### My approach

Think of a pile of books on my desk. The book I used last goes on top. When the desk is full, I take the bottom one away.

I need two things. To find a book fast, I keep a hash map from key to node. To move a book fast, I keep a doubly linked list, with the most recent at the front and the least recent at the back.

`get` finds the node, moves it to the front, and returns its value. `put` on an existing key updates it and moves it to the front. `put` on a new key at full capacity removes the node before the tail, deletes its map entry, then adds the new node at the front.

### Code (excerpt from `solution.py`)

```python
class Node:
    """Doubly linked list node. __slots__ keeps per-node memory small."""

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: Hashable = None, value: Any = None) -> None:
        self.key = key
        self.value = value
        self.prev: Node = self  # self-links, so the type is never None
        self.next: Node = self
```

Methods of `LRUCache` (indentation kept as in the file):

```python
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
```

### Why these data structures

A library has a card catalog and a shelf. The catalog tells me where a book is, with no searching. The shelf order tells me which book was touched last. I need both.

The hash map gives O(1) lookup, because it jumps straight to the node. The doubly linked list gives O(1) moves, because a node already knows its two neighbours, so I never walk the list. I added a dummy head and tail so I never check for null. Each node also stores its key. When I evict, I need that key to delete the map entry. Without it, I would have to search the map, which is O(n).

## Problem 2: Event Scheduler

### My approach

Think of my diary. I write meetings in time order. Two meetings clash only if the next one starts before the previous one ends. If one ends at 10 and the next starts at 10, I walk straight from one to the other. That is not a clash.

So `can_attend_all` sorts by start time and checks each meeting against the one before it. If any start is earlier than the previous end, I return False. Otherwise I return True. The sort costs O(n log n) and the scan costs O(n).

### Code (excerpt from `solution.py`)

```python
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
```

### How the room count works

Think of a hotel front desk. Every meeting is a guest who needs a room. If a room has been vacated, I give it to the guest. If not, I open a new room.

I keep a min-heap of end times, one per room in use. The top is the room that frees up first. For each meeting, if the top end is at or before the new start, that room is free, so I take it back. Then I push the new end time. The most rooms in use at once is my answer. I sort by start first, so I never miss a room that has already freed up.

Two-pointer alternative: sort the start times and the end times separately.
Walk through the starts. If the next start is before the earliest unused end, I need one more room. Otherwise I move the end pointer forward.
It is also O(n log n) and needs no heap. I kept the heap because `assign_rooms` needs to know which room frees up.

## Final Discussion & Analysis

### Time & Space Complexity

`n` = number of events, `C` = cache capacity. "avg" means a hash lookup is O(1) on average and O(n) only with adversarial hash collisions. The cache as a whole uses O(C) space.

| Function | Time | Space | Why |
|---|---|---|---|
| `LRUCache.__init__` | O(1) | O(1) now, O(C) once full | Builds two sentinels and an empty dict; no loops. |
| `LRUCache.get` | O(1) avg | O(1) | One dict lookup plus a fixed number of pointer changes; no new objects. |
| `LRUCache.put` | O(1) avg | O(1) per call | One dict operation plus fixed pointer changes; at most one new node. |
| `_remove`, `_add_to_front`, `_move_to_front` | O(1) | O(1) | Each touches a fixed number of neighbours and never walks the list. |
| `ThreadSafeLRUCache.get` / `put` | O(1) avg, plus lock wait | O(1) | The same work, done inside one lock. |
| `_validated_copy` | O(n) | O(n) | One pass over the events, building a new list. |
| `can_attend_all` | O(n log n) | O(n) | The sort dominates; the scan is O(n); the sorted copy is O(n). |
| `min_rooms_required` | O(n log n) | O(n) | Sort, then n heap pushes and pops at O(log n) each; the heap can hold n end times. |
| `assign_rooms` | O(n log n) | O(n) | Sort, then each event passes through two heaps once at O(log n); the label list is O(n). |
| `_room_label` | O(log k) | O(log k) | The label for room k has about log base 26 of k letters. |

### Trade-offs: hash map plus doubly linked list

Think of a library again. A card catalog tells me where a book is. The shelf order tells me which book was used last.

A hash map alone is like a catalog with no shelf order. To find the oldest book, I would scan every entry. A linked list alone keeps the order, but finding one book means walking along the shelf, which is O(n). Together, the map jumps to the node and the list moves it, so every step is O(1).

The cost is memory and code. Each entry needs a dict slot plus a node with two pointers. There is also more pointer code to get wrong. In production I would use `OrderedDict`, which does this inside.

### Future Proofing: assigning room names

At a hotel desk, I keep a tray of free key cards and hand out the lowest number first. I would build the scheduler the same way.

I sort events by start time but keep each event's original index. A min-heap of (end time, room id) tracks rooms in use. Before each event, I move every room that has ended into a second min-heap of free room ids. If it has a room, I take the smallest id. If not, I open the next new id. I turn ids into "Room A", "Room B" and so on, and store each label at the event's original index. The room count matches `min_rooms_required`. Time is still O(n log n).

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

Think of a shop with one till. One customer is served at a time. I would add one lock and take it inside both `get` and `put`.

`get` needs the lock too, because a hit moves a node, so it writes to the list. That is why a read-write lock does not help: there are no read-only calls to run side by side. A plain `Lock` is enough, since `get` and `put` never call each other.

The cost is waiting. To scale up, I could split keys into shards by hash, each with its own lock and LRU. Order is then per shard. Beyond one machine, I would use a shared cache such as Redis.

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

Python 3.10 or newer. Standard library only, no installs.

```
python solution.py
python -m unittest discover -v
```

Run both commands from the folder that contains `solution.py`.