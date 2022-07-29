import os
import sqlite3

from io import BytesIO
from httpx import AsyncClient
from PIL import ImageFilter, Image, ImageDraw, ImageFont
from nonebot.adapters.onebot.v11 import MessageSegment, Message

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
        host_min = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=4'
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
        response_min = await Client.get(url=host_min)
        response_big = await Client.get(url=host_big)
        response_min = BytesIO(response_min.read())
        response_big = BytesIO(response_big.read())
    """虚化背景"""
    back_ground = Image.open(response_big).filter(CostumeGB(radius=60))
    """切圆头像"""
    img_head = Image.open(response_min)
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
    imgaeBytes = BytesIO()
    back_ground.save(imgaeBytes,format="png")
    return Message(MessageSegment.image(imgaeBytes))

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
            host_min = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=3'
            host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
            response_min = await Client.get(url=host_min)
            response_big = await Client.get(url=host_big)
            response_min = BytesIO(response_min.read())
            response_big = BytesIO(response_big.read())
        """虚化背景"""
        back_ground = Image.open(response_big).filter(CostumeGB(radius=60))
        """切圆头像"""
        img_head = Image.open(response_min)
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
    imgaeBytes = BytesIO()
    Final_IMG.save(imgaeBytes,format="png")
    return Message(MessageSegment.image(imgaeBytes))

async def get_head_img(QQ) -> bytes:
    async with AsyncClient(proxies={}) as Client:
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={QQ}&s=640'
        response_big = await Client.get(url=host_big)
    return response_big.read()

async def makeGalImg(tag:str, index:int) -> Message:
    """
        制作GalGme推荐图片
    """
    try:
        conn = sqlite3.connect(os.path.join(os.getcwd(),"Resources","gal.db"))
        galdb = conn.cursor()
    except:
        return Message("[文件缺失：Galgamedatabase]\ngal.db缺失，请检查项目完整性")
    else:
        sql = f'SELECT * FROM "{tag}" WHERE "index" = {index}'
        res = galdb.execute(sql).fetchone()
        pic:bytes = res[1]
        words:str = res[2]
        wordLiSt = words.split("\n")
        wordLiSt.remove("")
        introduce = wordLiSt[0]
        introList = []
        for i in range((len(introduce)//17)+1):
            i = i+1
            if i > 1:
                _ = "                  "+introduce[(i-1)*17:i*17]
            else:
                _=introduce[(i-1)*17:i*17]
            introList.append(_)
        wordLiSt.remove(wordLiSt[0])
        img = Image.open(BytesIO(pic))
        w, h = img.size
        w_s = int(w*3)
        h_s = int(h*3)
        img = img.resize((w_s, h_s),Image.ANTIALIAS)    #初步放大完成

        background = Image.open(os.path.join(os.getcwd(),"Resources","background.png"))
        background.paste(img, (80,80))

        set_Font = ImageFont.truetype(os.path.join(os.getcwd(),  "Resources", 'Fonts', 'STXINWEI.TTF'), 50)  # 设置字体属性
        
        a,b = background.size
        try:
            _ = Image.new("L", (a-80-w_s-180 ,h_s-17))  #可写字的区域
        except:
            return Message('[处理错误：ImgBuilder]\nSenrin脑子坏了T_T，再来一次吧...')
        write_words = ImageDraw.ImageDraw(background)
        set_h = 0
        for x in introList:
            write_words.text((660, 150+set_h), x, fill="#203864", font=set_Font) 
            set_h = set_h + 57

        for x in wordLiSt:
            write_words.text((660, 150+set_h), x, fill="#203864", font=set_Font) 
            set_h = set_h + 57

        imgaeBytes = BytesIO()
        background.save(imgaeBytes,format="png")
        return Message(MessageSegment.image(imgaeBytes))

async def makeLibImg(StudyPath) -> Message:
    """
        制作词库集合图片
    """
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(), "Resources", "Fonts", 'msyh.ttc'), 30)  # 设置字体属性
    with open(StudyPath, mode="r", encoding='utf-8-sig') as f:
        lib = '现有词库如下：\n'+f.read()  # 读取词库str
    x, _y = set_Font.getsize(max(lib.split('\n'), key=len))
    y, _x = set_Font.getsize((len(lib.split('\n'))*'00'))  # 斗长度！！！！！
    image = Image.new(mode='RGB', size=(x, y), color=(255, 255, 255))  # 新建画布
    draw = ImageDraw.ImageDraw(image)  # 写字
    draw.text((0, 0), lib, font=set_Font,fill="#000000", direction=None)  # 开始画！

    imgaeBytes = BytesIO()
    image.save(imgaeBytes,format="png")
    return Message(MessageSegment.image(imgaeBytes))