import pytest

from utils.randomizer import MessageRandomizer


class TestMessageRandomizer:
    def test_single_message_always_returns_it(self):
        r = MessageRandomizer(["only one"])
        assert r.pick() == "only one"

    def test_empty_pool_raises(self):
        with pytest.raises(ValueError):
            MessageRandomizer([])

    def test_no_immediate_repetition(self):
        messages = ["a", "b", "c"]
        r = MessageRandomizer(messages)
        last = r.pick()
        for _ in range(20):
            current = r.pick()
            assert current != last, "Same message picked twice in a row"
            last = current

    def test_all_messages_reachable(self):
        messages = ["a", "b", "c", "d", "e"]
        r = MessageRandomizer(messages)
        seen = set()
        for _ in range(200):
            seen.add(r.pick())
        assert seen == set(messages)

    def test_two_messages_alternate(self):
        r = MessageRandomizer(["x", "y"])
        results = [r.pick() for _ in range(10)]
        for i in range(1, len(results)):
            assert results[i] != results[i - 1]
