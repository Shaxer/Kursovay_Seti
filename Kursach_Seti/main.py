from fastapi import FastAPI
import couchdb
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# fastapi dev main.py
def create_app(db):
    app = FastAPI()

    # Configure CORS
    origins = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
        # Add other origins if needed
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/brigades/get/{brigade_id}")
    def brigades_get(brigade_id):
        # запрос по id
        key = f'brig{brigade_id}'
        if key not in db:
            raise HTTPException(status_code=404, detail="Brigade not found")
        return db[key]


    @app.delete("/brigades/remove/{brigade_id}")
    def brigades_remove(brigade_id):
        if brigade_id not in db:
            raise HTTPException(status_code=404, detail="Brigade not found")
        num = db[brigade_id]['num']
        submissions = []
        for doc in db:
            if doc.startswith('submission') and str(db[doc].get('brigade_num')) == str(num):
                submissions.append(doc)
        for submition in submissions:
            del db[submition]
        del db[brigade_id]

        return JSONResponse(content={"message": f"Brigade {num} deleted successfully"}, status_code=200)


    @app.get("/brigades/all/")
    def brigades_all():
        # запрос всех бригад
        mango = {'selector': {'num': {'$gt': 0}}}
        x = db.find(mango)
        res = []
        for el in x:
             res.append(el)
        return res


    @app.post("/brigades/create")
    async def create_brigade(request: Request):
        data = await request.json()
        brigade_num = data.get('num')
        students = data.get('students', '').split(',')

        if len(str(brigade_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")
        if len(set(str(brigade_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер бригады должен состоять только из цифр")
        if str(brigade_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер бригады не должен начинаться с 0")

        if not brigade_num:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")

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


    @app.post("/labs/submit")
    async def submit_lab(request: Request):
        data = await request.json()
        brigade_num = data.get('num')
        lab_num = data.get('lab_num')
        if len(str(brigade_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер бригады'")
        if len(set(str(brigade_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер бригады должен состоять только из цифр")
        if str(brigade_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер бригады не должен начинаться с 0")

        if len(str(lab_num)) == 0:
            raise HTTPException(status_code=400, detail="Заполните поле 'номер работы'")
        if len(set(str(lab_num)).difference(set("1234567890"))) != 0:
            raise HTTPException(status_code=400, detail="Номер работы должен состоять только из цифр")
        if str(lab_num)[0] == '0':
            raise HTTPException(status_code=400, detail="Номер работы не должен начинаться с 0")

        if f"brig{brigade_num}" not in db:
            raise HTTPException(status_code=400, detail="Такой бригады не существует")

        submission_date = data.get('date')

        if not brigade_num or not lab_num or not submission_date:
            raise HTTPException(status_code=400, detail="Заполнены не все поля")

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


    @app.delete("/labs/submissions/remove/{submition_id}")
    async def delete_lab(submition_id):
        if submition_id not in db:
            raise HTTPException(status_code=404, detail="Сдача не найдена")
        del db[submition_id]
        return JSONResponse(content={"message": f"Сдача успешно удалена"}, status_code=200)


    @app.get("/labs/submissions")
    async def get_all_submissions():
        submissions = [db[doc] for doc in db if doc.startswith('submission')]
        return JSONResponse(content=submissions, status_code=200)

    return app


if __name__ == "__main__":
    local = 'http://localhost:5984'
    docker = 'http://couchdb:5984'
    couch = couchdb.Server(docker)
    couch.resource.credentials = ('admin', 'admin')
    try:
        db = couch.create('test1')
    except Exception as e:
        db = couch['test1']
    app = create_app(db)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
