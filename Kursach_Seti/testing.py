import pytest
import pytest
from fastapi.testclient import TestClient
from main import create_app

# Mocking CouchDB
class MockCouchDB:
    def __init__(self):
        self.data = {}

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def find(self, query):
        if query == {'selector': {'num': {'$gt': 0}}}:
            return [v for k, v in self.data.items() if k.startswith('brig')]
        elif query == {'selector': {'num': 1}}:
            return [v for k, v in self.data.items() if k.startswith('brig') and v['num'] == 1]
        return []

    def __iter__(self):
        return iter(self.data)

db = MockCouchDB()

app = create_app(db)

client = TestClient(app)

def test_brigades_get():
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    response = client.get("/brigades/get/1")
    assert response.status_code == 200
    assert response.json() == {'num': 1, 'students': ['John Doe', 'Jane Doe']}

def test_brigades_get_not_found():
    response = client.get("/brigades/get/999")
    assert response.status_code == 404


def test_brigades_remove():
    # Add a mock brigade and submissions
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    response = client.delete("/brigades/remove/brig1")
    assert response.status_code == 200
    assert response.json() == {"message": "Brigade 1 deleted successfully"}
    assert 'brig1' not in db
    assert 'submission_1_1_01.01.2023' not in db

def test_brigades_remove_not_found():
    response = client.delete("/brigades/remove/brig999")
    assert response.status_code == 404

def test_brigades_all():
    # Add mock brigades
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    db['brig2'] = {'num': 2, 'students': ['Alice', 'Bob']}
    response = client.get("/brigades/all/")
    assert response.status_code == 200
    assert response.json() == [{'num': 1, 'students': ['John Doe', 'Jane Doe']}, {'num': 2, 'students': ['Alice', 'Bob']}]

def test_create_brigade():
    response = client.post("/brigades/create", json={"num": 3, "students": "Charlie,Dave"})
    assert response.status_code == 200
    assert response.json() == {"brigade_id": "brig3", "brigade_data": {"num": 3, "students": ["Charlie", "Dave"]}}
    assert 'brig3' in db

def test_create_brigade_invalid_num():
    response = client.post("/brigades/create", json={"num": "abc", "students": "Charlie,Dave"})
    assert response.status_code == 400

def test_submit_lab():
    # Add a mock brigade
    db['brig1'] = {'num': 1, 'students': ['John Doe', 'Jane Doe']}
    response = client.post("/labs/submit", json={"num": 1, "lab_num": 1, "date": "01.01.2023"})
    assert response.status_code == 200
    assert response.json() == {"submission_id": "submission_1_1_01.01.2023", "submission_data": {"brigade_num": 1, "lab_num": 1, "submission_date": "01.01.2023"}}
    assert 'submission_1_1_01.01.2023' in db

def test_submit_lab_invalid_date():
    response = client.post("/labs/submit", json={"num": 1, "lab_num": 1, "date": "01-01-2023"})
    assert response.status_code == 400

def test_delete_lab():
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    response = client.delete("/labs/submissions/remove/submission_1_1_01.01.2023")
    assert response.status_code == 200
    assert response.json() == {"message": "Сдача успешно удалена"}
    assert 'submission_1_1_01.01.2023' not in db

def test_delete_lab_not_found():
    response = client.delete("/labs/submissions/remove/submission_999_999_01.01.2023")
    assert response.status_code == 404

def test_get_all_submissions():
    db['submission_1_1_01.01.2023'] = {'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}
    db['submission_2_2_02.02.2023'] = {'brigade_num': 2, 'lab_num': 2, 'submission_date': '02.02.2023'}
    response = client.get("/labs/submissions")
    assert response.status_code == 200
    assert response.json() == [{'brigade_num': 1, 'lab_num': 1, 'submission_date': '01.01.2023'}, {'brigade_num': 2, 'lab_num': 2, 'submission_date': '02.02.2023'}]
