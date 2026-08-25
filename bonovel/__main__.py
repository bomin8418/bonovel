"""包 CLI 入口：python -m bonovel。"""

import sys

from bonovel.cli import main

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv[1:]))
