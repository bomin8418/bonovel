"""命令行参数解析与应用启动入口。"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from bonovel import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bonovel",
        description="bo-novel — 面向终端的功能完善的中文小说阅读器。",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"bo-novel {__version__}",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="待导入的一个或多个 .txt 小说文件；不提供则进入交互式界面。",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        metavar="DIR",
        default=None,
        help="覆盖用户数据目录（书库/配置所在处），默认由操作系统决定。",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])

    from bonovel.app import run

    return run(files_to_import=list(args.files), data_dir=args.data_dir)


if __name__ == "__main__":
    sys.exit(main())
