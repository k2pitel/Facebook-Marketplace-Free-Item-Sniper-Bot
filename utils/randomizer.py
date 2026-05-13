import random
from typing import List, Optional


class MessageRandomizer:
    """Randomly selects messages from a pool, avoiding immediate repetition."""

    def __init__(self, messages: List[str]) -> None:
        if not messages:
            raise ValueError("Message pool must not be empty.")
        self._messages = list(messages)
        self._last_message: Optional[str] = None

    def pick(self) -> str:
        """Return a randomly selected message, avoiding the last one if possible."""
        if len(self._messages) == 1:
            self._last_message = self._messages[0]
            return self._messages[0]

        candidates = [m for m in self._messages if m != self._last_message]
        message = random.choice(candidates)
        self._last_message = message
        return message
