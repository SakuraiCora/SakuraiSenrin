"""
    前体消息构造
"""
import os

from nonebot.adapters.onebot.v11.message import MessageSegment, Message

async def RandomSetuMsg(userID, Rmodle, num, level) -> Message:

    handle_msg = (
    MessageSegment.at(userID)+MessageSegment.text("随机涩图触发\n")
    +MessageSegment.text(f"触发方式：{Rmodle}\n")
    +MessageSegment.text(f"图片分级：{level}\n")
    +MessageSegment.text(f"图片数量：{num}\n")
    +MessageSegment.text("Loading......（约3秒钟）")
    )
    return handle_msg

async def SearchSetuMsg(userID, Smodle, keywords, num) -> Message:
    handle_msg = (
    MessageSegment.at(userID)+MessageSegment.text("定向涩图触发\n")
    +MessageSegment.text(f"触发方式：{Smodle}\n")
    +MessageSegment.text(f"关键词：{keywords}\n")
    +MessageSegment.text(f"图片数量：{num}\n")
    +MessageSegment.text("Loading......（约3秒钟）")
    )
    return handle_msg


def ExceptionBuilder(excMsg:str) -> str:
    workPath = os.getcwd()
    workPath = workPath.replace(workPath[0],workPath[0].lower())
    _ = excMsg.replace('Traceback (most recent call last):\n  ', '').replace(workPath,"")
    return _