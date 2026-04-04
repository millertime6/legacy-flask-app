from collections import deque
from datetime import datetime, timezone


class RetryQueue:
    """Simple in-memory queue to simulate retryable integration failures."""

    def __init__(self):
        self._queue = deque()

    def enqueue(self, entity: str, operation: str, payload: dict):
        self._queue.append(
            {
                "entity": entity,
                "operation": operation,
                "payload": payload,
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
                "attempts": 0,
            }
        )

    def pop_next(self):
        if not self._queue:
            return None
        item = self._queue.popleft()
        item["attempts"] += 1
        return item

    def size(self):
        return len(self._queue)


retry_queue = RetryQueue()
