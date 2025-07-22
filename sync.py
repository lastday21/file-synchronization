import logging
from pathlib import Path
import os
from datetime import datetime


def get_local_files(path, local_folder):
    root = Path(local_folder)
    curr = Path(path)
    files = {}
    for entry in curr.iterdir():
        if entry.is_dir():
            files.update(get_local_files(entry, root))
        elif entry.is_file():
            rel = entry.relative_to(root)
            files[str(rel)] = entry.stat().st_mtime
    return  files

def sync_cycle(disk_client, local_folder):
    prefix = f"disk:/{disk_client.cloud_folder}/"
    cloud_file = {}
    local_files = get_local_files(local_folder, local_folder)
    crude_remote_files = disk_client.get_info()
    items = crude_remote_files.get('_embedded', {}).get('items', [])

    for item in items:
        path_disk = item['path']
        if path_disk.startswith(prefix):
            relative_path = path_disk.removeprefix(prefix)
        else:
            logging.warning(f"Неожиданный формат пути: {path_disk}")
            continue
        time_disk = datetime.fromisoformat(item['modified']).timestamp()
        cloud_file[relative_path] = time_disk

    only_local = set(local_files) - set(cloud_file)
    only_cloud = set(cloud_file) - set(local_files)
    in_both = set(cloud_file) & set(local_files)

    for path in only_local:
        full_local = os.path.join(local_folder, path)
        try:
            disk_client.load(full_local, path)
            logging.info(f"Загружен новый файл: {path}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке {path}: {e}")

    for path in only_cloud:
        try:
            disk_client.delete(path)
            logging.info(f"Файл {path} удален")
        except Exception as e:
            logging.error(f"Не удалось удалить {path}: {e}")

    for path in in_both:
        if local_files[path] > cloud_file[path]:
            full_local = os.path.join(local_folder, path)
            try:
                disk_client.reload(full_local, path)
                logging.info(f"Обновление файла завершено: {path}")
            except Exception as e:
                logging.error(f"Ошибка при обновлении файла {path}: {e}")