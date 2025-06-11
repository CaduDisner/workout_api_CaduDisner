### Estrutura do Projeto:
# workout_api/
# ├── app/
# │   ├── main.py
# │   ├── routers/workouts.py
# │   ├── models.py
# │   ├── database.py
# │   └── schemas.py
# ├── Dockerfile
# ├── docker-compose.yml
# ├── requirements.txt
# └── README.md

# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./workouts.db"  # ou use postgres com docker-compose

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# app/models.py
from sqlalchemy import Column, Integer, String
from .database import Base

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    load = Column(Integer)
    reps = Column(Integer)

# app/schemas.py
from pydantic import BaseModel

class WorkoutBase(BaseModel):
    title: str
    load: int
    reps: int

class WorkoutCreate(WorkoutBase):
    pass

class WorkoutUpdate(WorkoutBase):
    pass

class WorkoutOut(WorkoutBase):
    id: int

    class Config:
        orm_mode = True

# app/routers/workouts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/workouts", tags=["Workouts"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.WorkoutOut, status_code=201)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    db_workout = models.Workout(**workout.dict())
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@router.get("/", response_model=list[schemas.WorkoutOut])
def get_workouts(db: Session = Depends(get_db)):
    return db.query(models.Workout).all()

@router.get("/{workout_id}", response_model=schemas.WorkoutOut)
def get_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(models.Workout).get(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@router.put("/{workout_id}", response_model=schemas.WorkoutOut)
def update_workout(workout_id: int, update: schemas.WorkoutUpdate, db: Session = Depends(get_db)):
    workout = db.query(models.Workout).get(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    for key, value in update.dict().items():
        setattr(workout, key, value)
    db.commit()
    db.refresh(workout)
    return workout

@router.delete("/{workout_id}", status_code=204)
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(models.Workout).get(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(workout)
    db.commit()
    return

# app/main.py
from fastapi import FastAPI
from .database import Base, engine
from .routers import workouts

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(workouts.router)

# requirements.txt
fastapi
uvicorn[standard]
sqlalchemy
pydantic

# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# README.md
# Workout API - FastAPI + Docker

## Como rodar localmente:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Com Docker:
```bash
docker-compose up --build
```

Acesse a API em http://localhost:8000/docs
