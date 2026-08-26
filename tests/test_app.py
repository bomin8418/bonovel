"""应用分发层单元测试：按键大小写归一化等。"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from bonovel.app import App


class _StubView:
    def __init__(self):
        self.received = []
        self.resized = None

    def on_key(self, key: str, text):
        self.received.append((key, text))
        return None

    def resize(self, columns, rows):
        self.resized = (columns, rows)


class AppDispatchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data_dir = Path(self.tmp) / "data"
        self.data_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_uppercase_key_normalized_to_lowercase(self):
        app = App(directory=str(self.data_dir))
        stub = _StubView()
        app._view = stub
        for upper in ("C", "P", "G", "B", "Q", "I", "D"):
            app._dispatch(upper, upper)
        # key 归一化为小写，text 保留原样
        self.assertEqual(stub.received, [(k.lower(), k) for k in ("C", "P", "G", "B", "Q", "I", "D")])

    def test_lowercase_and_special_keys_unchanged(self):
        app = App(directory=str(self.data_dir))
        stub = _StubView()
        app._view = stub
        app._dispatch("up", None)
        app._dispatch("pagedown", None)
        app._dispatch("c", "c")
        self.assertEqual(
            stub.received,
            [("up", None), ("pagedown", None), ("c", "c")],
        )

    def test_resize_still_handled_before_normalization(self):
        app = App(directory=str(self.data_dir))
        stub = _StubView()
        app._view = stub
        from bonovel import keys

        app._dispatch(keys.RESIZE, None)
        self.assertEqual(stub.received, [])
        self.assertIsNotNone(stub.resized)


if __name__ == "__main__":
    unittest.main()
