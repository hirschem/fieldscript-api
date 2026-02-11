import threading

_usage_events = []
_usage_lock = threading.Lock()

def add_usage_event(event: dict):
    with _usage_lock:
        _usage_events.append(event)

def get_usage_events():
    with _usage_lock:
        return list(_usage_events)
