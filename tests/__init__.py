"""把项目 src/ 加入 sys.path，使 `python -m unittest discover` 在任意 cwd 都能导入 src.bonovel。"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
