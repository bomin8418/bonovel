"""PyInstaller 打包入口：把 bo-novel 打包为独立可执行文件。"""

import sys

from bonovel.cli import main

if __name__ == "__main__":
    sys.exit(main())
