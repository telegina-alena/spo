from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles

spo_api = FastAPI()

#работа со статик файлами (для корректного отображения картинок и стилей)
spo_api.mount("/img", StaticFiles(directory="./frontend/img"), name="img")
spo_api.mount("/style", StaticFiles(directory="./frontend/style"), name="style")

#отображение основной страницы
@spo_api.get("/")
async def root():
    html_path = "./frontend/html/main.html"
    return FileResponse(html_path)