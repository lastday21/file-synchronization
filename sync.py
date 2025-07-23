"""
Модуль sync

Содержит логику синхронизации локальной папки с облачным хранилищем через клиент Yandex_disc:
- сбор информации о локальных файлах,
- сравнение с данными облака,
- загрузка новых файлов,
- обновление изменённых,
- удаление удалённых.
"""

import logging
from pathlib import Path
import os
from datetime import datetime


def get_local_files(path, root):
    """
    Собирает все файлы в папке и возвращает их относительные пути и время последней модификации.

    :param str root_path: абсолютный путь к корневой папке синхронизации
    :return: словарь, где ключ — относительный путь файла от root_path, значение — время последней
             модификации в секундах с плавающей точкой (mtime)
    :rtype: Dict[str, float]
    """
    files = {}

    try:
        entries = list(Path(path).iterdir())
    except OSError as exc:
        logging.warning(f"Нет доступа к каталогу {path}: {exc}")
        return files

    for entry in entries:
        try:
            if entry.is_dir():
                files.update(get_local_files(entry, root))
            elif entry.is_file():
                rel = entry.relative_to(root)
                files[str(rel)] = entry.stat().st_mtime
        except OSError as exc:
            logging.warning(f"Нет доступа к {entry}: {exc}")

    return files

def sync_cycle(disk_client, local_folder):
    """
    Выполняет одну итерацию синхронизации: сверяет локальные файлы с облачными и вызывает
    соответствующие методы клиента.

    :param client: объект клиента с методами:
                   - get_info() → dict с ключом '_embedded' → 'items' (список метаданных файлов);
                   - load(local_path: str, remote_path: str) для загрузки нового файла;
                   - reload(local_path: str, remote_path: str) для перезаписи существующего;
                   - delete(remote_path: str) для удаления файла из облака.
    :param str local_folder: абсолютный путь к локальной папке синхронизации
    :return: None
    :raises Exception: при ошибках чтения файлов или сетевых запросах
    """
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