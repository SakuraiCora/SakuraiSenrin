import os
import json
import time
from typing import Dict
from nonebot.adapters.onebot.v11.message import Message, MessageSegment

try:
    with open(file="./Resources/Json/ban.json", mode='r', encoding='utf-8-sig') as f:
        ban_dic:Dict[str,dict[str,int]] = json.load(f)
except:
    raise FileNotFoundError("没有找到ban.json，请检查项目是否完整")
else:
    pass

async def Ban(UserID:str) -> Message:
    """
        用户封禁函数
        规则：第一次60s，第二次+20s
        参数：UserID #用户QQ号
    """
    try:
        level = ban_dic[UserID]["Level"]
    except:
        level = 1
    else:
        level = level +1
    banTime = int(time.time())+40+20*level
    ban_dic[UserID]["Time"] = banTime  #time用于判断用户是否处于封禁阶段（免去sleep的烦恼）
    ban_dic[UserID]["Level"] = level
    with open(file="./Resources/Json/ban.json", mode='w', encoding='utf-8-sig') as f:
        json.dump(ban_dic, f, indent=2,sort_keys=True, ensure_ascii=False)
    return MessageSegment.at(int(UserID))+MessageSegment.text(f"[防滥用警告：Ban]\n防滥用机制触发，{banTime}s后即可恢复")