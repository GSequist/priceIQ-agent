import threading
from typing import Dict


class LocalStateManager:
    """Simple state manager - start/stop/get streaming state"""

    def __init__(self):
        self._streaming_users: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def start_streaming(self, user_id: str):
        """Start streaming for a user"""
        with self._lock:
            self._streaming_users[user_id] = True

    def stop_streaming(self, user_id: str):
        """Stop streaming for a user"""
        with self._lock:
            self._streaming_users[user_id] = False

    def get_state(self, user_id: str) -> bool:
        """Get streaming state for a user"""
        with self._lock:
            return self._streaming_users.get(user_id, False)


local_state = LocalStateManager()
