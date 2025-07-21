import configparser
import os
from logger import setup_logger

config = configparser.ConfigParser()
config.read('config.ini')

local_path = config['SETTINGS']['local_folder']
if not os.path.exists(local_path):
    print(f"Ошибка: папка '{local_path}' не существует.")
    exit()

setup_logger(local_path)

