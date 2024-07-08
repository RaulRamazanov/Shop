from fastapi import FastAPI

# Create an instance of FastAPI
app = FastAPI()

# Example: Register routers, templates, static files, etc.
# Replace `admin` and `superadmin` with your actual router imports

# Import routers
from . import admin
from . import superadmin

# Example: Mount static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Example: Templates
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

# Example: Register routers
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(superadmin.router, prefix="/superadmin", tags=["superadmin"])