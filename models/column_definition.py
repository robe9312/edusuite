from dataclasses import dataclass, field
from typing import Optional, List


class ColumnType:
    FROZEN = "frozen"
    TEXT = "text"
    GRADE = "grade"
    COMPUTED = "computed"
    STATUS = "status"


@dataclass
class ColumnDef:
    id: str
    name: str
    col_type: str
    group: str = ""
    width: int = 100
    editable: bool = False
    align: str = "center"
    formula: str = ""
    valid_min: float = 0.0
    valid_max: float = 10.0
    valid_values: Optional[list] = None
    heatmap: bool = False
    frozen: bool = False
    meta: dict = field(default_factory=dict)
    tooltip: str = ""


def build_grade_columns(subjects, period, template_id=None):
    if template_id:
        from models.template_manager import template_manager
        cols, template = template_manager.columns_from_template(template_id)
        if cols:
            # Map template columns to spreadsheet model expected format
            # This might require a mapping function based on template types
            # For now, assuming template columns are compatible or need minimal transformation
            mapped_cols = []
            for col_data in cols:
                # Basic mapping, adjust as needed based on actual template structure
                mapped_col = ColumnDef(
                    id=col_data.get('id', col_data.get('name', str(uuid.uuid4()))),
                    name=col_data.get('name', 'Sin nombre'),
                    col_type=col_data.get('col_type', ColumnType.TEXT),
                    group=col_data.get('group', ''),
                    width=col_data.get('width', 100),
                    editable=col_data.get('editable', False),
                    align=col_data.get('align', 'center'),
                    formula=col_data.get('formula', ''),
                    valid_min=col_data.get('valid_min', 0.0),
                    valid_max=col_data.get('valid_max', 10.0),
                    valid_values=col_data.get('valid_values', None),
                    heatmap=col_data.get('heatmap', False),
                    frozen=col_data.get('frozen', False),
                    meta=col_data.get('meta', {{}}),
                    tooltip=col_data.get('tooltip', '')
                )
                mapped_cols.append(mapped_col)
            return mapped_cols, template # Return template info too, e.g., for sheet name

    # Fallback to hardcoded grade columns if no template or template loading fails
    cols = [
        ColumnDef("nombre", "Alumno", ColumnType.FROZEN, width=200, align="left", frozen=True),
    ]
    for subj in subjects:
        g = subj.get("name", "")
        cname = subj.get("short", subj.get("name", ""))
        for p in ["T1", "T2", "T3"]:
            cols.append(ColumnDef(
                id=f"{subj['id']}_{p}",
                name=p,
                col_type=ColumnType.GRADE,
                group=cname,
                width=48,
                editable=True,
                heatmap=True,
                meta={"subject_id": subj["id"], "period": p},
                tooltip=f"{cname} {p}",
            ))
        cols.append(ColumnDef(
            id=f"{subj['id']}_prom",
            name="Prom",
            col_type=ColumnType.COMPUTED,
            group=cname,
            width=52,
            formula="avg",
            heatmap=True,
            tooltip=f"{cname} Promedio",
        ))
    return cols, subjects
