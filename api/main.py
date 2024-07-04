from fastapi import FastAPI, HTTPException, Request, status, Depends, Form, Cookie
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlmodel import create_engine, select, Session
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime 
import bcrypt
import uuid
import os


app = FastAPI()

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="templates")


# Подключаем папку с статическими файлами (изображениями)
app.mount("/static", StaticFiles(directory="./static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Передаем request в шаблон для дальнейшего использования
    return templates.TemplateResponse("index.html", {"request": request})
