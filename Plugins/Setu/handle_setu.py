import os
import asyncio
import random
import aiohttp
from nonebot.adapters.cqhttp.message import MessageSegment, Message
from httpx import AsyncClient
from config import LOLICON_API, SETU_PATH, PROXY

async def get_setu(modle, level, num, key) -> tuple[bool,list[Message]]:  # 定义获取函数，返回为tuple，bool为是否重置CD，list包含涩图数据
    download_urls = []
    setu:tuple[bool,list[Message]] = (True,[])
    if modle == 'random':
        post_data = {"apikey": LOLICON_API, "r18": level, "num": num}
    elif modle == 'search':
        post_data = {"apikey": LOLICON_API, "keyword": key, "num": num}
    else:
        post_data = {}
    async with AsyncClient(proxies={}) as Client:
        host = "http://api.lolicon.app/setu/v2/"
        response = await Client.get(url=host, params=post_data)
        result = response.json()
    if len(result['data']) == 0:
        setu = (False,[Message(f'悲！没有符合条件的涩图：{key}')])
    else:
        quota = '∞'
        for one in result['data']:
            img_url, title, author, pixivID = one['urls']['original'], one['title'], one['author'], one['pid']
            tags = one['tags']
            all_tag = ''
            for tag in tags:
                all_tag += f"{tag} "
            PicName = img_url.split("/")[-1]
            if '.jpg' in PicName:
                PicName = PicName.replace('.jpg','.png')
            way = os.path.join(SETU_PATH, PicName)
            download_urls.append((way,img_url))
            msg = (
                MessageSegment.image(f"file:///{way}")
                +MessageSegment.text(f"\n插画名称：{title}\n")
                +MessageSegment.text(f"插画作者：{author}\n")
                +MessageSegment.text(f"插画ID:{pixivID}\n")
                +MessageSegment.text(f"tags：{all_tag}\n")
                +MessageSegment.text(f"剩余调用次数：{quota}"))
            setu[1].append(msg)

        async def job(_way, session, url):
            get_pic = await session.get(url, proxy=PROXY)
            get_pic = await get_pic.read()
            with open(_way, "wb") as ffs:
                ffs.write(get_pic)
            return str(url)

        async def main(loop, URL, num):
            async with aiohttp.ClientSession() as session:
                num = len(URL)
                tasks = [loop.create_task(job((URL[RR][0]), session, (URL[RR])[1]))
                        for RR in range(num)]
                await asyncio.sleep(0.1)
                await asyncio.gather(*tasks)
        loop = asyncio.get_event_loop()
        await main(loop, download_urls, num)
    return setu

async def random_setu(Rmodle, level, num) -> tuple[bool,list[Message]]:  # 随机涩图函数封装
    if Rmodle == 'regex':
        pixivID = random.choice(os.listdir(SETU_PATH))
        way = os.path.join(SETU_PATH, pixivID)  # 从本地库整一个
        setu = (True,[Message(MessageSegment.image(f"file:///{way}"))])
    else:
        modle = 'random'
        setu = await get_setu(modle=modle, level=level, num=num, key=None)
    return setu

async def search_setu(Keywords, num) -> tuple[bool,list[Message]]:  # 定向涩图函数封装
    modle = 'search'
    setu = await get_setu(modle=modle, level=None, num=num, key=Keywords)
    return setu