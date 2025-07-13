import threading
from classes.statemanager import local_state


class KeyboardListener:
    """Listens for 'q' and stops local state"""

    def __init__(self):
        self._listening = False
        self._user_id = None

    def start_listening(self, user_id: str):
        """Start listening for 'q' and stop the user's stream when pressed"""
        if self._listening:
            return

        self._listening = True
        self._user_id = user_id

        def listen():
            while self._listening:
                try:
                    user_input = input()
                    if user_input.lower().strip() == "q":
                        print("\n[STOP] Stop signal received!")
                        local_state.stop_streaming(self._user_id)
                        break
                except (EOFError, KeyboardInterrupt):
                    break

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def stop_listening(self):
        """Stop listening"""
        self._listening = False


keyboard_listener = KeyboardListener()
