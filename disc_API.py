"""
Модуль disc_API

Содержит класс Yandex_disc для работы с API Яндекс.Диска:
- формирование URL для загрузки файлов,
- загрузка новых файлов,
- перезапись существующих,
- удаление и
- получение информации о содержимом папки в облаке.
"""

import logging
import requests

class Yandex_disc():
    """
    Обёртка над HTTP-API Яндекс.Диска для синхронизации файлов.

    :param str cloud_folder: имя папки на Яндекс.Диске, куда будут загружаться файлы
    :param str token: OAuth-токен для доступа к API Яндекс.Диска
    """

    def __init__(self,cloud_folder, token):
        self.cloud_folder = cloud_folder
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers ={
            "Authorization": f"OAuth {self.token}"
        }
        self._logger = logging.getLogger(__name__)

    def _get_upload_url(self, remote_path, overwrite=False):
        """
       Запрашивает у API URL для загрузки файла.

       :param str remote_path: относительный путь (имя) файла внутри cloud_folder
       :param bool overwrite: если True — перезаписать файл, если False — только загрузить новый
       :return: URL, по которому нужно выполнить HTTP PUT для загрузки содержимого
       :rtype: str
       :raises requests.HTTPError: при не-200 ответе от сервера
       """

        params = {
            "path": f"{self.cloud_folder}/{remote_path}",
            "overwrite": str(overwrite).lower()
        }
        resp = requests.get(f"{self.base_url}/upload", headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()["href"]

    def load(self,local_path, remote_path):
        """
        Загружает файл в облако, если его там ещё нет.

        Читает весь файл из local_path и отправляет по URL, полученному из _get_upload_url.

        :param str local_path: путь к файлу на локальной машине
        :param str remote_path: имя (или относительный путь) файла в облачной папке
        :return: None
        :raises OSError: при ошибке чтения файла
        """

        href = self._get_upload_url(remote_path, overwrite=False)
        with open(local_path, "rb") as f:
            data = f.read()
        response = requests.put(href, data=data, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось загрузить {local_path}:{e}")
        else:
            self._logger.info(f"Файл {local_path} успешно загружен в {self.cloud_folder}/{remote_path}")

    def reload(self,local_path, remote_path):
        """
       Перезаписывает существующий в облаке файл.

       Использует overwrite=True при запросе URL, чтобы заменить старую версию.

       :param str local_path: путь к файлу на локальной машине
       :param str remote_path: имя (или относительный путь) файла в облачной папке
       :return: None
       :raises OSError: при ошибке чтения файла
       """
        href = self._get_upload_url(remote_path, overwrite=True)
        with open(local_path, "rb") as f:
            data = f.read()
        response = requests.put(href, data=data, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось перезаписать {remote_path}:{e}")
        else:
            self._logger.info(f"Файл {local_path} успешно перезаписан в {self.cloud_folder}/{remote_path}")

    def delete(self, local_path):
        """
        Удаляет файл из облачного хранилища.

        :param str remote_path: имя (или относительный путь) файла в облачной папке
        :return: None
        :raises requests.RequestException: при неудачном HTTP-запросе
        """

        url = f"{self.base_url}?path={self.cloud_folder}/{local_path}"
        response = requests.delete(url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось удалить {local_path}:{e}")
        else:
            self._logger.info(f"Файл {local_path} успешно удален из {self.cloud_folder}/{local_path}")

    def get_info(self):
        """
        Получает метаданные содержимого папки в облаке.

        Делает запрос GET к ресурсу папки и возвращает распарсенный JSON.

        :return: словарь с данными API (ключи `_embedded` → `items` и прочие)
        :rtype: dict
        :raises requests.RequestException: при ошибке HTTP-запроса — возвращает пустой dict
        """

        url = f"{self.base_url}?path={self.cloud_folder}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            count = len(data.get("_embedded", {}).get("items", []))
            self._logger.info(f"В папке {self.cloud_folder} найдено {count} элементов")
            return data
        except requests.RequestException as e:
            self._logger.error("Не удалось получить данные: %s", e)
            return {}