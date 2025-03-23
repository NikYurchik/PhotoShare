from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.extra.update({"user": {"is_authenticated": False}})
app.extra.update({"errors": []})
app.extra.update({"history": []})
app.extra.update({"qualifiers": {}})
app.extra.update({"qualifiers_ts": 0})


app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory='templates')


user_agent_ban_list = [r"Python-urllib"]
# user_agent_ban_list = [r"Gecko", r"Python-urllib"]

