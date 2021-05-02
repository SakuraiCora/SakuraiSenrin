"""
    SearchPic包含的功能：
    1.基本的回复搜图
    2.判断是否给出图片
    3.样品图片存入库中
    4.检验搜索结果是否存在
    5.多图连搜
"""
import re
import os
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import (
    Event, GroupMessageEvent, PrivateMessageEvent)
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_message
from costrule import only_reply
from httpx import AsyncClient

api_key = 'bbb7fcbbd4bef75c7b66e8a42a1ee4136f939ac3'
Reply_SearchPic = on_message(priority=5, rule=only_reply(), block=True)


@Reply_SearchPic.handle()
async def _Reply_SearchPic(bot: Bot, event: Event):
    send_except_msg = (
        Message(
            f"[CQ:at,qq={event.get_user_id()}]你确定你给我的是一张图片？\n"
            "若持续出此报错，请按照以下步骤搜图：\n"
            '1.将图片逐张转发至Zer0\n'
            '2.回复需要搜索的图片并附上“搜图”'
        )
    )
    if '搜图' in str(event.get_message()):
        search_list = []
        result_list = []
        send_msg_result = '搜图结果如下：\n'
        for _msg in event.reply.message:  # type:ignore    初步处理数据
            if _msg.type == 'image':
                search_list.append(_msg.data['url'])
            else:
                pass
        if search_list:  # 有图
            await Reply_SearchPic.send('ちょっと待ってください......')
            for numst in range(len(search_list)):
                msg_url = search_list[numst]
                # 获取搜索结果
                search_result = await SauceNAO(numst=numst, pic_url=msg_url)
                if search_result:
                    result_list.append(search_result)
            if result_list:  # 存在搜索结果
                for result_send in result_list:
                    _add_result = (
                        f"第{result_send[0]}张图片：\n"
                        f"{result_send[1]}"
                    )
                    send_msg_result += _add_result
                if isinstance(event, GroupMessageEvent):
                    await Reply_SearchPic.send(Message(f'[CQ:at,qq={event.get_user_id()}] Zer0从SauceNAO获得了搜图结果，并将以私聊方式发送！'))
                    await bot.send_private_msg(user_id=event.user_id, message=Message(send_msg_result))
                elif isinstance(event, PrivateMessageEvent):
                    await Reply_SearchPic.send(Message('好耶！找到图咯！\n'+send_msg_result))
            else:  # 不存在搜索结果
                await Reply_SearchPic.send(Message(f'[CQ:at,qq={event.get_user_id()}] 暂无相关信息，Zer0搜了个寂寞'))
        else:  # 无图
            await Reply_SearchPic.finish(send_except_msg)
    await Reply_SearchPic.finish()


async def SauceNAO(numst, pic_url):  # 搜图结果，空则返回None，return示例：(1,NAO_result)
    async with AsyncClient(proxies={}) as Client:
        response = await Client.get(url=f"https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=1&api_key={api_key}&url={pic_url}")
    result = response.json()
    try:  # 从相关系数判断搜索结果是否存在
        similarity = float(result['results'][0]['header']['similarity'])
    except:
        return None
    else:
        if similarity < 50.0:
            return None
        pic_url = result['results'][0]['header']['thumbnail']
        async with AsyncClient(proxies={}) as Client:
            _get_sample = await Client.get(url=pic_url)
            get_sample = _get_sample.read()
            with open(file=os.path.join(os.getcwd(), 'Data_Base\\SamplePic.jpg'), mode='wb') as WS:
                WS.write(get_sample)
        pic_url = os.path.join(os.getcwd(), 'Data_Base\\SamplePic.jpg')
        try:
            source = result['results'][0]['data']['source']
        except:
            source = '无相关信息'
        try:
            creator = result['results'][0]['data']['creator']
        except:
            creator = '无相关信息'
        if 'pixiv' in source:  # 不标准的pixiv来源
            pattern = re.compile(r'\d+')
            illust = pattern.findall(source)[0]
            NAO_result = (
                "检测到图源于Pixiv\n"
                f"[CQ:image,file=file:///{pic_url}]\n"
                f'相似系数：{similarity}\n'
                f"插画画师：{creator}\n"
                f'插画ID：{illust}\n'
                f'Pixiv源址：{source}'
            )
        elif 'pixiv_id' in result['results'][0]['data']:  # 标准的pixiv来源
            creator = result['results'][0]['data']['member_name']
            source = result['results'][0]['data']['ext_urls'][0]
            illust = result['results'][0]['data']['pixiv_id']
            title = result['results'][0]['data']['title']
            NAO_result = (
                "检测到图源于Pixiv\n"
                f"[CQ:image,file=file:///{pic_url}]\n"
                f'相似系数：{similarity}\n'
                f'插画名称：{title}\n'
                f"插画画师：{creator}\n"
                f'插画ID：{illust}\n'
                f'Pixiv源址：{source}'
            )
        else:  # 其他来源
            source = result['results'][0]['data']['ext_urls'][0]
            NAO_result = (
                f"[CQ:image,file=file:///{pic_url}]\n"
                f'相似系数：{similarity}\n'
                f'图片作者：{creator}\n'
                f'图片源址：{source}'
            )
        return (numst+1, NAO_result)
