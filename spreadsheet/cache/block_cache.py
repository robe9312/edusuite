from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple
from ..datasource.base import DataSource


class BlockCache:
    def __init__(self, source: DataSource, block_size: int = 100):
        self._source = source
        self._block_size = block_size
        self._cache: Dict[Tuple[int, int], Dict[Tuple[int, int], Any]] = {}
        self._loaded_blocks: Set[Tuple[int, int]] = set()

    def _block_key(self, row: int, col: int) -> Tuple[int, int]:
        return (row // self._block_size, col // self._block_size)

    def _load_block(self, br: int, bc: int) -> None:
        key = (br, bc)
        if key in self._loaded_blocks:
            return
        row_start = br * self._block_size
        col_start = bc * self._block_size
        row_end = row_start + self._block_size - 1
        col_end = col_start + self._block_size - 1
        data = self._source.load_block(row_start, col_start, row_end, col_end)
        self._cache[key] = data
        self._loaded_blocks.add(key)

    def get(self, row: int, col: int) -> Any:
        bk = self._block_key(row, col)
        self._load_block(*bk)
        return self._cache[bk].get((row, col))

    def set(self, row: int, col: int, value: Any) -> None:
        bk = self._block_key(row, col)
        if bk not in self._cache:
            self._cache[bk] = {}
            self._loaded_blocks.add(bk)
        self._cache[bk][(row, col)] = value

    def get_range(self, row_start: int, col_start: int,
                  row_end: int, col_end: int) -> Dict[Tuple[int, int], Any]:
        result = {}
        for r in range(row_start, row_end + 1):
            for c in range(col_start, col_end + 1):
                result[(r, c)] = self.get(r, c)
        return result

    def set_range(self, data: Dict[Tuple[int, int], Any]) -> None:
        for (r, c), v in data.items():
            self.set(r, c, v)

    def flush(self) -> None:
        for key, block_data in self._cache.items():
            br, bc = key
            row_start = br * self._block_size
            col_start = bc * self._block_size
            row_end = row_start + self._block_size - 1
            col_end = col_start + self._block_size - 1
            self._source.save_block(row_start, col_start, row_end, col_end, block_data)
        self._source.flush()

    def invalidate_block(self, row: int, col: int) -> None:
        bk = self._block_key(row, col)
        self._cache.pop(bk, None)
        self._loaded_blocks.discard(bk)

    def clear(self) -> None:
        self._cache.clear()
        self._loaded_blocks.clear()
