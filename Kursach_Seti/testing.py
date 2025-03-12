import pytest
from fastapi.testclient import TestClient
from main import create_app

# Мок-класс для имитации CouchDB
class MockCouchDB:
    def __init__(self):
        self.data = {}  # Словарь для хранения данных

    def __contains__(self, key):
        return key in self.data  # Проверка наличия ключа в данных

    def __getitem__(self, key):
        return self.data[key]  # Получение значения по ключу

    def __setitem__(self, key, value):
        self.data[key] = value  # Установка значения по ключу

    def __delitem__(self, key):
        del self.data[key]  # Удаление значения по ключу

    def find(self, query):
        # Имитация поиска в базе данных
        if query == {'selector': {'num': {'$gt': 0}}}:
            return [v for k, v in self.data.items() if k.startswith('brig')]
        elif query == {'selector': {'num': 1}}:
            return [v for k, v in self.data.items() if k.startswith('brig') and v['num'] == 1]
        return []

    def __iter__(self):
        return iter(self.data)  # Итерация по данным

# Создание мок-базы данных
db = MockCouchDB()

# Создание тестового приложения
app = create_app(db)

# Создание тестового клиента
client = TestClient(app)

# Тест для получения информации о бригаде
def test_brigades_get():
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    response = client.get("/brigades/get/1")
    assert response.status_code == 200
    assert response.json() == {'num': 1, 'students': ['John Doe', 'Jane Doe']}

# Тест для случая, когда бригада не найдена
def test_brigades_get_not_found():
    response = client.get("/brigades/get/999")
    assert response.status_code == 404

# Тест для удаления бригады
def test_brigades_remove():
    # Добавление мок-бригады и связанных сдач
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    response = client.delete("/brigades/remove/brig1")
    assert response.status_code == 200
    assert response.json() == {"message": "Brigade 1 deleted successfully"}
    assert 'brig1' not in db
    assert 'submission_1_1_01.01.2023' not in db

# Тест для случая, когда бригада для удаления не найдена
def test_brigades_remove_not_found():
    response = client.delete("/brigades/remove/brig999")
    assert response.status_code == 404

# Тест для получения списка всех бригад
def test_brigades_all():
    # Добавление мок-бригад
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    db['brig2'] = {'num': 2, 'students': ['Alice', 'Bob']}
    response = client.get("/brigades/all/")
    assert response.status_code == 200
    assert response.json() == [{'num': 1, 'students': ['John Doe', 'Jane Doe']}, {'num': 2, 'students': ['Alice', 'Bob']}]

# Тест для создания новой бригады
def test_create_brigade():
    response = client.post("/brigades/create", json={"num": 3, "students": "Charlie,Dave"})
    assert response.status_code == 200
    assert response.json() == {"brigade_id": "brig3", "brigade_data": {"num": 3, "students": ["Charlie", "Dave"]}}
    assert 'brig3' in db

# Тест для случая, когда номер бригады невалиден
def test_create_brigade_invalid_num():
    response = client.post("/brigades/create", json={"num": "abc", "students": "Charlie,Dave"})
    assert response.status_code == 400

# Тест для сдачи лабораторной работы
def test_submit_lab():
    # Добавление мок-бригады
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    response = client.post("/labs/submit", json={"num": 1, "lab_num": 1, "date": "01.01.2023"})
    assert response.status_code == 200
    assert response.json() == {"submission_id": "submission_1_1_01.01.2023", "submission_data": {"brigade_num": 1, "lab_num": 1, "submission_date": "01.01.2023"}}
    assert 'submission_1_1_01.01.2023' in db

# Тест для случая, когда дата сдачи невалидна
def test_submit_lab_invalid_date():
    response = client.post("/labs/submit", json={"num": 1, "lab_num": 1, "date": "01-01-2023"})
    assert response.status_code == 400

# Тест для удаления сдачи лабораторной работы
def test_delete_lab():
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    response = client.delete("/labs/submissions/remove/submission_1_1_01.01.2023")
    assert response.status_code == 200
    assert response.json() == {"message": "Сдача успешно удалена"}
    assert 'submission_1_1_01.01.2023' not in db

# Тест для случая, когда сдача для удаления не найдена
def test_delete_lab_not_found():
    response = client.delete("/labs/submissions/remove/submission_999_999_01.01.2023")
    assert response.status_code == 404

# Тест для получения списка всех сдач лабораторных работ
def test_get_all_submissions():
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    db['submission_2_2_02.02.2023'] = {'brigade_num': 2, 'lab_num': 2, 'submission_date': '02.02.2023'}
    response = client.get("/labs/submissions")
    assert response.status_code == 200
    assert response.json() == [{'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}, {'brigade_num': 2, 'lab_num': 2, 'submission_date': '02.02.2023'}]