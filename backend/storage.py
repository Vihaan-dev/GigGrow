import copy
import json
import os
import tempfile
import threading
from datetime import datetime

_STORE_LOCK = threading.Lock()

DEFAULT_STORE = {
    "meta": {
        "version": 1,
        "created_at": None,
        "updated_at": None,
    },
    "users": [],
    "earnings": [],
    "spending": [],
    "events": [],
}


def _utc_now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_store_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(base_dir, "data", "store.json")
    return os.getenv("DATA_FILE", default_path)


def _write_json_atomic(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", dir=directory, delete=False) as tmp:
        json.dump(data, tmp, indent=2, sort_keys=True)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name

    os.replace(temp_name, path)


def ensure_store():
    path = get_store_path()
    if os.path.exists(path):
        return

    data = copy.deepcopy(DEFAULT_STORE)
    now = _utc_now()
    data["meta"]["created_at"] = now
    data["meta"]["updated_at"] = now
    _write_json_atomic(path, data)


def _read_store_nolock():
    path = get_store_path()
    with open(path, "r") as handle:
        return json.load(handle)


def read_store():
    with _STORE_LOCK:
        ensure_store()
        data = _read_store_nolock()
        return copy.deepcopy(data)


def update_store(update_fn):
    with _STORE_LOCK:
        ensure_store()
        data = _read_store_nolock()
        result = update_fn(data)

        if "meta" not in data or not isinstance(data["meta"], dict):
            data["meta"] = {"version": 1}
        if data["meta"].get("created_at") is None:
            data["meta"]["created_at"] = _utc_now()
        data["meta"]["updated_at"] = _utc_now()

        _write_json_atomic(get_store_path(), data)
        return result


def next_id(items):
    if not items:
        return 1
    return max(item.get("id", 0) for item in items) + 1
