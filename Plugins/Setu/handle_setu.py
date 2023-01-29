import os
import asyncio
import random
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from httpx import AsyncClient
from botConfig import LOLICON_API, SETU_PATH, PROXY

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
        response = await Client.get(url=host, params=post_data, follow_redirects=True)
        result = response.json()
    if len(result['data']) == 0:
        setu = (False,[Message(f'悲！没有符合条件的涩图：{key}')])
    else:
        quota = '∞'
        for one in result['data']:
            img_url, title, author, pixivID = one['urls']['original'], one['title'], one['author'], one['pid']
            all_tag = ' '.join(one['tags'])
            PicName = img_url.split("/")[-1]
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

        async def job(_way, session:AsyncClient, url):
            get_pic = (await session.get(url)).read()
            with open(_way, "wb") as ffs:
                ffs.write(get_pic)
            return str(url)

        async def main(loop, URL, num):
            PROXY_ = PROXY if PROXY else {}
            async with AsyncClient(proxies=PROXY_) as client:
                num = len(URL)
                tasks = [loop.create_task(job((URL[RR][0]), client, (URL[RR])[1])) for RR in range(num)]
                await asyncio.sleep(0.1)
                await asyncio.gather(*tasks)
        loop = asyncio.get_event_loop()
        await main(loop, download_urls, num)
    return setu

async def random_setu(Rmodle, level, num) -> tuple[bool,list[Message]]:  # 随机涩图函数封装
    if Rmodle == 'regex':
        img = []
        for _ in range(num):
            pixivID = random.choice(os.listdir(SETU_PATH))
            way = os.path.join(SETU_PATH, pixivID)  # 从本地库整一个
            img.append(Message(MessageSegment.image(f"file:///{way}")))
        setu = (True,img)
    else:
        modle = 'random'
        setu = await get_setu(modle=modle, level=level, num=num, key=None)
    return setu

async def search_setu(Keywords, num) -> tuple[bool,list[Message]]:  # 定向涩图函数封装
    modle = 'search'
    setu = await get_setu(modle=modle, level=None, num=num, key=Keywords)
    return setu