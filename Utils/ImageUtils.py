import os
import math
import sqlite3

from io import BytesIO
from typing import List, Dict
from httpx import AsyncClient
from pil_utils import Text2Image
from pil_utils.types import ColorType
from PIL import ImageFilter, Image, ImageDraw, ImageFont

from .CustumClass import ReverseItem
from .MessageUtils import split_list, split_str

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

async def get_info_card(qq:int, user_name:str, sex:str, title:str, level:str, time:str) -> BytesIO:
    """
        制作资料卡
    """
    async with AsyncClient(proxies={}) as Client:
        host_min = f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s=4'
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s=640'
        response_min = await Client.get(url=host_min)
        response_big = await Client.get(url=host_big)
        response_min = BytesIO(response_min.read())
        response_big = BytesIO(response_big.read())
    """虚化背景"""
    back_ground = Image.open(response_big).filter(CostumeGB(radius=60))
    """切圆头像"""
    w = 140
    img_head_open = Image.open(response_min)
    img_head = Image.new('RGBA', (w, w))
    img_head.paste(img_head_open)
    alpha_layer = Image.new('L', (w, w))
    draw = ImageDraw.ImageDraw(alpha_layer)
    draw.ellipse((0, 0, w, w), fill=255)
    img_head.putalpha(alpha_layer)
    """组合图片"""
    back_ground.paste(img_head, (250, 10), alpha_layer)
    """user_name"""
    write_words = ImageDraw.ImageDraw(back_ground)
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'LXGWWenKaiMono-Regular.ttf'), 60)  # 设置字体属性
    w, h = set_Font.getsize(user_name)
    write_words.text(((640-w)/2, 150), user_name, fill="#FFFFFF", font=set_Font)
    """qq title level sex"""
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'LXGWWenKaiMono-Regular.ttf'), 30)  # 设置字体属性
    write_words.text((40, 300), f'qq号：{str(qq)}', fill="#FFFFFF", font=set_Font)
    write_words.text((40, 400), f'头衔：{title}', fill="#FFFFFF", font=set_Font)
    write_words.text((400, 300), f'性别：{sex}', fill="#FFFFFF", font=set_Font)
    write_words.text((400, 400), f'等级：{level}', fill="#FFFFFF", font=set_Font)
    """time"""
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'LXGWWenKaiMono-Regular.ttf'), 40)  # 设置字体属性
    write_words.text((40, 500), f'入群时间：{time}', fill="#FFFFFF", font=set_Font)
    """copyright"""
    cr = 'Copyright ©2020-2023 SakuraiSenrin, All Rights Reserved.'
    set_Font = ImageFont.truetype(os.path.join(
        os.getcwd(),  "Resources", 'Fonts', 'LXGWWenKaiMono-Regular.ttf'), 15)  # 设置字体属性
    w, h = set_Font.getsize(cr)
    write_words.text(((640-w)/2, 600), cr, fill="#FFFFFF", font=set_Font)
    imgaeBytes = BytesIO()
    back_ground.save(imgaeBytes,format="png")
    return imgaeBytes

