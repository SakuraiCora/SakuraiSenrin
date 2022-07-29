"""
    SearchPic包含的功能：
    1.基本的回复搜图
    2.判断是否给出图片
    3.样品图片存入库中
    4.检验搜索结果是否存在
    5.多图连搜
"""
import traceback

from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.plugin import on_message
from Utils.CustomRule import check_white_list, only_reply
from Utils.Builder import ExceptionBuilder
from .handle import SauceNAO

Reply_SearchPic = on_message(priority=5, rule=only_reply() & check_white_list(), block=True)


@Reply_SearchPic.handle()
async def _Reply_SearchPic(bot: Bot, event: MessageEvent):
    send_except_msg = (
        MessageSegment.at(event.user_id)
        +MessageSegment.text("Senrin把消息抖空了硬是没发现图片的影子\n"
                            +"若持续出现此报错，请按照以下步骤搜图：\n"
                            +'1.将图片逐张转发至Senrin\n'
                            +'2.回复需要搜索的图片并附上“搜图”')
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
            await Reply_SearchPic.send('[SearchPic正常:Succeed]\nちょっと待ってください......')
            for numst in range(len(search_list)):
                msg_url = search_list[numst]
                # 获取搜索结果
                try:
                    search_result = await SauceNAO(numst=numst, pic_url=msg_url)
                except:
                    await Reply_SearchPic.finish(f'[未知错误:Unknown]\n似乎出现了蜜汁错误......图搜到了但没完全搜到......\n{ExceptionBuilder(traceback.format_exc())}')
                if search_result:
                    result_list.append(search_result)
            if result_list:  # 存在搜索结果
                for result_send in result_list:
                    _add_result = (
                        f"第{result_send[0]}张图片：\n"
                        f"{result_send[1]}\n"
                    )
                    send_msg_result += _add_result
                await Reply_SearchPic.send(Message('[SearchPic正常:Succeed]\n好耶！找到图咯！\n'+send_msg_result))
            else:  # 不存在搜索结果
                await Reply_SearchPic.send(MessageSegment.text(f'[SearchPic正常:Succeed]\n').at(event.get_user_id()).text('暂无相关信息，Senrin搜了个寂寞'))
        else:  # 无图
            await Reply_SearchPic.finish(send_except_msg)
    await Reply_SearchPic.finish()