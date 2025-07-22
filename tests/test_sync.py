"""
Набор юнит-тестов для модуля sync.py, проверяющий функции:
- get_local_files: сбор локальных файлов с учётом вложенных каталогов
- sync_cycle: корректная загрузка новых файлов, удаление удалённых в облаке,
  обновление при более поздней локальной версии и отсутствие действий, если
  облачная версия новее.

"""

import os
from datetime import datetime, timedelta
from sync import get_local_files, sync_cycle

class DummyClient:
    def __init__(self, cloud_folder='backup', items=None):
        self.cloud_folder = cloud_folder
        self.loaded = []
        self.reloaded = []
        self.deleted = []
        self.items = items or []

    def get_info(self):
        return {'_embedded': {'items': self.items}}

    def load(self, local, remote):
        self.loaded.append((local, remote))

    def reload(self, local, remote):
        self.reloaded.append((local, remote))

    def delete(self, remote):
        self.deleted.append(remote)

def test_get_local_files_nested(tmp_path):
    (tmp_path / "dir").mkdir()
    f1 = tmp_path / "file1.txt"; f1.write_text("a")
    f2 = tmp_path / "dir" / "file2.txt"; f2.write_text("b")
    res = get_local_files(str(tmp_path), str(tmp_path))
    assert set(res) == {"file1.txt", os.path.join("dir", "file2.txt")}

def test_sync_cycle_only_local(tmp_path):
    f = tmp_path / "new.txt"; f.write_text("data")
    client = DummyClient()
    sync_cycle(client, str(tmp_path))
    assert any(str(f) == local for local, _ in client.loaded)
    assert client.deleted == []
    assert client.reloaded == []

def test_sync_cycle_only_cloud(tmp_path):
    client = DummyClient(items=[
        {'path': 'disk:/backup/old.txt', 'modified': '2025-07-01T00:00:00+00:00'}
    ])
    sync_cycle(client, str(tmp_path))
    assert client.deleted == ['old.txt']
    assert client.loaded == []
    assert client.reloaded == []

def test_sync_cycle_update_newer(tmp_path):
    f = tmp_path / "upd.txt"; f.write_text("v2")
    old = datetime.now() - timedelta(days=1)
    iso = old.isoformat() + "+00:00"
    client = DummyClient(items=[
        {'path': 'disk:/backup/upd.txt', 'modified': iso}
    ])
    os.utime(f, None)
    sync_cycle(client, str(tmp_path))
    assert any(str(f) == local for local, _ in client.reloaded)

def test_sync_cycle_no_action_if_older(tmp_path):
    f = tmp_path / "same.txt"; f.write_text("v1")
    future = datetime.now() + timedelta(days=1)
    iso = future.isoformat() + "+00:00"
    client = DummyClient(items=[
        {'path': 'disk:/backup/same.txt', 'modified': iso}
    ])
    os.utime(f, None)
    sync_cycle(client, str(tmp_path))
    assert client.loaded == []
    assert client.deleted == []
    assert client.reloaded == []
