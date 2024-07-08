from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from . import admin
from . import superadmin

app = FastAPI()

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="templates")

# Подключаем папку с статическими файлами (изображениями)
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Регистрация роутера admin
app.include_router(admin.router, prefix="/admin", tags=["admin"])


# Регистрация роутера superadmin
app.include_router(superadmin.router, prefix="/superadmin", tags=["superadmin"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
