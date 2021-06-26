"""
    GalRecommend包含的功能
    1.来自恋爱游戏网的随机Galgame推荐
    2.来自恋爱游戏网的定向Galgame推荐
"""
from costrule import check_white_list_all
import random
import os
from httpx import AsyncClient
from bs4 import BeautifulSoup
from nonebot.adapters.cqhttp import Bot
from nonebot.adapters.cqhttp.event import Event, MessageEvent
from nonebot.plugin import on_command
from nonebot.adapters.cqhttp.message import Message
st = ['悬疑推理', '奇幻', '青梅竹马', 'RPG', '探险', '传奇', '学园', '恋爱', '女性向', '猎奇', 'NTR', '致郁', '过激', '后宫', '妹系', '同居', '女性视角', '喜剧', '机器人', '大小姐', '魔法', '魔物娘', '萝莉', '近未来', '校园', '社团', '战斗', '科幻', '女装', '馆', '女仆', '病娇', '老师', '岛', '纯爱', '青春', '百合', '护士', '穿越', '策略', '模拟经营', '姐妹', '兽耳', '田园', '职场', '偶像', '御姐', '冒险', '怪物娘', '女神', '巫女', '解谜', '幻想', '公主', '新娘',
      '美少女养成游戏', '科学幻想', '鬼畜', '内涵', '异世界', '养成', '黑暗向', '悬疑', '国产', '妻', '模拟养成', '催泪', '架空世界', '3D', '双子', '天使', '甜作', '伪娘', '重口', '夏', '治愈', '女子＊＊', '姐系', '超能力', '恶魔', 'ACT', '三角关系', '魔女', '魔法少女', '怪物', '女战士', '开店', '吸血鬼', '咖啡店', '音乐', '末世', '和风', '魔幻', '蔷薇向', '轮回', '傲娇', '灵异', '禁忌恋', '另类', '变身', '复仇', '电波作', '童话', '未亡人', '蒸汽朋克', '网络世界', '剧情', '青涩']

Random_Gal = on_command(
    'gal', priority=5, rule=check_white_list_all())  # gal random
Tag_List = on_command('taglist', priority=5, rule=check_white_list_all())


async def get_img(pic_url):
    async with AsyncClient(proxies={}) as Client:
        _get_sample = await Client.get(url=pic_url)
        get_sample = _get_sample.read()
        with open(file=os.path.join(os.getcwd(), 'Data_Base\\SamplePicGal.jpg'), mode='wb') as WS:
            WS.write(get_sample)
    pic_url = os.path.join(os.getcwd(), 'Data_Base\\SamplePicGal.jpg')
    return pic_url


async def get_random_game(Client, event):  # 随机galgame推荐
    rd = str(random.randint(20000, 300000))
    url = "https://www.lianaiyx.com/e/search/result/?searchid={}".format(rd)
    res = await Client.get(url)
    txt = res.text
    soup = BeautifulSoup(txt, "html.parser")
    h2s = soup.find_all("a", class_="img")
    rdh2s = random.sample(h2s, 1)
    for h in rdh2s:
        # 获取连接
        href = h.get("href")         # 第二级界面
        rs1 = await Client.get(href)
        rs1.encoding = 'utf-8'
        tx2 = rs1.text
        soup1 = BeautifulSoup(tx2, "html.parser")
        h22 = soup1.find("h1", class_="yh")
        img_get = soup1.find("div", class_="pagePic l")
        img2 = img_get.find("img")
        img2 = img2.attrs["src"]
        img2 = await get_img(pic_url=f'https://www.lianaiyx.com{img2}')
        name = h22.text  # 获取游戏名
        divs = soup1.find_all("div", class_="arcDES fix pt8")
        j = divs[-1]
        jian1 = j.text  # 获取简介1
        div2s = soup1.find("div", class_="pageBody wwbrk")
        jian2 = div2s.text  # 获取简介2
        jian = jian1 + jian2
        if len(jian) >= 200:
            jian = jian[:200]+"\n......（后略）"
        mg = (
            f"[CQ:at,qq={event.user_id}]\n"
            "来自恋网的随机推荐\n"
            f"[CQ:image,file=file:///{img2}]\n"
            f"{name}\n{jian}"
        )
        return mg


