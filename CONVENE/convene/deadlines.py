"""Wall-clock deadlines for external calls, with bounded daemon workers."""
from queue import Empty, Queue
import threading
import time

_slots = threading.BoundedSemaphore(8)


class DeadlineError(ValueError):
    pass


def remaining(deadline: float) -> float:
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise DeadlineError('Research deadline exceeded; retry fewer URLs.')
    return seconds


def bounded_call(call, *, deadline: float):
    """Return by deadline even if OS DNS/provider code stalls.

    A timed-out socket call may finish in its daemon worker. Slots are held until
    it actually exits, so repeated stalls cannot spawn unlimited workers.
    """
    wait = remaining(deadline)
    if not _slots.acquire(blocking=False):
        raise DeadlineError('Research workers are busy; retry shortly.')
    result = Queue(maxsize=1)

    def run():
        try:
            result.put((True, call()))
        except Exception as error:
            result.put((False, error))
        finally:
            _slots.release()

    threading.Thread(target=run, daemon=True).start()
    try:
        success, value = result.get(timeout=wait)
    except Empty:
        raise DeadlineError('Research deadline exceeded; retry fewer URLs.') from None
    remaining(deadline)
    if not success:
        raise value
    return value
