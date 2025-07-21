import logging
import requests

class Yandex_disc():
    def __init__(self,cloud_folder, token):
        self.cloud_folder = cloud_folder
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers ={
            "Authorization": f"OAuth {self.token}"
        }
        self._logger = logging.getLogger(__name__)

    def _get_upload_url(self, file_name, overwrite=False):
        params = {
            "path": f"{self.cloud_folder}/{file_name}",
            "overwrite": str(overwrite).lower()
        }
        resp = requests.get(f"{self.base_url}/upload", headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()["href"]

    def load(self,file_name):
        href = self._get_upload_url(file_name, overwrite=False)
        with open(file_name, "rb") as f:
            data = f.read()
        response = requests.put(href, data=data, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось загрузить {file_name}:{e}")
        else:
            self._logger.info(f"Файл {file_name} успешно загружен в {self.cloud_folder}")

    def reload(self,file_name):
        href = self._get_upload_url(file_name, overwrite=True)
        with open(file_name, "rb") as f:
            data = f.read()
        response = requests.put(href, data=data, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось перезаписать {file_name}:{e}")
        else:
            self._logger.info(f"Файл {file_name} успешно перезаписан в {self.cloud_folder}")

    def delete(self, file_name):
        url = f"{self.base_url}?path={self.cloud_folder}/{file_name}"
        response = requests.delete(url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось удалить {file_name}:{e}")
        else:
            self._logger.info(f"Файл {file_name} успешно удален из {self.cloud_folder}")

    def get_info(self):
        url = f"{self.base_url}?path={self.cloud_folder}"
        response = requests.get(url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось получить данные {self.cloud_folder}:{e}")
            return {}
        else:
            data = response.json()
            count = len(data.get("items", []))
            self._logger.info(f"В папке {self.cloud_folder} найдено {count} элементов")
            return  data