#!/usr/bin/env python3
"""bo-novel 统一启动器：一条命令启动或测试（跨平台，无需 PYTHONPATH）。

用法：
    python run.py             启动阅读器
    python run.py --test      运行整套单元测试
    python run.py --version   查看版本
    python run.py 小说.txt    导入并阅读
    python run.py -d 目录     指定数据目录

其余参数原样透传给 bonovel.cli.main。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _run_tests() -> int:
    import unittest

    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), top_level_dir=str(ROOT)
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--test":
        return _run_tests()
    from bonovel.cli import main as app_main

    return app_main(argv=args)


if __name__ == "__main__":
    sys.exit(main())
