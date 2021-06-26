"""
    TextAppraisal包含的功能：
    1.初步鉴定消息是否为文字
    2.发现违规立即上报
    3.正则匹配URL
"""
from costrule import check_white_list_group
import re
from datetime import datetime
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_message
from config import AdminList_REPORT

get_text = on_message(priority=5, rule=check_white_list_group())


@get_text.handle()
async def _get_text(bot: Bot, event: GroupMessageEvent):
    async def report():
        time = datetime.now()
        msg = Message(
            f"[CQ:at,qq={event.user_id}]喂，你看看你发的什么消息啊kora！"
        )
        msg_master = (
            '上报链接消息！！！\n'
            f'MessageID:{event.message_id}\n'
            f'Sender:{event.sender.nickname}({event.user_id})\n'
            f'Time:{time}'
        )
        for Admin in AdminList_REPORT:
            await bot.send_private_msg(user_id=Admin, message=msg_master)
            await bot.send_private_msg(user_id=Admin, message=Message(f"Message:{str(event.get_message())}"))
        await get_text.send(msg)

    out_msg = ''
    for _msg in event.message:
        if _msg.type == 'xml' or _msg.type == 'json':
            await report()
        if _msg.type == 'text':
            for each in str(_msg):
                if re.match(r'[A-Za-z0-9;/?:@&=]', each):
                    out_msg += each
                else:
                    pass
            if out_msg:
                if re.match(r'(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?', out_msg) or re.match(r'^(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)?((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.[a-zA-Z]{2,4})(\:[0-9]+)?(/[^/][a-zA-Z0-9\.\,\?\'\\/\+&%\$#\=~_\-@]*)*$', out_msg) or re.match(r'^(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*$', out_msg) or re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$', out_msg) or re.match(r'^(((ht|f)tp(s?))\://)?(www.|[a-zA-Z].)[a-zA-Z0-9\-\.]+\.(com|edu|gov|mil|net|org|biz|info|name|museum|us|ca|uk)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\;\?\'\\\+&%\$#\=~_\-]+))*$', out_msg) or re.match(r'\b(([\w-]+://?|www[.])[^\s()<>]+(?:[\w\d]+|([^[:punct:]\s]|/)))', out_msg):
                    await report()
                else:
                    pass
            else:
                pass
        else:
            pass
    await get_text.finish()
