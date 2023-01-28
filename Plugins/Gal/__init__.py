"""
    GalRecommend V2.0 包含的功能
    1.来自恋爱游戏网的随机Galgame推荐
    2.来自恋爱游戏网的定向Galgame推荐
"""
import random
import sqlite3

from io import BytesIO
from Utils.CustomRule import check_white_list
from Utils.ImageUtils import makeGalImg
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.plugin import on_command
from nonebot.adapters.onebot.v11.message import MessageSegment

conn = sqlite3.connect("./Resources/db/gal.db")
galdb = conn.cursor()
st = ['3D', 'ACT', 'NTR', 'RPG', '三角关系', '传奇', '伪娘', '偶像', '催泪', '傲娇', '公主', '养成', '兽耳', '内涵', '冒险', '剧情', '双子', '变身', '另类', '同居', '后宫', '吸血鬼', '和风', '咖啡店', '喜剧', '国产', '复仇', '夏', '大小姐', '天使', '奇幻', '女仆', '女性向', '女性视角', '女战士', '女神', '女装', '妹系', '姐妹', '姐系', '学园', '岛', '巫女', '幻想', '开店', '异世界', '御姐', '怪物', '怪物娘', '恋爱', '恶魔', '悬疑', '悬疑推理', '战斗', '护士', '探险', '新娘', '末世', '机器人', '架空世界', '校园', '模拟养成', '模拟经营', '治愈', '灵异', '猎奇', '甜作', '田园', '电波作', '病娇', '百合', '社团', '科学幻想', '科幻', '穿越', '童话', '策略', '纯爱', '网络世界', '美少女养成游戏', '老师', '职场', '致郁', '萝莉', '蒸汽朋克', '蔷薇向', '解谜', '超能力', '轮回', '近未来', '重口', '青春', '青梅竹马', '音乐', '馆', '魔女', '魔幻', '魔法', '魔法少女', '魔物娘', '黑暗向']

Random_Gal = on_command('gal', priority=5, rule=check_white_list())  # gal random
Tag_List = on_command('taglist', priority=5, rule=check_white_list())

@Random_Gal.handle()
async def RDL(event: MessageEvent):
    args = str(event.get_message()).split(" ")
    if len(args) > 1:
        if args[1] == 'random':
            tag = st[random.randint(0,len(st)-1)]
        elif args[1] == 'tag':
            try:
                tag = args[2]
                if tag not in st:
                    raise Exception
            except:
                await Random_Gal.finish("[参数错误:args]\n传入参数过少或错误，请发送#help RGAL查看帮助文档")
        else:
            await Random_Gal.finish("[参数错误:args]\n传入参数过少或错误，请发送#help RGAL查看帮助文档")
        sql = f"SELECT COUNT(*) FROM '{tag}'"
        res = galdb.execute(sql).fetchone()[0]
        index = random.randint(1,int(res))
        await Random_Gal.send("[RandomGal正常:Succeed]\nちょっと待ってください......")
        msg =  await makeGalImg(tag,index)
        await Random_Gal.finish(MessageSegment.image(msg))
    else:
        await Random_Gal.finish("[参数错误:args]\n传入参数过少或错误，请发送#help RGAL查看帮助文档")



@Tag_List.handle()
async def TAG():
    await Tag_List.send("[RandomGal正常:Succeed]\nちょっと待ってください......")
    with open("./Resources/tag.png", 'rb') as f:
        img:bytes = f.read()
    await Tag_List.finish(MessageSegment.image(BytesIO(img)))