#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
from typing import List
from fastapi import FastAPI, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, IPvAnyAddress, validator
import uvicorn

from webs.login import User, Token, get_current_active_user, get_access_token
from message import Message
from sdn import SdnApi

app = FastAPI()
app.mount("/static", StaticFiles(directory="webs/static"), name="static")
templates = Jinja2Templates(directory="webs/templates")

if __name__ != '__main__':
    survey = Message(mode='survey', fqdn='archcncm0576.cluster1')
    sdn = SdnApi()

# 设置允许访问的域名
origins = ["*"]  #也可以设置为"*"，即为所有。
# 设置跨域传参
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等。
    allow_headers=["*"],  # 允许跨域的headers，可以用来鉴别来源等作用。
)

# =============================================================================
#       Frontend Handler 
# =============================================================================

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/")
async def read_root():
    return {"nodes": await survey.getNodes(), "vrouters": sdn.get_vrouters()}

# This is for test and can be deleted
@app.get("/items/{id}")
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})

# =============================================================================
#       Backend Handler 
# =============================================================================
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return get_access_token(form_data.username, form_data.password)

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

class HostItem(BaseModel):
    ip: IPvAnyAddress
    fqdn: str

class Hosts(BaseModel):
    names: List[str] = ['all']
    items: List[HostItem]
    class Config:
        schema_extra = {
            "example": {
                "names": ["archcnstcm6907.cluster1", "archcnstcm6908.cluster1", "archcnstcm6909.cluster1"],
                "items": [
                    { "ip": "13.13.13.13", "fqdn": "archcnstcm6907.cluster1"},
                    { "ip": "13.13.13.14", "fqdn": "archcnstcm6908.cluster1"},
                    { "ip": "13.13.13.15", "fqdn": "archcnstcm6909.cluster1"}
                ]
            }
        }

@app.post("/hosts")
async def modify_hosts(hosts: Hosts, current_user: User = Depends(get_current_active_user)):
    cmd = ''
    for item in hosts.items:
        cmd += f"echo {item.ip} {item.fqdn} >> /etc/hosts;"
    replys = await survey.sendSurvey(who=hosts.names, do='cmd', survey=cmd)
    if not replys:
        replys = 'Error: not reply from any of hosts'
    return replys
@app.get("/hosts")
async def read_hosts(current_user: User = Depends(get_current_active_user)):
    cmd = 'cat /etc/hosts'
    replys = await survey.sendSurvey(who=['all'], do='cmd', survey=cmd)
    if not replys:
        replys = 'Error: not reply from any of hosts'
    return replys


if __name__ == '__main__':
    uvicorn.run("web:app", host="0.0.0.0", port=os.environ.get('WEB_PORT', 7787))
