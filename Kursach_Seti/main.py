from fastapi import FastAPI
import couchdb
from pydantic import BaseModel, validator
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Модель Pydantic для создания бригады
class BrigadeCreate(BaseModel):
    num: int  # Номер бригады
    students: str  # Список студентов (в виде строки, разделенной запятыми)

    @validator('num')
    def validate_num(cls, v):
        # Проверка номера бригады: он должен быть положительным числом
        if v <= 0:
            raise ValueError("Номер бригады должен быть положительным числом")
        return v

# Модель Pydantic для сдачи лабораторной работы
class LabSubmit(BaseModel):
    num: int  # Номер бригады
    lab_num: int  # Номер лабораторной работы
    date: str  # Дата сдачи в формате DD.MM.YYYY

    @validator('date')
    def validate_date(cls, v):
        # Проверка даты: проверка корректности формата
        try:
            datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Неверный формат даты, должен быть таким DD.MM.YYYY")
        return v

# Функция для создания FastAPI приложения
def create_app(db):
    app = FastAPI()

    # Настройка CORS (Cross-Origin Resource Sharing)
    origins = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"  # Разрешить все источники
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Разрешить все HTTP-методы
        allow_headers=["*"],  # Разрешить все заголовки
    )

    # Эндпоинт для получения информации о бригаде по её ID
    @app.get("/brigades/get/{brigade_id}")
    def brigades_get(brigade_id):
        key = f'brig{brigade_id}'
        if key not in db:
            raise HTTPException(status_code=404, detail="Brigade not found")
        return db[key]

    # Эндпоинт для удаления бригады по её ID
    @app.delete("/brigades/remove/{brigade_id}")
    def brigades_remove(brigade_id):
        if brigade_id not in db:
            raise HTTPException(status_code=404, detail="Brigade not found")
        num = db[brigade_id]['num']
        submissions = []
        # Поиск всех связанных сдач лабораторных работ
        for doc in db:
            if doc.startswith('submission') and str(db[doc].get('brigade_num')) == str(num):
                submissions.append(doc)
        # Удаление всех связанных сдач
        for submition in submissions:
            del db[submition]
        # Удаление бригады
        del db[brigade_id]

        return JSONResponse(content={"message": f"Brigade {num} deleted successfully"}, status_code=200)

    # Эндпоинт для получения списка всех бригад
    @app.get("/brigades/all/")
    def brigades_all():
        mango = {'selector': {'num': {'$gt': 0}}}  # Запрос для поиска всех бригад
        x = db.find(mango)
        res = []
        for el in x:
             res.append(el)
        return res

    # Эндпоинт для создания новой бригады
    @app.post("/brigades/create")
    async def create_brigade(brigade: BrigadeCreate):
        brigade_num = brigade.num
        students = brigade.students.split(',')

        # Проверка номера бригады
        if len(str(brigade_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")
        if len(set(str(brigade_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер бригады должен состоять только из цифр")
        if str(brigade_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер бригады не должен начинаться с 0")

        if not brigade_num:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")

        # Проверка списка студентов
        if len(set(set("1234567890")).difference(''.join(students))) < 10:
            raise HTTPException(status_code=400, detail="В ФИО не бывает цифр")

        if not students or not all(students):
            raise HTTPException(status_code=400, detail="Заполните ФИО студентов")

        brigade_id = f'brig{brigade_num}'

        if brigade_id in db:
            raise HTTPException(status_code=409, detail=f"Бригада {brigade_num} уже существует")
        brigade_data = {
            'num': brigade_num,
            'students': students
        }

        db[brigade_id] = brigade_data

        return JSONResponse(content={"brigade_id": brigade_id, "brigade_data": brigade_data}, status_code=200)

    # Эндпоинт для сдачи лабораторной работы
    @app.post("/labs/submit")
    async def submit_lab(lab: LabSubmit):
        brigade_num = lab.num
        lab_num = lab.lab_num
        submission_date = lab.date
        # Проверка номера бригады
        if len(str(brigade_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")
        if len(set(str(brigade_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер бригады должен состоять только из цифр")
        if str(brigade_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер бригады не должен начинаться с 0")

        # Проверка номера лабораторной работы
        if len(str(lab_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер работы'")
        if len(set(str(lab_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер работы должен состоять только из цифр")
        if str(lab_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер работы не должен начинаться с 0")

        if f"brig{brigade_num}" not in db:
            raise HTTPException(status_code=400, detail="Такой бригады не существует")
        
        if not brigade_num or not lab_num or not submission_date:
            raise HTTPException(status_code=400, detail="Заполнены не все поля")

        # Проверка даты
        try:
            submission_date = datetime.strptime(submission_date, '%d.%m.%Y').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат даты, должен быть таким DD.MM.YYYY")

        submission_id = f"submission_{brigade_num}_{lab_num}_{submission_date.strftime('%d.%m.%Y')}"

        if submission_id in db:
            raise HTTPException(status_code=400, detail="Такая сдача уже существует")
        submission_data = {
            'brigade_num': brigade_num,
            'lab_num': lab_num,
            'submission_date': submission_date.strftime('%d.%m.%Y')
        }

        db[submission_id] = submission_data

        return JSONResponse(content={"submission_id": submission_id, "submission_data": submission_data}, status_code=200)

    # Эндпоинт для удаления сдачи лабораторной работы по её ID
    @app.delete("/labs/submissions/remove/{submition_id}")
    async def delete_lab(submition_id):
        if submition_id not in db:
            raise HTTPException(status_code=404, detail="Сдача не найдена")
        del db[submition_id]
        return JSONResponse(content={"message": f"Сдача успешно удалена"}, status_code=200)

    # Эндпоинт для получения списка всех сдач лабораторных работ
    @app.get("/labs/submissions")
    async def get_all_submissions():
        submissions = [db[doc] for doc in db if doc.startswith('submission')]
        return JSONResponse(content=submissions, status_code=200)

    return app

# Запуск приложения
if __name__ == "__main__":
    local = 'http://localhost:5984'
    docker = 'http://couchdb:5984'
    couch = couchdb.Server(docker)
    couch.resource.credentials = ('admin', 'admin')
    try:
        db = couch.create('test1')  # Создание базы данных, если она не существует
    except Exception as e:
        db = couch['test1']  # Использование существующей базы данных
    app = create_app(db)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Запуск сервера FastAPI