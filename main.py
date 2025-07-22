import configparser
import logging
from pathlib import Path
import os
from logger import setup_logger
from yandex_disc import  Yandex_disc
import time
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


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    local_path = config['SETTINGS']['local_folder']
    cloud_folder = config['SETTINGS']['cloud_folder']
    token = config['SETTINGS']['token']
    sync_period = int(config['SETTINGS']['sync_period'])
    log_path = config['SETTINGS']['log_path']
    if not os.path.exists(local_path):
        os.makedirs(local_path, exist_ok=True)
        logging.info(f"Создана папка для синхронизации: {local_path}")

    setup_logger(log_path)
    disc = Yandex_disc(cloud_folder, token)


    try:
        sync_cycle(disc, local_path)
    except Exception as e:
        logging.error(f"Первый запуск неудачный: {e}")

    while True:
        time.sleep(sync_period)
        try:
            sync_cycle(disc, local_path)
        except Exception as e:
            logging.error(f"Ошибка в цикле: {e}")

if __name__ == "__main__":
    print("Запуск синхронизатора")
    main()