async def get_water_card(member_info:List[tuple[int,str,int]]) -> BytesIO:
    """
        制作吹氵排行榜
    """
    color_list = [
        "#007bff",
        "#2b91ff",
        "#55a7ff",
        "#80bdff",
        "#aad3ff",
        "#000000"
    ]
    set_Font = ImageFont.truetype("./Resources/Fonts/LXGWWenKaiMono-Regular.ttf", 50)  # 设置字体属性
    _ = "Water Rank 今日吹水排行榜"
    x, y = set_Font.getsize(_)
    water_title = Image.new(mode='RGB', size=(800, 130), color="#FFFFFF")
    draw = ImageDraw.ImageDraw(water_title)
    draw.text(((800-x)/2, (130-y)/2), _, font=set_Font,fill=(0,0,0), direction=None)
    WaterList:List[Image.Image] = [water_title]
    if not member_info:
        _ = '   好冷，暂无吹水记录:(   '
        x, y = set_Font.getsize(_)
        image = Image.new(mode='RGB', size=(x, y), color="#19c2ff")
        draw = ImageDraw.ImageDraw(image)
        draw.text((0, 0), _, font=set_Font,fill=(255,255,255), direction=None)
        imgaeBytes = BytesIO()
        image.save(imgaeBytes,format="png")
        return imgaeBytes

    for i, _item in enumerate(member_info):
        i = i if i<=4 else 5
        font = "Regular" if i<=4 else "Bold"
        set_Font = ImageFont.truetype(f"./Resources/Fonts/LXGWWenKaiMono-{font}.ttf", 50)  # 设置字体属性
        qq = _item[0]
        user_name = _item[1]
        waterTimes = _item[2]
        name = user_name if len(user_name) <=10 else user_name[:10]+"..."

        async with AsyncClient(proxies={}) as Client:
            host_min = f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s=3'
            response_min = await Client.get(url=host_min)
            response_min = BytesIO(response_min.read())
        """虚化背景"""
        back_ground = Image.new(mode="RGB",size=(800,130), color=(255,255,255))
        """切圆头像"""
        w = 100
        img_head_open = Image.open(response_min)
        img_head = Image.new('RGBA', (w, w))
        img_head.paste(img_head_open)
        alpha_layer = Image.new('L', (w, w))
        draw = ImageDraw.ImageDraw(alpha_layer)
        draw.ellipse((0, 0, w, w), fill=255)
        img_head.putalpha(alpha_layer)
        """组合图片"""
        back_ground.paste(img_head, (40,15), alpha_layer)
        """添加文字"""
        write_words = ImageDraw.ImageDraw(back_ground)
        w1, h1 = set_Font.getsize(name)
        w2, h2 = set_Font.getsize(f'{waterTimes}次')
        write_words.text((150, (130-h1)/2), name, fill=color_list[i], font=set_Font)
        write_words.text((750-w2, (130-h1)/2), f'{waterTimes}次', fill=color_list[i], font=set_Font)
        WaterList.append(back_ground)

    Final_IMG = Image.new('RGB',(800,130*len(WaterList)))#最终拼接的图像的大小
    Y_left = 0
    Y_right = 130
    for _item in WaterList:
        Final_IMG.paste(_item,(0,Y_left,800,Y_right))
        Y_left += 130
        Y_right += 130
    Final_IMG.show()
    imgaeBytes = BytesIO()
    Final_IMG.save(imgaeBytes,format="png")
    return imgaeBytes

async def get_head_img(qq:int, size:int=640) -> bytes:
    async with AsyncClient(proxies={}) as Client:
        host_big = f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s={size}'
        response_big = await Client.get(url=host_big)
    return response_big.read()

async def makeGalImg(tag:str, index:int) -> BytesIO:
    """
        制作GalGme推荐图片
    """
    try:
        conn = sqlite3.connect("./Resources/db/gal.db")
        galdb = conn.cursor()
    except:
        raise FileNotFoundError("[文件缺失：Galgamedatabase]\ngal.db缺失，请检查项目完整性")
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

        set_Font = ImageFont.truetype(os.path.join(os.getcwd(),  "Resources", 'Fonts', 'LXGWWenKaiMono-Regular.ttf'), 50)  # 设置字体 属性

        a,b = background.size
        try:
            _ = Image.new("L", (a-80-w_s-180 ,h_s-17))  #可写字的区域
        except:
            raise RuntimeError('[处理错误：ImgBuilder]\nSenrin脑子坏了T_T，再来一次吧...')
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
        return imgaeBytes

async def makeLibImg(StudyPath:str) -> BytesIO:
    """
        制作词库集合图片
    """
    set_Font = ImageFont.truetype(os.path.join(os.getcwd(), "Resources", "Fonts", 'LXGWWenKaiMono-Regular.ttf'), 30)  # 设置字体属性
    with open(StudyPath, mode="r", encoding='utf-8-sig') as f:
        lib = '现有词库如下：\n'+f.read()
    x, _y = set_Font.getsize(max(lib.split('\n'), key=len))
    y, _x = set_Font.getsize((len(lib.split('\n'))*'00')) 
    image = Image.new(mode='RGB', size=(x, y), color=(255, 255, 255))
    draw = ImageDraw.ImageDraw(image)
    draw.text((0, 0), lib, font=set_Font,fill="#000000", direction=None)

    imgaeBytes = BytesIO()
    image.save(imgaeBytes,format="png")
    return imgaeBytes

