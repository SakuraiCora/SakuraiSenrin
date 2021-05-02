"""
    Study包含的功能：
    学习模块（写入 读取 操作词库）
    {
        "public":{
            "key":("value","user_id"),
            "key":("value","user_id"),
            "key":("value","user_id"),
            "key":("value","user_id")
        }
        "private":{
            "user_id":{
                "key":"value",
                "key":"value",
                "key":"value"
            }
            "user_id":{
                "key":"value",
                "key":"value",
                "key":"value"
            }
            "user_id":{
                "key":"value",
                "key":"value",
                "key":"value"
            }
        }
    }
"""
import os
import json
from config import masterList
from costrule import check_white_list_all, only_master
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.message import Message
from nonebot.adapters.cqhttp.event import PrivateMessageEvent
from nonebot.plugin import on_message
from nonebot.typing import T_State
from PIL import Image, ImageDraw, ImageFont

study = on_command("study", priority=5,
                   rule=check_white_list_all())  # 定义study命令
lib_manage = on_command('lib_manage', priority=5,
                        rule=only_master())  # 定义查询与删除
get_march = on_message(rule=check_white_list_all(), priority=5)

with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'r', encoding="utf-8") as fr:
    studylib = json.load(fr)


@study.handle()  # study写入，需二次确认[private]
async def handle_study(bot: Bot, event: Event, state: T_State):
    arg = str(event.get_message()).split()
    """
        study写入传参 #study module(str) key(str) value(str)        至于<similar(int)>就先咕咕咕吧（别打我）
        这次用dict写，可以用更多的符号
    """
    if len(arg) != 3:
        await study.finish('[传参错误]：参数数量不足或过多')
    if arg:
        if arg[0] not in ['a', 'm', 'A', 'M']:
            await study.finish('[传参错误]：参数表达错误')
        else:
            if arg[0].lower() == 'a':  # to_all 全员响应
                if arg[1] not in studylib['public']['all_users'].keys():
                    studylib['public']['all_users'][arg[1]] = (
                        arg[2], event.get_user_id())
                    msg = (
                        '好耶！学会了新东西！'
                    )
                    with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'w', encoding="utf-8") as f:
                        json.dump(studylib, f, indent=2,
                                  sort_keys=True, ensure_ascii=False)
                    await study.finish(msg)
                else:
                    if event.get_user_id() not in masterList:
                        msg = (
                            "芜湖~词库里有这条条例咯......"
                        )
                        await study.finish(msg)
                    else:
                        state['key'], state['value'] = arg[1], arg[2]
                        state['class'] = 'A'
            elif arg[0].lower() == 'm':
                if event.get_user_id() not in studylib['private'].keys():
                    studylib['private'][str(event.get_user_id())] = {}
                else:
                    pass
                state['key'], state['value'] = arg[1], arg[2]
                if arg[1] not in studylib['private'][str(event.get_user_id())].keys():
                    studylib['private'][str(
                        event.get_user_id())][arg[1]] = arg[2]
                    msg = (
                        '好耶！学会了新东西！'
                    )
                    with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'w', encoding="utf-8") as f:
                        json.dump(studylib, f, indent=2,
                                  sort_keys=True, ensure_ascii=False)
                    await study.finish(msg)
                else:
                    state['class'] = 'M'


@study.got('result', prompt='芜湖~词库里有这条条例咯......\n覆盖原条例？（Y/N）')
async def got_study(bot: Bot, event: Event, state: T_State):
    result = state['result']
    if result not in ['Y', 'y', 'N', 'n']:
        await study.reject('输入不合规范呐.......\nY为覆盖原条例\nN为保留原条例')
    if result.lower() == 'y':
        if state['class'] == 'M':
            studylib['private'][str(event.get_user_id())
                                ][state['key']] = state['value']
            with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'w', encoding="utf-8") as f:
                json.dump(studylib, f, indent=2,
                          sort_keys=True, ensure_ascii=False)
        elif state['class'] == 'A':
            studylib['public']['all_users'][state['key']] = state['value']
            with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'w', encoding="utf-8") as f:
                json.dump(studylib, f, indent=2,
                          sort_keys=True, ensure_ascii=False)
        await study.finish('好耶！已经覆盖了原条例！')
    elif result.lower() == 'n':
        await study.finish('已保留原条例！Zer0又白忙活了......\n草你妈燃起来了！')


@lib_manage.handle()  # 空元素return_help  show展示 del删除(class uesr_id key)
async def _del_lib(bot: Bot, event: Event, state: dict):
    arg = str(event.get_message()).split()
    if arg:  # 空元素返回
        if arg[0] not in ['show', 'del']:
            await lib_manage.finish("#lib_manage\n  1.show\n  2.del class uesr_id key")
        else:
            if arg[0] == 'show':
                if isinstance(event, PrivateMessageEvent):
                    set_Font = ImageFont.truetype(os.path.join(
                        os.getcwd(), "Data_Base", 'msyh.ttc'), 30)  # 设置字体属性
                    save_path = os.path.join(
                        os.getcwd(), "Data_Base", "send.jpg")  # 设置保存路径
                    with open(os.path.join(os.getcwd(), "Data_Base", "studylib.json"), mode="r", encoding='utf-8-sig') as f:
                        lib = '现有词库如下：\n'+f.read()  # 读取词库str
                    x,_y = set_Font.getsize(max(lib.split('\n'),key=len))
                    y,_x = set_Font.getsize((len(lib.split('\n'))*'00'))    #斗长度！！！！！
                    image = Image.new(mode='RGB', size=(
                        x, y), color=(255, 255, 255))  # 新建画布
                    draw = ImageDraw.ImageDraw(image)  # 写字
                    draw.text((0, 0), lib, font=set_Font,
                              fill="#000000", direction=None)  # 开始画！
                    image.save(save_path)  # 保存作画
                    await lib_manage.finish(Message(f"[CQ:image,file=file:///{save_path}]"))
                else:
                    await lib_manage.finish("nmlgb宁一定要在大庭广众之下公开这些信息么？？？")
            elif arg[0] == 'del':
                try:
                    del studylib[arg[1]][arg[2]][arg[3]]
                    with open(f"{os.getcwd()}\\Data_Base\\studylib.json", 'w', encoding="utf-8") as f:
                        json.dump(studylib, f, indent=2,
                                  sort_keys=True, ensure_ascii=False)
                except:
                    await lib_manage.finish("#lib_manage\n  1.show\n  2.del class uesr_id key")
                else:
                    msg = (
                        "已删除对应的词库！\n"
                        f"class:{arg[1]}\n"
                        f"user_id:{arg[2]}\n"
                        f"key:{arg[3]}"
                    )
                    await lib_manage.finish(msg)
    else:
        await lib_manage.finish("#lib_manage\n  1.show\n  2.del class uesr_id key")


@get_march.handle()
async def _get_march(bot: Bot, event: Event):
    try:
        return_msg_pub = studylib['public']['all_users'][str(
            event.get_message())][0]
        await get_march.finish(Message(return_msg_pub))
    except:
        pass
    try:
        return_msg_pri = studylib['private'][event.get_user_id()][str(
            event.get_message())]
        await get_march.finish(Message(return_msg_pri))
    except:
        pass
