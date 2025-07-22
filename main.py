import configparser
import logging
from sync import sync_cycle
import os
from logger import setup_logger
from disc_API import  Yandex_disc
import time



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
        print(f"Первый запуск неудачен: {e}")
        logging.error(f"Первый запуск неудачный: {e}")
        exit(1)

    while True:
        time.sleep(sync_period)
        try:
            sync_cycle(disc, local_path)
        except Exception as e:
            logging.error(f"Ошибка в цикле: {e}")

if __name__ == "__main__":
    print("Запуск синхронизатора")
    main()





