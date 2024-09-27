from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import os
import logging

app = FastAPI()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': int(os.getenv('POSTGRES_PORT', 5432))
}

class ItemModel(BaseModel):
    train_date: str
    platform: int
    start_point: str
    end_point: str
    arrival_time: str
    departure_time: str

class PostgresQuery:
    def __init__(self, config):
        self.conn = psycopg2.connect(**config)

    def execute_query(self, query, params=None, fetch=True):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            else:
                return cursor.rowcount

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

@app.get("/")
async def root():
    return {"message": "Please use /trains, /trains/id/{id}, /trains/platform/{platform}, or /trains/end_point/{end_point}."}

@app.get("/trains")
async def get_trains():
    try:
        query = PostgresQuery(DB_CONFIG)
        q = "SELECT * FROM trains"
        result = query.execute_query(q)
        query.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": "An error occurred while fetching the trains."})

@app.get("/trains/id/{id}")
async def get_train_by_id(id: int):
    query = None
    try:
        query = PostgresQuery(DB_CONFIG)
        q = "SELECT * FROM trains WHERE id = %(id)s"
        params = {"id": id}

        result = query.execute_query(q, params)
        if not result:
            raise HTTPException(status_code=404, detail="Train not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=str(e), 
            headers={"X-Error": "An error occurred while fetching the train."}
        )
    finally:
        if query:
            query.close()


@app.get("/trains/platform/{platform}")
async def get_train_by_platform(platform: str):
    try:
        query = PostgresQuery(DB_CONFIG)
        q = "SELECT * FROM trains WHERE platform = %(platform)s"
        params = {"platform": platform}
        result = query.execute_query(q, params)
        query.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": "An error occurred while fetching the train."})

@app.get("/trains/end_point/{end_point}")
async def get_train_by_end_point(end_point: str):
    try:
        query = PostgresQuery(DB_CONFIG)
        q = "SELECT * FROM trains WHERE end_point = %(end_point)s"
        params = {"end_point": end_point}
        result = query.execute_query(q, params)
        query.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": "An error occurred while fetching the train."})

@app.post("/trains")
async def create_train(train: ItemModel):
    try:
        query = PostgresQuery(DB_CONFIG)
        q = """
            INSERT INTO trains 
            (train_date, platform, start_point, end_point, arrival_time, departure_time) 
            VALUES (%(train_date)s, %(platform)s, %(start_point)s, %(end_point)s, %(arrival_time)s, %(departure_time)s)
            RETURNING *
        """
        params = train.model_dump()
        result = query.execute_query(q, params)
        query.commit()
        query.close()
        return {"message": "Train created successfully", "train": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": "An error occurred while creating the train."})

@app.put("/trains/id/{id}")
async def update_train(id: int, train: ItemModel):
    try:
        query = PostgresQuery(DB_CONFIG)
        # Check if train exists
        check_q = "SELECT id FROM trains WHERE id = %(id)s"
        check_result = query.execute_query(check_q, {"id": id})
        if not check_result:
            raise HTTPException(status_code=404, detail="Train not found")
        
        q = """
            UPDATE trains 
            SET train_date = %(train_date)s, platform = %(platform)s, start_point = %(start_point)s, 
                end_point = %(end_point)s, arrival_time = %(arrival_time)s, departure_time = %(departure_time)s
            WHERE id = %(id)s
            RETURNING *
        """
        params = {**train.model_dump(), "id": id}
        result = query.execute_query(q, params)
        query.commit()
        query.close()
        return {"message": "Train updated successfully", "train": result[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e), headers={"X-Error": "An error occurred while updating the train."})

@app.delete("/trains/id/{id}")
async def delete_train(id: int):
    query = None
    try:
        query = PostgresQuery(DB_CONFIG)
        param = {"id": id}

        # Check if the train exists
        check_q = "SELECT * FROM trains WHERE id = %(id)s"
        check_result = query.execute_query(check_q, param)
        if not check_result:
            raise HTTPException(status_code=404, detail="Train not found")
        
        # Perform the delete operation
        q = "DELETE FROM trains WHERE id = %(id)s"
        delete_result = query.execute_query(q, param, fetch=False)
        query.commit()

        if delete_result == 0:
            raise HTTPException(status_code=404, detail="Train not found")
        
        return {
            "message": "Train deleted successfully",
            "deleted_train": check_result[0],  # Returning the deleted train's data
            "rows_affected": delete_result     # Number of rows affected
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while deleting the train: {str(e)}"
        )
    finally:
        if query:
            query.close()