class WordBankImg:

    def __init__(self) -> None:
        pass

    def security_text(self, text:str) -> str:
        from bbcode import Parser
        _ = Parser().tokenize(text)
        safe_text = ""
        for x in _:
            if x[0] != 4:
                safe_text += len(x[3]) * "*"
            else:
                safe_text += x[3]
        return safe_text


    def highlightText(
            self, 
            raw_text:str, 
            highlight_text:str, 
            font_size:int,
            highlight_color:ColorType = "#007bff"
    ) -> str:
        bbcode_text = ""
        _list = raw_text.split(highlight_text)

        for x in _list[:-1]:
            bbcode_text += x+f"[color={highlight_color}]{highlight_text}[/color]"
        else:
            bbcode_text += _list[-1]
        return f"[size={font_size}]{bbcode_text}[/size]"


    def wordBankItemImg(
            self,
            search_key:str, 
            find_key:str, 
            shuf_item_list:List[ReverseItem]
            ) -> Image.Image:
        safe_search_key = split_str(self.security_text(search_key)).strip()
        safe_find_key = split_str(self.security_text(find_key)).strip()
        title = self.highlightText(
            raw_text = safe_find_key, 
            highlight_text = safe_search_key, 
            font_size = 40
            )
        body = ""
        for shuf_item in shuf_item_list:
            for k in shuf_item.__dict__:
                v:str = getattr(shuf_item, k)
                if len(v) > 20:
                    v = v[:20] + "..."
                body += f"    {k}={v}\n"
            body += "\n"
        body = self.highlightText(
            raw_text = body,
            highlight_text= search_key,
            font_size = 30
        )
        b = f"{title}:\n{body}"
        return Text2Image.from_bbcode_text(b,fontname="./Resources/Fonts/LXGWWenKaiMono-Regular.ttf").to_image(bg_color="#FFFFFF")


    def concat_images_horizontally(self,image_list: List[Image.Image]) -> Image.Image:
        widths, heights = zip(*(i.size for i in image_list))
        new_image = Image.new('RGB', (sum(widths), max(heights)),color=(255,255,255))
        x_offset = 0
        for img in image_list:
            new_image.paste(img, (x_offset, 0))
            x_offset += img.width
        return new_image


    def concat_images_vertically(self, image_list: List[Image.Image]) -> Image.Image:
        widths, heights = zip(*(i.size for i in image_list))
        new_image = Image.new('RGB', (max(widths), sum(heights)),color=(255,255,255))
        y_offset = 0
        for img in image_list:
            new_image.paste(img, (0, y_offset))
            y_offset += img.height
        return new_image


    def concat_images(self, list_of_list_images: List[List[Image.Image]]) -> Image.Image:
        horizontal_images = [self.concat_images_horizontally(image_list) for image_list in list_of_list_images]
        final_image = self.concat_images_vertically(horizontal_images)
        return final_image


    def wordBankResultImg(
            self, 
            search_key:str, 
            result:List[List[Dict[str, List[ReverseItem]]]],
            page:int=0
        ) -> BytesIO:      # TODO
        return_bytes = BytesIO()
        word_item_list:List[Image.Image] = []
        word_to_img_list:List[List[Image.Image]]
        for i,items in enumerate(result[page]):
            for k,v in items.items():
                word_item_list.append(self.wordBankItemImg(search_key, f"{i+1}.{k}", v))
        word_to_img_list = split_list(word_item_list, int(math.sqrt(len(word_item_list))))
        page_detail_img = Text2Image.from_bbcode_text(f"当前页码：第 [color=#007bff]{page+1}[/color] 页， 共 [color=#007bff]{len(result)}[/color] 页",fontname="./Resources/Fonts/LXGWWenKaiMono-Regular.ttf",fontsize=50).to_image(bg_color=(255,255,255))
        word_to_img_list.append([page_detail_img])
        self.concat_images(word_to_img_list).save(return_bytes, format="png")
        return return_bytes