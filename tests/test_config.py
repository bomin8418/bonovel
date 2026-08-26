"""配置模块单元测试：默认值、加载合并、校验、原子保存、数据目录定位。"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from bonovel import config
from bonovel.config import (
    CONFIG_FILENAME,
    default_config,
    load_config,
    save_config,
)


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = Path(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_default_config_is_complete(self):
        cfg = default_config()
        self.assertEqual(cfg["reading_mode"], "page")
        self.assertIn("theme", cfg)
        self.assertIn("font_size", cfg)
        self.assertIsNone(cfg["last_read"])

    def test_default_config_does_not_share_state(self):
        a = default_config()
        b = default_config()
        a["theme"] = "dark"
        self.assertEqual(b["theme"], "plain")

    def test_load_without_file_returns_defaults(self):
        cfg = load_config(self.tmp)
        self.assertEqual(cfg["line_spacing"], 1)

    def test_load_merges_saved_values(self):
        save_config({"theme": "dark", "font_size": 2}, self.tmp)
        cfg = load_config(self.tmp)
        self.assertEqual(cfg["theme"], "dark")
        self.assertEqual(cfg["font_size"], 2)
        # 未设置的键仍为默认
        self.assertEqual(cfg["line_spacing"], 1)

    def test_save_creates_json_file(self):
        save_config({"theme": "paper"}, self.tmp)
        path = self.dir / CONFIG_FILENAME
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "paper")

    def test_invalid_theme_rejected_on_load(self):
        (self.dir / CONFIG_FILENAME).write_text(
            json.dumps({"theme": "nonsense"}), encoding="utf-8"
        )
        with self.assertRaises(Exception):
            load_config(self.tmp)

    def test_corrupt_json_raises(self):
        (self.dir / CONFIG_FILENAME).write_text("{not json", encoding="utf-8")
        with self.assertRaises(Exception):
            load_config(self.tmp)

    def test_save_validates(self):
        with self.assertRaises(Exception):
            save_config({"reading_mode": "weird"}, self.tmp)

    def test_data_dir_override(self):
        d = config.data_dir(self.tmp)
        self.assertEqual(d, self.dir)
        self.assertTrue(d.exists())


if __name__ == "__main__":
    unittest.main()
