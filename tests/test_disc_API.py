"""
Набор юнит-тестов для класса Yandex_disc, проверяющий методы работы с API:
- _get_upload_url
- load
- reload
- delete
- get_info
"""


import logging
import pytest
import requests
from unittest.mock import patch, Mock

from disc_API import Yandex_disc

@pytest.fixture
def client():
    return Yandex_disc('backup', 'token')

@patch('disc_API.requests.get')
def test_get_upload_url_success(mock_get, client):
    mock_get.return_value = Mock(status_code=200, json=lambda: {'href': 'http://upload'})
    url = client._get_upload_url('file.txt', overwrite=True)
    assert url == 'http://upload'

@patch('disc_API.requests.get')
def test_get_upload_url_http_error(mock_get, client):
    resp = Mock()
    resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mock_get.return_value = resp
    with pytest.raises(requests.HTTPError):
        client._get_upload_url('file.txt')

@patch('disc_API.requests.put')
@patch.object(Yandex_disc, '_get_upload_url', return_value='http://upload')
def test_load_success(mock_url, mock_put, client, tmp_path, caplog):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"data")
    resp = Mock()
    resp.raise_for_status.return_value = None
    mock_put.return_value = resp
    caplog.set_level(logging.INFO)
    client.load(str(file_path), 'a.txt')
    assert any("успешно загружен" in rec.message for rec in caplog.records)

@patch('disc_API.requests.put')
@patch.object(Yandex_disc, '_get_upload_url', return_value='http://upload')
def test_load_failure(mock_url, mock_put, client, tmp_path, caplog):
    file_path = tmp_path / "b.txt"
    file_path.write_bytes(b"data")
    resp = Mock()
    resp.raise_for_status.side_effect = requests.RequestException("fail")
    mock_put.return_value = resp
    caplog.set_level(logging.ERROR)
    client.load(str(file_path), 'b.txt')
    assert any("Не удалось загрузить" in rec.message for rec in caplog.records)

@patch('disc_API.requests.put')
@patch.object(Yandex_disc, '_get_upload_url', return_value='http://upload')
def test_reload_success(mock_url, mock_put, client, tmp_path, caplog):
    file_path = tmp_path / "c.txt"
    file_path.write_bytes(b"data")
    resp = Mock()
    resp.raise_for_status.return_value = None
    mock_put.return_value = resp
    caplog.set_level(logging.INFO)
    client.reload(str(file_path), 'c.txt')
    assert any("успешно перезаписан" in rec.message for rec in caplog.records)

@patch('disc_API.requests.put')
@patch.object(Yandex_disc, '_get_upload_url', return_value='http://upload')
def test_reload_failure(mock_url, mock_put, client, tmp_path, caplog):
    file_path = tmp_path / "d.txt"
    file_path.write_bytes(b"data")
    resp = Mock()
    resp.raise_for_status.side_effect = requests.RequestException("fail")
    mock_put.return_value = resp
    caplog.set_level(logging.ERROR)
    client.reload(str(file_path), 'd.txt')
    assert any("Не удалось перезаписать" in rec.message for rec in caplog.records)

@patch('disc_API.requests.delete')
def test_delete_success(mock_delete, client, caplog):
    resp = Mock()
    resp.raise_for_status.return_value = None
    mock_delete.return_value = resp
    caplog.set_level(logging.INFO)
    client.delete('e.txt')
    assert any("успешно удален" in rec.message for rec in caplog.records)

@patch('disc_API.requests.delete')
def test_delete_failure(mock_delete, client, caplog):
    resp = Mock()
    resp.raise_for_status.side_effect = requests.RequestException("fail")
    mock_delete.return_value = resp
    caplog.set_level(logging.ERROR)
    client.delete('f.txt')
    assert any("Не удалось удалить" in rec.message for rec in caplog.records)

@patch('disc_API.requests.get')
def test_get_info_success(mock_get, client, caplog):
    data = {'_embedded': {'items': [1, 2, 3]}}
    resp = Mock(status_code=200, json=lambda: data)
    resp.raise_for_status.return_value = None
    mock_get.return_value = resp
    caplog.set_level(logging.INFO)
    result = client.get_info()
    assert result == data
    assert any("найдено 3 элементов" in rec.message for rec in caplog.records)

@patch('disc_API.requests.get')
def test_get_info_failure(mock_get, client, caplog):
    resp = Mock()
    resp.raise_for_status.side_effect = requests.RequestException("fail")
    mock_get.return_value = resp
    caplog.set_level(logging.ERROR)
    result = client.get_info()
    assert result == {}
    assert any("Не удалось получить данные" in rec.message for rec in caplog.records)
