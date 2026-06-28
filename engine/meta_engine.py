"""Meta Engine for EduSuite Meta Editor

Provides high‑level operations for managing MetaEditor projects (components)
and their versioned JSON definitions stored in SQLite.
"""

from typing import List, Dict, Any, Optional

from db.database import Database


class MetaEngine:
    """Helper class encapsulating MetaEditor CRUD operations.

    The underlying schema consists of three tables:
    * components – a logical project (e.g., 'Calificaciones')
    * component_defs – versioned JSON blobs for a component
    * component_perms – permissions (not used directly here)
    """

    def __init__(self):
        self.db = Database()

    # ---------------------------------------------------------------------
    # Component (project) management
    # ---------------------------------------------------------------------
    def get_or_create_project(self, name: str, comp_type: str = 'custom') -> int:
        # Try to find existing project
        projects = self.list_projects(active_only=False)
        for p in projects:
            if p['name'] == name:
                return p['id']
        # Not found, create a new one
        return self.create_project(name, comp_type)

        """Insert a new component and return its identifier.

        Args:
            name: Human readable name of the project.
            comp_type: Arbitrary string describing the type (e.g., 'grades').
            active: 1 if the project should be listed as active.
        """
        return self.db.create_component(name, comp_type, active)

    def list_projects(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Return all components (projects)."""
        return self.db.get_all_components(active_only)

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        return self.db.get_component(project_id)

    # ---------------------------------------------------------------------
    # Version handling
    # ---------------------------------------------------------------------
    def save_version(
        self,
        project_id: int,
        json_blob: str,
        *,
        version: Optional[int] = None,
        state: str = 'draft',
        set_active: bool = False,
    ) -> int:
        """Persist a new version of a component.

        If ``version`` is omitted the engine auto‑increments based on the
        highest existing version for the component.
        """
        # The Database.save_component_def will handle inserting state
        return self.db.save_component_def(project_id, json_blob, version, state)

        """Persist a new version of a component.

        If ``version`` is omitted the engine auto‑increments based on the
        highest existing version for the component.
        """
        return self.db.save_component_def(project_id, json_blob, version)

    def get_latest_version(self, project_id: int) -> Optional[Dict[str, Any]]:
        return self.db.get_latest_component_def(project_id)

    def list_versions(self, project_id: int) -> List[Dict[str, Any]]:
        return self.db.get_all_component_defs(project_id)

    def activate_version(self, project_id: int, version_id: int) -> None:
        """Mark a version as the published one.

        Sets the given version's state to 'active' and resets others to 'draft'.
        """
        # Reset all versions of this project to draft
        self.db.execute_sql(
            "UPDATE meta_versions SET state = 'draft' WHERE project_id = ?",
            (project_id,)
        )
        # Set the selected version to active
        self.db.execute_sql(
            "UPDATE meta_versions SET state = 'active' WHERE id = ?",
            (version_id,)
        )


    # ---------------------------------------------------------------------
    # Validation utilities
    # ---------------------------------------------------------------------
    @staticmethod
    def validate_json(data: Dict[str, Any]) -> (bool, str):
        """Very basic validation for Luckysheet JSON.

        Returns a tuple ``(is_valid, message)``.
        """
        if not isinstance(data, dict):
            return False, "El JSON debe ser un objeto dict"
        if "sheetData" not in data:
            return False, "Falta la clave 'sheetData' en la configuración"
        # Additional validation rules can be added here.
        return True, "OK"

# Instantiate a singleton for convenient import
meta_engine = MetaEngine()
