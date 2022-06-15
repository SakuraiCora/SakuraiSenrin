import os
import aiofiles

from httpx import AsyncClient
from PIL import ImageFilter, Image, ImageDraw, ImageFont
from nonebot.adapters.cqhttp import MessageSegment, Message

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

async def get_info_card(QQ:int, user_name:str, sex:str, title:str, level:str, time:str) -> Message:
    """
        制作资料卡
    """
    async with AsyncClient(proxies={}) as Client:
        path_min = os.path.join(os.getcwd(), 'Resources',
                                'HeadIMG', f'{QQ}_min.jpg')
        path_big = os.path.join(os.getcwd(), 'Resources',
                                'HeadIMG', f'{QQ}_big.jpg')
        host_min = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=4'
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
        response_min = await Client.get(url=host_min)
        response_big = await Client.get(url=host_big)
        response_min = response_min.read()
        response_big = response_big.read()
        async with aiofiles.open(path_min, mode='wb') as Photo_min:
            await Photo_min.write(response_min)
        async with aiofiles.open(path_big, mode='wb') as Photo_big:
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
    back_ground.paste(img_head, (250, 10), alpha_layer)
    """user_name"""
    write_words = ImageDraw.ImageDraw(back_ground)
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'msyh.ttc'), 60)  # 设置字体属性
    w, h = set_Font.getsize(user_name)
    write_words.text(((640-w)/2, 150), user_name,   # type:ignore
                     fill="#FFFFFF", font=set_Font)  
    """QQ title level sex"""
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'msyh.ttc'), 30)  # 设置字体属性
    write_words.text((40, 300), f'QQ号：{str(QQ)}',
                     fill="#FFFFFF", font=set_Font)
    write_words.text((40, 400), f'头衔：{title}', fill="#FFFFFF", font=set_Font)
    write_words.text((400, 300), f'性别：{sex}', fill="#FFFFFF", font=set_Font)
    write_words.text((400, 400), f'等级：{level}', fill="#FFFFFF", font=set_Font)
    """time"""
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'msyh.ttc'), 40)  # 设置字体属性
    write_words.text((40, 500), f'入群时间：{time}', fill="#FFFFFF", font=set_Font)
    """copyright"""
    cr = 'Copyright ©2020-2022 SakuraiCora, All Rights Reserved.'
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'msyh.ttc'), 15)  # 设置字体属性
    w, h = set_Font.getsize(cr)
    write_words.text(((640-w)/2, 600), cr, fill="#FFFFFF",  # type:ignore
                     font=set_Font)
    save_path = os.path.join(os.getcwd(), "Resources", "HeadSend.jpg")  # 设置保存路径
    back_ground.save(save_path)
    return Message(MessageSegment.image(f'file:///{save_path}'))

async def get_water_card(member_info:list[tuple[int,str,int]]) -> Message:
    """
        制作吹氵排行榜
    """
    WaterList:list[Image.Image] = []

    for _item in member_info:
        QQ = _item[0]
        user_name = _item[1]
        waterTimes = _item[2]
        name = user_name if len(user_name) <=12 else user_name[:12]+"..."

        async with AsyncClient(proxies={}) as Client:
            path_min = os.path.join(os.getcwd(), 'Resources',
                                    'HeadIMG', f'{QQ}_min.jpg')
            path_big = os.path.join(os.getcwd(), 'Resources',
                                    'HeadIMG', f'{QQ}_big.jpg')
            host_min = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=3'
            host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
            response_min = await Client.get(url=host_min)
            response_big = await Client.get(url=host_big)
            response_min = response_min.read()
            response_big = response_big.read()
            async with aiofiles.open(path_min, mode='wb') as Photo_min:
                await Photo_min.write(response_min)
            async with aiofiles.open(path_big, mode='wb') as Photo_big:
                await Photo_big.write(response_big)
        """虚化背景"""
        back_ground = Image.open(path_big).filter(CostumeGB(radius=60))
        """切圆头像"""
        img_head = Image.open(path_min)
        w = 100
        alpha_layer = Image.new('L', (w, w))
        draw = ImageDraw.ImageDraw(alpha_layer)
        draw.ellipse((0, 0, w, w), fill=255)
        img_head.putalpha(alpha_layer)
        """组合图片"""
        back_ground.paste(img_head, (0,0), alpha_layer)
        """裁剪图片"""
        back_ground = back_ground.crop((0,0,640,100))
        """添加文字"""
        write_words = ImageDraw.ImageDraw(back_ground)
        set_Font = ImageFont.truetype(os.path.join(os.getcwd(), "Resources", 'Fonts', 'zsjt.ttf'), 50)  # 设置字体属性
        w1, h1 = set_Font.getsize(name)
        w2, h2 = set_Font.getsize(f'{waterTimes}次')
        write_words.text((100, (100-h1)/2), name, fill="#FFFFFF", font=set_Font)  
        write_words.text((640-w2, (100-h1)/2), f'{waterTimes}次', fill="#FFFFFF", font=set_Font)
        WaterList.append(back_ground)

    Final_IMG = Image.new('RGB',(640,100*len(WaterList)))#最终拼接的图像的大小
    Y_left = 0
    Y_right = 100
    for _item in WaterList:
        Final_IMG.paste(_item,(0,Y_left,640,Y_right))
        Y_left += 100
        Y_right += 100
    save_path = os.path.join(os.getcwd(), "Resources", "WaterSend.jpg")  # 设置保存路径
    Final_IMG.save(save_path)
    return Message(MessageSegment.image(f'file:///{save_path}'))

async def get_head_img(QQ) -> str:
    async with AsyncClient(proxies={}) as Client:
        path_big = os.path.join(os.getcwd(), 'Resources','HeadIMG', f'{QQ}_big.jpg')
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
        response_big = await Client.get(url=host_big)
    response_big = response_big.read()
    async with aiofiles.open(path_big, mode='wb') as Photo_big:
        await Photo_big.write(response_big)
    return (f'file:///{path_big}')