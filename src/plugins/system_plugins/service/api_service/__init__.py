import nonebot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot

app: FastAPI = nonebot.get_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/service/get_user_name/{user_id}")
async def get_user_name(user_id: int):
    if (bot := get_bot()) and isinstance(bot, Bot):
        username = (await bot.get_stranger_info(user_id=user_id)).get("nick")
    else:
        username = None
    return {"user_id": user_id, "username": username}


@app.get("/api/service/get_group_name/{group_id}")
async def get_group_name(group_id: int):
    if (bot := get_bot()) and isinstance(bot, Bot):
        group_name = (await bot.get_group_info(group_id=group_id)).get("group_name")
    else:
        group_name = None
    return {"group_id": group_id, "group_name": group_name}
