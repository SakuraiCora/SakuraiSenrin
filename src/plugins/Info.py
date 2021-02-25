"""
    Info包含的功能：
    根据有限的信息制作资料卡
"""
import re
import os
import aiofiles
import datetime
from httpx import AsyncClient
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from nonebot.adapters.cqhttp.message import Message
from nonebot.plugin import on_command
from costrule import check_white_list_group

class CostumeGB(ImageFilter.Filter):
    name = "GaussianBlur"

    def __init__(self, radius=2, bounds=None):
        self.radius = radius
        self.bounds = bounds

    def filter(self, image):
        if self.bounds:
            clips = image.crop(self.bounds).gaussian_blur(self.radius)
            image.paste(clips, self.bounds)
            return image
        else:
            return image.gaussian_blur(self.radius)
async def get_card(QQ, user_name, sex, title, level, time):
    async with AsyncClient(proxies={}) as Client:
        path_min = os.path.join(os.getcwd(),'Data_Base',f'{QQ}_min.jpg')
        path_big = os.path.join(os.getcwd(),'Data_Base',f'{QQ}_big.jpg')
        host_min = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=4'
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
        response_min = await Client.get(url=host_min)
        response_big = await Client.get(url=host_big)
        response_min = response_min.read()
        response_big = response_big.read()
        async with aiofiles.open(path_min,mode='wb') as Photo_min:
            await Photo_min.write(response_min)
        async with aiofiles.open(path_big,mode='wb') as Photo_big:
            await Photo_big.write(response_big)
    """虚化背景"""
    back_ground = Image.open(path_big).filter(CostumeGB(radius=60)) 
    """切圆头像"""
    img_head = Image.open(path_min)
    w = 140
    alpha_layer = Image.new('L', (w, w))
    draw = ImageDraw.ImageDraw(alpha_layer)
    draw.ellipse((0, 0, w, w), fill=255)
    img_head.putalpha(alpha_layer)
    """组合图片"""
    back_ground.paste(img_head,(250,10),alpha_layer)
    """user_name"""
    write_words = ImageDraw.ImageDraw(back_ground)
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(),"Data_Base",'msyh.ttc'), 60) #设置字体属性
    w, h = set_Font.getsize(user_name)
    write_words.text(((640-w)/2, 150), user_name, fill="#FFFFFF", font=set_Font)    #type:ignore
    """QQ title level sex"""
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(),"Data_Base",'msyh.ttc'), 30) #设置字体属性
    write_words.text((40,300),f'QQ号：{str(QQ)}',fill="#FFFFFF",font=set_Font)
    write_words.text((40,400),f'头衔：{title}',fill="#FFFFFF",font=set_Font)
    write_words.text((400,300),f'性别：{sex}',fill="#FFFFFF",font=set_Font)
    write_words.text((400,400),f'等级：{level}',fill="#FFFFFF",font=set_Font)
    """time"""
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(),"Data_Base",'msyh.ttc'), 40) #设置字体属性
    write_words.text((40,500),f'入群时间：{time}',fill="#FFFFFF",font=set_Font)
    """copyright"""
    cr = 'Copyright ©2020-2021 SakuraiCora, All Rights Reserved.'
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(),"Data_Base",'msyh.ttc'), 15) #设置字体属性
    w, h = set_Font.getsize(cr)
    write_words.text(((640-w)/2, 600), cr, fill="#FFFFFF", font=set_Font)    #type:ignore
    save_path = os.path.join(os.getcwd(),"Data_Base","send.jpg")    #设置保存路径
    back_ground.save(save_path)
    return save_path

info = on_command('info',priority=5,rule=check_white_list_group())
@info.handle()
async def info_get(bot: Bot, event):
    args = str(event.get_message()).strip()
    if args:
        try:
            args = re.findall(r"\[CQ:at,qq=(\d+).*?\]", args)  # 正则匹配QQ号
            args = int(args[0])
        except:
            await info.finish("[参数处理错误：args]")  # 异常处理
    if isinstance(event, GroupMessageEvent):
        if isinstance(args, int):
            msg = Message(
                "Zer0正在制作属于你的专属资料卡......\n"
                f"制作对象：[CQ:at,qq={str(args)}]"
            )
            await info.send(msg)
            QQ = int(str(args))
        elif event.to_me == True:
            msg = Message(
                "嘿嘿没想到吧，Zer0也有资料卡哦！\n"
                f"制作对象：[CQ:at,qq={bot.self_id}]"
            )
            await info.send(msg)
            QQ = int(bot.self_id)
        else:  # 个人记录查询
            msg = Message(
                "Zer0正在制作属于你的专属资料卡......\n"
                f"制作对象：[CQ:at,qq={event.user_id}]"
            )
            await info.send(msg)
            QQ = event.user_id
        member_info = await bot.get_group_member_info(group_id=event.group_id,user_id=QQ)        
        dateArray = datetime.datetime.utcfromtimestamp(member_info['join_time'])
        join_time_format = dateArray.strftime("%Y-%m-%d %H:%M:%S")
        save_path = await get_card(QQ,member_info['nickname'],member_info['sex'],member_info['title'],f"LV.{member_info['level']}",join_time_format)
        await info.finish(Message(f"[CQ:image,file=file:///{save_path}]"))
    else:
        await info.finish("请您高抬贵脚移步至群聊中查询可否？")