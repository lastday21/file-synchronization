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

    def _get_upload_url(self, remote_path, overwrite=False):
        params = {
            "path": f"{self.cloud_folder}/{remote_path}",
            "overwrite": str(overwrite).lower()
        }
        resp = requests.get(f"{self.base_url}/upload", headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()["href"]

    def load(self,local_path, remote_path):
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
        url = f"{self.base_url}?path={self.cloud_folder}/{local_path}"
        response = requests.delete(url, headers=self.headers)
        try:
            response.raise_for_status()
        except requests.RequestException as e:
            self._logger.error(f"Не удалось удалить {local_path}:{e}")
        else:
            self._logger.info(f"Файл {local_path} успешно удален из {self.cloud_folder}/{local_path}")

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