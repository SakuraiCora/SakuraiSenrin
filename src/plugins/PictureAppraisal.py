"""
    PictureAppraisal包含的功能：
    1.初步鉴定消息是否为图片
    2.初步筛查表情包与图片
    3.调用BaiduAPI进行鉴定，返回结果
    4.发现违规立即上报
    5.每30天一次重获token
    6.合规的图片存入库中，不再上报（json/dict写针不戳）
    {
        file:value,
        file:value,
        file:value
    }
"""
import json
import os
from ...config import baidu_client_id, baidu_client_secret, post_id
from ...costrule import check_white_list_group
from datetime import datetime
from httpx import AsyncClient
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_message, require
global conclution
conclution = ''
picture_lib = {}

try:
    with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'r', encoding="utf-8") as fr:
        picture_lib = json.load(fr)
except:
    pass

scheduler = require('nonebot_plugin_apscheduler').scheduler  # 定义计划任务
get_pic = on_message(priority=5, rule=check_white_list_group())


@scheduler.scheduled_job('cron', day='1')  # 每月一日重获tocken
async def _get_token():
    async with AsyncClient() as Client:
        host = 'https://aip.baidubce.com/oauth/2.0/token'
        PostData = {'grant_type': 'client_credentials',
                    'client_id': baidu_client_id,
                    'client_secret': baidu_client_secret}
        get_data = await Client.post(host, data=PostData)
        result = get_data.json()
    access_token = result['access_token']
    picture_lib['token'] = access_token
    with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'w', encoding="utf-8") as f:
        json.dump(picture_lib, f, indent=2, sort_keys=True,
                  ensure_ascii=False)  # 获取新的token后储存


@get_pic.handle()
async def _get_pic(bot: Bot, event: GroupMessageEvent):
    async def Apprasial():
        async with AsyncClient() as Client:
            access_token = picture_lib['token']
            host = 'https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined'
            PostData = {'access_token': access_token,
                        'imgUrl': img}
            Headers = {"content-type": "application/x-www-form-urlencoded"}
            get_data = await Client.post(host, data=PostData, headers=Headers)
            result = get_data.json()
        if "error_code" in result:
            if result["error_code"] == 110:
                await _get_token()
                await Apprasial()
            else:
                return
        else:
            return result

    async def action():
        time = datetime.now()
        if conclution == '合规':
            picture_lib[event.message[0].data['file']] = '合规'
        elif conclution == '不合规':
            picture_lib[event.message[0].data['file']] = '不合规'
            msg = Message(
                f"[CQ:at,qq={event.user_id}]我叼你妈的在发图之前可以长点脑子吗？😅😅😅"
            )
            msg_master = (
                '上报违规消息！！！\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            await bot.send_private_msg(user_id=post_id, message=msg_master)
            await bot.send_private_msg(user_id=post_id, message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        elif conclution == '疑似':
            picture_lib[event.message[0].data['file']] = '疑似'
            msg = Message(
                f"[CQ:at,qq={event.user_id}]欸，你这图不对劲欸......"
            )
            msg_master = (
                '上报可疑消息......\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            await bot.send_private_msg(user_id=post_id, message=msg_master)
            await bot.send_private_msg(user_id=post_id, message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'w', encoding="utf-8") as f:
            json.dump(picture_lib, f, indent=2,
                      sort_keys=True, ensure_ascii=False)
        await get_pic.finish()

    if event.message[0].type == 'image':  # 判断是否为图片消息
        img = event.message[0].data['url']  # 获取图片hash
        file = event.message[0].data['file']
        if file in picture_lib:  # 图片是否在本地库中
            conclution = picture_lib[f'{file}']  # 从本地库中取得结论
            await action()  # 根据结论采取行动
        else:
            result = await Apprasial()  # 从API中取得结果
            conclution = result['conclusion']  # 从API中取得结论
            await action()  # 根据结论采取行动
