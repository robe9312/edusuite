import os
import shutil
import datetime
from db.database import get_db_path


def local_backup(destination_dir=None):
    db_path = get_db_path()
    if destination_dir is None:
        destination_dir = os.path.join(os.path.dirname(os.path.dirname(db_path)), "backups")
    os.makedirs(destination_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"school_{timestamp}.db"
    backup_path = os.path.join(destination_dir, backup_name)
    shutil.copy2(db_path, backup_path)
    return backup_path


def list_backups(backup_dir=None):
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(get_db_path())), "backups")
    if not os.path.exists(backup_dir):
        return []
    files = [f for f in os.listdir(backup_dir) if f.endswith(".db")]
    files.sort(reverse=True)
    return [os.path.join(backup_dir, f) for f in files]


def restore_from_backup(backup_path):
    db_path = get_db_path()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    auto_backup = f"{db_path}.{timestamp}.pre_restore"
    shutil.copy2(db_path, auto_backup)
    shutil.copy2(backup_path, db_path)
    return auto_backup
