"""
main.py — точка входа сервиса синхронизации файлов.
"""

from __future__ import annotations

import configparser
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

import requests

from logger import setup_logger
from disc_API import Yandex_disc
from sync import sync_cycle


CONFIG_PATH = "config.ini"
REQUIRED_KEYS = ("local_folder", "cloud_folder", "token",
                 "sync_period", "log_path")


def _load_and_validate_config(path: str = CONFIG_PATH) -> Tuple[str, str, str, int, str]:
    """Читает config.ini и проверяет обязательные параметры, завершая программу при ошибках."""
    config = configparser.ConfigParser()
    if not config.read(path):
        print("config.ini не найден. Скопируйте config_template.ini и заполните параметры.")
        sys.exit(1)

    if "SETTINGS" not in config:
        print("В config.ini отсутствует секция [SETTINGS]")
        sys.exit(1)

    settings = config["SETTINGS"]
    missing = [k for k in REQUIRED_KEYS if k not in settings or not settings[k].strip()]
    if missing:
        print(f"Не заданы параметры: {', '.join(missing)}")
        sys.exit(1)

    local_folder = settings["local_folder"].strip()
    cloud_folder = settings["cloud_folder"].strip()
    token = settings["token"].strip()
    log_path = settings["log_path"].strip()

    try:
        sync_period = int(settings["sync_period"])
        if sync_period <= 0:
            raise ValueError
    except ValueError:
        print("sync_period должен быть целым числом > 0")
        sys.exit(1)

    if not Path(local_folder).is_dir():
        print(f"Папка синхронизации не найдена: {local_folder}")
        sys.exit(1)

    return local_folder, cloud_folder, token, sync_period, log_path


def _check_token(client: Yandex_disc) -> None:
    """Пробует запросить get_info(); завершает программу при 401/403."""
    try:
        client.get_info()
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            print("Неверный OAuth-токен — проверьте config.ini")
            sys.exit(1)
        raise
    except requests.RequestException as exc:
        logging.error(f"Не удалось проверить токен: {exc}")
        sys.exit(1)


def main() -> None:
    local_folder, cloud_folder, token, sync_period, log_path = _load_and_validate_config()
    print("Синхронизатор запущен.")

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    setup_logger(log_path)
    logging.info(f"Запуск программы: {datetime.now().isoformat()}, папка={local_folder}")

    disc = Yandex_disc(cloud_folder, token)
    _check_token(disc)

    try:
        sync_cycle(disc, local_folder)
    except Exception as exc:
        logging.error(f"Первая синхронизация завершилась с ошибкой: {exc}")
        print("Первый запуск неудачен, подробности в логе.")
        sys.exit(1)

    try:
        while True:
            time.sleep(sync_period)
            try:
                sync_cycle(disc, local_folder)
            except Exception as exc:
                logging.error(f"Ошибка в цикле синхронизации: {exc}")
    except KeyboardInterrupt:
        logging.info("Завершение работы программы")
        print("Синхронизатор остановлен.")


if __name__ == "__main__":
    main()
