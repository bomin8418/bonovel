"""书库管理：导入记录、最近阅读、进度保存与删除。

书库清单持久化于 <data_dir>/library.json，键为书目 id（首个文件的规范化路径）
，值为 {title, files, codec, last_read, bookmarks, created, opened}。
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from bonovel import config
from bonovel.errors import LibraryError
from bonovel.parser import Novel, parse_files
from bonovel.stats import ProgressMemory


@dataclass
class Bookmark:
    """一条书签：@ 所在页的页码与可读+时间戳。"""

    page: int
    note: str = ""
    created: float = field(default_factory=lambda: __import__("time").time())

    def to_dict(self) -> dict:
        return {"page": self.page, "note": self.note, "created": self.created}

    @classmethod
    def from_dict(cls, d: dict) -> "Bookmark":
        return cls(
            page=int(d.get("page", 0)),
            note=str(d.get("note", "")),
            created=float(d.get("created", 0)),
        )


class Book:
    """书库中的一部小说条目（含进度、书签等伴随数据）。"""

    def __init__(
        self,
        book_id: str,
        title: str,
        files: List[str],
        codec: str,
        progress: Optional[ProgressMemory] = None,
        bookmarks: Optional[List[Bookmark]] = None,
        opened: float = 0.0,
        created: float = 0.0,
    ):
        self.id = book_id
        self.title = title
        self.files = files
        self.codec = codec
        self.progress = progress or ProgressMemory()
        self.bookmarks = bookmarks or []
        self.opened = opened
        self.created = created or opened


def _book_id(files: List[str]) -> str:
    """规范化书目 id：优先用首个文件路径，保证跨会话稳定。"""
    return str(Path(files[0]).resolve())


class Library:
    """书库对象：负责加载/保存 library.json 与增删查书目。"""

    def __init__(self, directory: "str | Path | None" = None):
        self.directory = config.data_dir(directory)
        self.path = self.directory / config.LIBRARY_FILENAME
        self.books: Dict[str, Book] = {}
        self._load()

    # ---- 持久化 ----
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LibraryError(f"书库文件无法读取 {self.path}：{exc}") from exc
        for key, entry in raw.items():
            try:
                files = list(entry["files"])
                self.books[key] = Book(
                    book_id=key,
                    title=str(entry.get("title", Path(files[0]).stem)),
                    files=files,
                    codec=str(entry.get("codec", "utf-8")),
                    progress=ProgressMemory.from_dict(entry.get("last_read")),
                    bookmarks=[
                        Bookmark.from_dict(b) for b in entry.get("bookmarks", [])
                    ],
                    opened=float(entry.get("opened", 0)),
                    created=float(entry.get("created", 0)),
                )
            except (KeyError, TypeError, ValueError):
                continue  # 跳过损坏条目

    def save(self) -> None:
        """原子写回 library.json。"""
        payload = {}
        for book in self.books.values():
            payload[book.id] = {
                "title": book.title,
                "files": list(book.files),
                "codec": book.codec,
                "last_read": book.progress.to_dict() if book.progress else None,
                "bookmarks": [b.to_dict() for b in book.bookmarks],
                "opened": book.opened,
                "created": book.created,
            }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=str(self.path.parent), prefix=".library-", suffix=".tmp"
            )
            try:
                with __import__("os").fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
                __import__("os").replace(tmp, self.path)
            except BaseException:
                try:
                    __import__("os").unlink(tmp)
                except OSError:
                    pass
                raise
        except OSError as exc:
            raise LibraryError(f"无法保存书库 {self.path}：{exc}") from exc

    # ---- 增删查 ----
    def insert(self, book: Book) -> None:
        self.books[book.id] = book
        self.save()

    def remove(self, book_id: str) -> None:
        if book_id in self.books:
            del self.books[book_id]
            self.save()

    def get(self, book_id: str) -> Optional[Book]:
        return self.books.get(book_id)

    def all(self) -> List[Book]:
        # 最近打开优先
        return sorted(
            self.books.values(), key=lambda b: b.opened, reverse=True
        )

    def scan_data_dir(self) -> int:
        """扫描数据目录顶层的 .txt/.TXT 文件并把书库中未收录的自动入库。

        用于支持“把小说放进数据目录、重启即现于书架”。已入库文件会跳过，
        避免每次启动重复重写。文件无法解析时跳过并保留日志。返回新入库数。
        """
        import logging

        logger = logging.getLogger("bonovel")
        added = 0
        try:
            for p in sorted(self.directory.glob("*.txt")):
                if not p.is_file():
                    continue
                bid = _book_id([str(p)])
                if bid in self.books:
                    continue
                try:
                    self.import_files([p])
                    added += 1
                except Exception as exc:  # noqa: BLE001 - 单文件失败不影响其余
                    logger.warning("自动入库失败 %s：%s", p, exc)
        except OSError as exc:  # pragma: no cover - 目录读取异常
            logger.warning("扫描数据目录失败：%s", exc)
        if added:
            self.save()
        return added

    def import_files(self, files: List["str | Path"]) -> Book:
        """解析并入库一个或多个文件，返回 Book 条目。"""
        novel = parse_files([str(f) for f in files])
        import time

        bid = _book_id(novel.files)
        existing = self.get(bid)
        now = time.time()
        if existing:
            existing.files = list(novel.files)
            existing.title = novel.title
            existing.codec = novel.codec
            existing.opened = now
            self.save()
            return existing
        book = Book(
            book_id=bid,
            title=novel.title,
            files=list(novel.files),
            codec=novel.codec,
            opened=now,
            created=now,
        )
        self.books[bid] = book
        self.save()
        return book
