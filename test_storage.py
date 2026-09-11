import tempfile
import unittest
from pathlib import Path

from storage import MessageStore


class MessageStoreTests(unittest.TestCase):
    def test_saves_and_replaces_message_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = MessageStore(Path(directory) / "test.db")
            store.initialize()
            store.save_recipient(101, 5792274744)
            self.assertEqual(store.get_recipient(101), 5792274744)
            store.save_recipient(101, 777)
            self.assertEqual(store.get_recipient(101), 777)
            self.assertIsNone(store.get_recipient(999))


if __name__ == "__main__":
    unittest.main()
