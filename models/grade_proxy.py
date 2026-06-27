from PySide6.QtCore import QSortFilterProxyModel, Qt


class GradeProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self._search_text = ""
        self._filter_column = -1
        self._filter_min = 0.0
        self._filter_max = 10.0
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)

    def set_search_text(self, text):
        self._search_text = text.strip().lower()
        self.invalidateFilter()

    def set_score_filter(self, col, min_val, max_val):
        self._filter_column = col
        self._filter_min = min_val
        self._filter_max = max_val
        self.invalidateFilter()

    def clear_filters(self):
        self._search_text = ""
        self._filter_column = -1
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if self._search_text:
            idx = self.sourceModel().index(source_row, 1, source_parent)
            name = idx.data(Qt.DisplayRole) or ""
            if self._search_text not in name.lower():
                return False

        if self._filter_column >= 0:
            idx = self.sourceModel().index(source_row, self._filter_column, source_parent)
            val = idx.data(Qt.DisplayRole)
            if val is not None:
                try:
                    fval = float(val)
                    if fval < self._filter_min or fval > self._filter_max:
                        return False
                except (ValueError, TypeError):
                    return False

        return True

    def lessThan(self, left, right):
        lv = left.data(Qt.DisplayRole)
        rv = right.data(Qt.DisplayRole)
        try:
            return float(lv) < float(rv)
        except (ValueError, TypeError):
            return str(lv) < str(rv)
