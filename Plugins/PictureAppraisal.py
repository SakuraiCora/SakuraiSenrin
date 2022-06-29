"""
    [半achieve]能跑就行能跑就行能跑就行能跑就行能跑就行能跑就行能跑就行能跑就行
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
from config import BAIDU_CLIENT_ID, BAIDU_CLIENT_SECRET
from Utils.CustomRule import Check_PA_Groups, only_reply
from datetime import datetime
from httpx import AsyncClient
from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_message, require
global conclution, picture_lib, check_api
conclution, check_api = '', True
SuperUsers:set[str] = get_driver().config.superusers
PicPath = os.path.join(os.getcwd(), 'Resources', 'Json', 'picture_lib.json')

try:
    with open(PicPath, 'r', encoding="utf-8") as fr:
        picture_lib = json.load(fr)
except:
    picture_lib = {}

scheduler = getattr(require('nonebot_plugin_apscheduler'),'scheduler')  # 定义计划任务
repire_lib = on_message(priority=5, rule=only_reply())
get_pic = on_message(priority=5, rule=Check_PA_Groups())


@scheduler.scheduled_job('cron', day='1')  # 每月一日重获tocken
async def _get_token():
    async with AsyncClient(proxies={}) as Client:
        host = 'https://aip.baidubce.com/oauth/2.0/token'
        PostData = {'grant_type': 'client_credentials',
                    'client_id': BAIDU_CLIENT_ID,
                    'client_secret': BAIDU_CLIENT_SECRET}
        get_data = await Client.post(host, data=PostData)
        result = get_data.json()
    access_token = result['access_token']
    picture_lib['token'] = access_token
    with open(PicPath, 'w', encoding="utf-8") as f:
        json.dump(picture_lib, f, indent=2, sort_keys=True,
                  ensure_ascii=False)  # 获取新的token后储存
    return access_token


@get_pic.handle()
async def _get_pic(bot: Bot, event: GroupMessageEvent):
    async def Apprasial():
        async with AsyncClient(proxies={}) as Client:
            try:
                access_token = picture_lib['token']
            except:
                access_token = await _get_token()
            else:
                pass
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
                for Admin in SuperUsers:
                    await bot.send_private_msg(user_id=int(Admin), message='API调用次数已耗尽，请立即上报！')
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
                f"[WARNING:不合规]\n[CQ:at,qq={event.user_id}]超速了超速了超速了超......"
            )
            msg_master = (
                '上报违规消息！！！\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            for Admin in SuperUsers:
                await bot.send_private_msg(user_id=int(Admin), message=msg_master)
                await bot.send_private_msg(user_id=int(Admin), message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        elif conclution == '疑似':
            picture_lib[img_msg.data['file']] = '疑似'
            msg = Message(
                f"[WARNING:疑似]\n[CQ:at,qq={event.user_id}]注意车速（"
            )
            msg_master = (
                '上报可疑消息......\n'
                f'MessageID:{event.message_id}\n'
                f'Sender:{event.sender.nickname}({event.user_id})\n'
                f'Time:{time}'
            )
            for Admin in SuperUsers:
                await bot.send_private_msg(user_id=int(Admin), message=msg_master)
                await bot.send_private_msg(user_id=int(Admin), message=Message(f"Message:{str(event.get_message())}"))
            await get_pic.send(msg)
        with open(PicPath, 'w', encoding="utf-8") as f:
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
                    conclution = result['conclusion']  #type:ignore 从API中取得结论
                    await action(_msg)  # 根据结论采取行动
            else:
                for Admin in SuperUsers:
                    await bot.send_private_msg(user_id=int(Admin), message='API调用次数已耗尽，请立即上报！')
                await get_pic.finish()
        else:
            pass
    await get_pic.finish()


@repire_lib.handle()
async def _repire_lib(bot: Bot, event: Event):
    sendmsg = (
        Message(
            ''
            f"[CQ:at,qq={event.get_user_id()}]Senrin把消息抖空了硬是没发现图片的影子\n"
            "若持续出现此报错，请按照以下步骤修正：\n"
            '1.将图片逐张转发至Senrin\n'
            '2.回复需要修正图片并附上“修正”'
        )
    )
    check_img = False
    if isinstance(event, GroupMessageEvent):
        if '修正' in str(event.message) and str(event.user_id) in SuperUsers:
            for _msg in event.reply.message:#type:ignore
                if _msg.type == 'image':
                    check_img = True
                    picture_lib[_msg.data['file']] = '合规'
                    await repire_lib.send('[repaire正常:succeed]\n'
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
        if event.user_id in SuperUsers:
            if '修正' in str(event.message):
                for _msg in event.reply.message:#type:ignore
                    if _msg.type == 'image':
                        check_img = True
                        picture_lib[_msg.data['file']] = '合规'
                        await repire_lib.send('[repaire正常:succeed]\n'
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
    with open(PicPath, 'w', encoding="utf-8") as f:
        json.dump(picture_lib, f, indent=2, sort_keys=True, ensure_ascii=False)
    await repire_lib.finish()