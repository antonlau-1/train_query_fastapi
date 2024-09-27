import pytest
from fastapi.testclient import TestClient
from main import app, ItemModel

client = TestClient(app)

@pytest.fixture
def mock_db(monkeypatch):
    class MockPostgres:
        def __init__(self, *args, **kwargs):
            self.trains = {
                52: {
                    "id": 52,
                    "train_date": "2022-01-01",
                    "platform": 4,
                    "start_point": "start_point",
                    "end_point": "end_point",
                    "arrival_time": "10:00:00",
                    "departure_time": "10:14:33"
                },
                443: {
                    "id": 443,
                    "train_date": "2022-01-02",
                    "platform": 2,
                    "start_point": "start_point2",
                    "end_point": "end_point2",
                    "arrival_time": "22:00:00",
                    "departure_time": "22:40:20"
                }
            }
        
        def execute_query(self, query, params=None, fetch=True):
            print(f"Executing query: {query} with params: {params}")
            
            if "INSERT" in query:
                return [{"id": 1}]
            
            if "DELETE" in query:
                train_id = params.get("id")
                if train_id in self.trains:
                    del self.trains[train_id]
                    return 1
                return 0
            
            if "SELECT" in query:
                if "WHERE id = " in query:
                    train_id = params.get("id")
                    return [self.trains[train_id]] if train_id in self.trains else []
                elif "SELECT id FROM trains WHERE id = " in query:
                    train_id = params.get("id")
                    return [{"id": train_id}] if train_id in self.trains else []
                else:
                    return list(self.trains.values())
            
            if "UPDATE" in query:
                train_id = params.get("id")
                if train_id in self.trains:
                    for key, value in params.items():
                        if key != "id" and value is not None:
                            self.trains[train_id][key] = value
                    return [self.trains[train_id]]
                return []
            
            return []
        
        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("main.PostgresQuery", MockPostgres)

def test_create_train(mock_db):
    new_train = ItemModel(
        train_date="2022-01-01",
        platform=4,
        start_point="start_point",
        end_point="end_point",
        arrival_time="10:00:00",
        departure_time="10:14:33"
    )
    response = client.post("/trains", json=new_train.model_dump())
    assert response.status_code == 200
    assert "message" in response.json()
    assert "train" in response.json()
    assert response.json()["message"] == "Train created successfully"
    assert response.json()["train"]["id"] == 1

def test_get_all_trains(mock_db):
    response = client.get("/trains")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2

def test_get_train_by_id(mock_db):
    response = client.get("/trains/id/52")
    assert response.status_code == 200
    assert response.json()[0]["id"] == 52


def test_get_train_by_id_not_found(mock_db):
    response = client.get("/trains/id/999")
    print(f"Response status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Train not found"}

def test_get_trains_by_platform(mock_db):
    response = client.get("/trains/platform/4")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_get_trains_by_end_point(mock_db):
    response = client.get("/trains/end_point/end_point")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_train(mock_db):
    updated_train = ItemModel(
        train_date="2023-01-01",
        platform=5,
        start_point="new_start",
        end_point="new_end",
        arrival_time="11:00:00",
        departure_time="11:30:00"
    )
    response = client.put("/trains/id/52", json=updated_train.model_dump())
    assert response.status_code == 200
    
    # Verify the update
    response = client.get("/trains/id/52")
    assert response.status_code == 200
    

def test_update_train_not_found(mock_db):
    updated_train = ItemModel(
        train_date="2023-01-01",
        platform=5,
        start_point="new_start",
        end_point="new_end",
        arrival_time="11:00:00",
        departure_time="11:30:00"
    )
    response = client.put("/trains/id/999", json=updated_train.model_dump())
    assert response.status_code == 404
    assert response.json() == {"detail": "Train not found"}

def test_delete_train(mock_db):
    response = client.delete("/trains/id/52")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "deleted_train" in response.json()
    assert "rows_affected" in response.json()
    assert response.json()["message"] == "Train deleted successfully"
    assert response.json()["rows_affected"] == 1


def test_delete_train_not_found(mock_db):
    response = client.delete("/trains/id/9999")
    print(f"Response status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Train not found"}