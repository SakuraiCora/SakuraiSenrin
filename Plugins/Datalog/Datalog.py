"""
    Datalog包含的功能：
    1.重置模块（自动 手动）
    2.吹氵记录（写入 查询）
"""
import json
import datetime
import os

from Utils.ImageUtils import get_water_card
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import GroupIncreaseNoticeEvent, GroupMessageEvent, MessageEvent

LogPath = os.path.join(os.getcwd(), 'Resources', 'Json', 'datalog.json')

async def get_water_list(memdic, groupID: int, bot) -> Message:

    """
    :说明:

        获取氵怪排行榜并返回为MessageSegment

    :参数:

        memdic, groupID:int

    """

    member_info:list[tuple[int,str,int]] = []
    linedic = memdic[str(groupID)]
    findic = reversed(sorted(linedic.items(), key=lambda kv: (kv[1], kv[0])))
    a = 0
    for _elem in findic:
        QQ = _elem[0]
        waterTimes = _elem[1]
        try:    #解决群员不存在的问题
            _ = await bot.get_group_member_info(group_id=groupID,user_id=QQ)    
        except:
            continue
        else:
            user_name = _['nickname']
            member_info.append((QQ, user_name, waterTimes))
            a += 1
            if a == 10:
                break
    _msg = await get_water_card(member_info)
    if isinstance(_msg, Message):
        return _msg
    else:
        return Message("[未知错误：Unknown]\n可恶，未知错误！！！")


async def start(LogPath) -> None:

    """
    :说明:

        重置吹氵记录

    :参数:

        LogPath
    """

    memdic = {
        "StartTime": str(datetime.datetime.now())
    }
    with open(LogPath, 'w', encoding="utf-8") as f:
        json.dump(memdic, f, indent=2, sort_keys=True, ensure_ascii=False)


async def water_get(args, event: MessageEvent, bot:Bot) -> Message:

    """
    :说明:

        手动查询吹氵记录和排行榜

    :参数:

        args
    """

    with open(LogPath, 'r+', encoding='utf-8') as f:
        memdic = json.load(f)
        try:
            StartTime: str = memdic['StartTime']
        except:
            StartTime: str = str(datetime.datetime.now())
            memdic['StartTime'] = StartTime
            json.dump(memdic, f, indent=2, sort_keys=True, ensure_ascii=False)
            memdic = json.load(f)


    if isinstance(event, GroupMessageEvent):

        if args == 'list':  # 排行榜查询
            msg = await get_water_list(memdic=memdic, groupID=event.group_id, bot=bot)
            if isinstance(msg, Message):
                return msg
            else:
                return Message("[未知错误：Unknown]\n可恶，未知错误！！！")
        elif args:  # 个人记录查询
            try:
                num = memdic[str(event.group_id)][str(args)]
            except:
                num = 0
            EndTime = datetime.datetime.now()
            return_msg = (
                MessageSegment.text("好耶！那就让我来康康宁有多氵\n")
                +MessageSegment.text("查询对象：")+MessageSegment.at(args)+MessageSegment.text("\n")
                +MessageSegment.text(f"吹氵次数：{num}\n")
                +MessageSegment.text(f"起始时间：{StartTime}\n")
                +MessageSegment.text(f"终止时间：{EndTime}"))
            return return_msg
        else:
            return Message("[参数错误：args]\n完了完了参数炸了！！！")  # 异常处理
    else:
        return Message("[未知错误：Unknown]\n请您高抬贵脚移步至群聊中查询可否？")


async def add_new_menber(memdic, event: GroupIncreaseNoticeEvent) -> None:

    """
    :说明:

        自动新增成员条例

    :参数:

        memdic
    """
    try:
        memdic[str(event.group_id)][str(event.user_id)] = 0
    except: #not found group
        memdic[str(event.group_id)] = {}


async def add_number_of_water(memdic, bot: Bot, event: GroupMessageEvent) -> None:

    """
    :说明:

        更新成员吹氵记录

    :参数:

        memdic
    """

    try:
        water_number = memdic[str(event.group_id)][str(event.user_id)]  # not found user
    except:
        try:
            memdic[str(event.group_id)][str(event.user_id)] = 1  # not found group
        except:
            memdic[str(event.group_id)] = {}  # add group
            memdic[str(event.group_id)][str(event.user_id)] = 1  # add user
    else:
        water_number = water_number + 1
        memdic[str(event.group_id)][str(event.user_id)] = water_number
    with open(LogPath, 'w', encoding="utf-8") as f:
        json.dump(memdic, f, indent=2, sort_keys=True, ensure_ascii=False)
