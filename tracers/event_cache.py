from collections import defaultdict


class EventCache:
    def __init__(self):
        self.first = True
        self.tracked_tids_that_cloned = set()
        self.new_pids = set()
        self.cached_events = defaultdict(list)

    def should_cache(self) -> bool:
        return len(self.tracked_tids_that_cloned) > 0

    def add(self, pid, cpu, raw_data, size):
        self.cached_events[pid].append((cpu, raw_data, size))

