"""
    PictureAppraisal包含的功能：
    1.初步鉴定消息是否为图片
    2.初步筛查表情包与图片
    3.调用BaiduAPI进行鉴定，返回结果
    4.发现违规立即上报
    5.每30天一次重获token
    6.合规的图片存入库中，不再上报（json/dict写针不戳）
    7.可以针对误报的图片进行修正
    {
        file:value,
        file:value,
        file:value
    }
"""
import json
import os
from config import baidu_client_id, baidu_client_secret, AdminList, AdminList_REPORT
from costrule import only_reply
from datetime import datetime
from httpx import AsyncClient
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_message, require
global conclution, picture_lib, check_api
conclution, check_api = '', True

try:
    with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'r', encoding="utf-8") as fr:
        picture_lib = json.load(fr)
except:
    picture_lib = {}

scheduler = require('nonebot_plugin_apscheduler').scheduler  # 定义计划任务
repire_lib = on_message(priority=5, rule=only_reply())
get_pic = on_message(priority=5)


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
            if result["error_code"] == 111:
                await _get_token()
                await Apprasial()
            elif result['error_code'] == 17:
                check_api = False
                for Admin in AdminList_REPORT:
                    await bot.send_private_msg(user_id=Admin, message='API调用次数已耗尽，请立即上报！')
                await get_pic.finish()
        else:
            return result

    async def action(img_msg):
        time = datetime.now()
        if conclution == '合规':
            picture_lib[img_msg.data['file']] = '合规'
        elif conclution == '不合规':
            picture_lib[img_msg.data['file']] = '不合规'
            msg = Message(
                f"[CQ:at,qq={event.user_id}]我叼你妈的在发图之前可以长点脑子吗？😅😅😅"
            )
            msg_master = (
                '上报违规消息！！！\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            for Admin in AdminList_REPORT:
                await bot.send_private_msg(user_id=Admin, message=msg_master)
                await bot.send_private_msg(user_id=Admin, message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        elif conclution == '疑似':
            picture_lib[img_msg.data['file']] = '疑似'
            msg = Message(
                f"[CQ:at,qq={event.user_id}]欸，你这图不对劲欸......"
            )
            msg_master = (
                '上报可疑消息......\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            for Admin in AdminList_REPORT:
                await bot.send_private_msg(user_id=Admin, message=msg_master)
                await bot.send_private_msg(user_id=Admin, message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'w', encoding="utf-8") as f:
            json.dump(picture_lib, f, indent=2,
                      sort_keys=True, ensure_ascii=False)
    for _msg in event.message:
        if _msg.type == 'image':  # 判断是否为图片消息
            img = _msg.data['url']  # 获取图片hash
            file = _msg.data['file']
            if check_api != False:
                if file in picture_lib:  # 图片是否在本地库中
                    conclution = picture_lib[f'{file}']  # 从本地库中取得结论
                    await action(_msg)  # 根据结论采取行动
                else:
                    result = await Apprasial()  # 从API中取得结果
                    conclution = result['conclusion']  # 从API中取得结论
                    await action(_msg)  # 根据结论采取行动
            else:
                for Admin in AdminList_REPORT:
                    await bot.send_private_msg(user_id=Admin, message='API调用次数已耗尽，请立即上报！')
                await get_pic.finish()
        else:
            pass
    await get_pic.finish()


@repire_lib.handle()
async def _repire_lib(bot: Bot, event: Event):
    sendmsg = (
        Message(
            f"[CQ:at,qq={event.get_user_id()}]你确定你给我的是一张图片？\n"
            "若持续出此报错，请按照以下步骤修正：\n"
            '1.将图片逐张转发至Zer0\n'
            '2.回复需要修正图片并附上“修正”'
        )
    )
    check_img = False
    if isinstance(event, GroupMessageEvent):
        if '修正' in str(event.message) and event.user_id in AdminList:
            for _msg in event.reply.message:
                if _msg.type == 'image':
                    check_img = True
                    picture_lib[_msg.data['file']] = '合规'
                    await repire_lib.send('那啥......Zer0已经去把数据库揍了一顿了\n'
                                          '应该不会发疯了吧......\n'
                                          '修正完毕')
                else:
                    pass
            if check_img == False:
                await repire_lib.finish(sendmsg)
            else:
                pass
        else:
            pass
    elif isinstance(event, PrivateMessageEvent):
        if event.user_id in AdminList:
            if '修正' in str(event.message):
                for _msg in event.reply.message:
                    if _msg.type == 'image':
                        check_img = True
                        picture_lib[_msg.data['file']] = '合规'
                        await repire_lib.send('那啥......Zer0已经去把数据库揍了一顿了\n'
                                              '应该不会发疯了吧......\n'
                                              '修正完毕')
                    else:
                        pass
                if check_img == False:
                    await repire_lib.finish(sendmsg)
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass
    with open(f"{os.getcwd()}\\Data_Base\\picture_lib.json", 'w', encoding="utf-8") as f:
        json.dump(picture_lib, f, indent=2, sort_keys=True, ensure_ascii=False)
    await repire_lib.finish()