async def get_tag_game(Client, tag, event):  # 标签galgame推荐
    if tag in st:
        url = f"https://www.lianaiyx.com/e/tags/index.php?page=0&tagname={tag}"
        res = await Client.get(url)
        txt = res.text
        soup = BeautifulSoup(txt, "html.parser")
        uls = soup.find("ul", class_="ulPic l")
        ass = uls.find_all("a", class_="img")
        ass = random.sample(ass, 1)
        mg = '悲！出现了蜜汁错误......'
        for a in ass:
            # 获取连接
            href = a.get("href")
            # 第二级界面
            rs1 = await Client.get(href)
            rs1.encoding = 'utf-8'
            tx2 = rs1.text
            soup1 = BeautifulSoup(tx2, "html.parser")
            h22 = soup1.find("h1", class_="yh")
            img_get = soup1.find("div", class_="pagePic l")
            img2 = img_get.find("img")
            img2 = img2.attrs["src"]
            img2 = await get_img(pic_url=f"https://www.lianaiyx.com{img2}")
            name = h22.text  # 获取游戏名
            divs = soup1.find_all("div", class_="arcDES fix pt8")
            j = divs[-1]
            jian1 = j.text  # 获取简介1
            div2s = soup1.find("div", class_="pageBody wwbrk")
            jian2 = div2s.text  # 获取简介2
            jian = jian1+jian2
            if len(jian) >= 200:
                jian = jian[:200]+"\n......（后略）"
            pass
            mg = (
                f"[CQ:at,qq={event.user_id}]\n"
                "来自恋网的随机推荐\n"
                f"[CQ:image,file=file:///{img2}]\n"
                f"{name}\n{jian}"
            )
    else:
        mg = (
            f"悲！暂无“{tag}”这个tag......\n"
            "请根据tag列表来选择tag！\n"
            "至于tag列表嘛，请发送 #taglist 来查看~"
        )
    return mg


@Random_Gal.handle()
async def RDL(bot: Bot, event: Event):
    args = str(event.get_message()).split()
    if isinstance(event, MessageEvent):
        if args:
            if args[0] == 'random':
                await Random_Gal.send('Zer0折寿中......')
                async with AsyncClient() as Client:
                    mg = await get_random_game(Client=Client, event=event)
                await Random_Gal.finish(Message(mg))
            elif args[0] == 'tag':
                try:
                    tag = args[1]
                except:
                    await Random_Gal.finish(Message(f"[CQ:at,qq={event.user_id}]传入了不正确的参数......\n然后指令坏掉了，Zer0处理了个寂寞"))
                else:
                    await Random_Gal.send('Zer0折寿中......')
                    async with AsyncClient() as Client:
                        mg = await get_tag_game(Client=Client, tag=tag, event=event)
                    await Random_Gal.finish(Message(mg))
            else:
                await Random_Gal.finish(Message(f"[CQ:at,qq={event.user_id}]传入了不正确的参数......\n然后指令坏掉了，Zer0处理了个寂寞"))
        else:
            await Random_Gal.finish(Message(f"[CQ:at,qq={event.user_id}]传入了不正确的参数......\n然后指令坏掉了，Zer0处理了个寂寞"))


@Tag_List.handle()
async def TAG(bot: Bot, event: Event):
    await Tag_List.finish("tag信息列表：\n 3D ACT NTR RPG 傲娇 百合 变身 病娇 策略 超能力 传奇 穿越 纯爱 催泪 大小姐 岛 电波作 恶魔 复仇 公主 怪物 怪物娘 馆 鬼畜 国产 过激 和风 黑暗向 后宫 护士 幻想 机器人 架空世界 姐妹 解谜 姐系 禁忌恋 近未来 剧情 咖啡店 开店 科幻 科学幻想 老师 恋爱 猎奇 另类 灵异 轮回 萝莉 冒险 美少女养成游戏 妹系 魔法 魔法少女 魔幻 模拟经营 模拟养成 魔女 末世 魔物娘 内涵 女仆 女神 女性视角 女性向 女战士 女装 女子＊＊ 偶像 妻 奇幻 蔷薇向 青春 青梅竹马 青涩三角关系 社团 兽耳 双子 探险 天使 田园 甜作 童话 同居 网络世界 伪娘 未亡人 巫女 喜剧 吸血鬼 夏 校园 新娘 悬疑 悬疑推理 学园 养成 异世界 音乐 御姐战斗 蒸汽朋克 职场 治愈 致郁 重口")
