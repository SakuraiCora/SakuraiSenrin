import os
import re
import time
from httpx import AsyncClient
from nonebot.adapters.cqhttp.message import MessageSegment
from config import SAUCENAO_API as api_key
from config import PROXY

async def SauceNAO(numst, pic_url):  # 搜图结果，空则返回None，return示例：(1,NAO_result)
    if PROXY == "":
        PROXY_ = {}
    else:
        PROXY_ = PROXY
    async with AsyncClient(proxies=PROXY_) as Client:
        response = await Client.get(url=f"https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=1&api_key={api_key}&url={pic_url}")
    result = response.json()
    try:  # 从相关系数判断搜索结果是否存在
        similarity = float(result['results'][0]['header']['similarity'])
    except:
        return None
    else:
        if similarity < 50.0:
            return None
        fileName = f'{time.time()}SamplePic{numst+1}.jpg'
        SamplePath = f'.\\Resources\\SearchIMG\\{fileName}'
        pic_url = result['results'][0]['header']['thumbnail']
        if PROXY == "":
            PROXY_ = {}
        else:
            PROXY_ = PROXY
        async with AsyncClient(proxies=PROXY_) as Client:
            _get_sample = await Client.get(url=pic_url)
            get_sample = _get_sample.read()
            with open(file=SamplePath, mode='wb') as WS:
                WS.write(get_sample)
        pic_url = SamplePath    #完成处理后得到路径
        try:
            source = result['results'][0]['data']['source']
        except:
            source = '无相关信息'
        try:
            creator = result['results'][0]['data']['creator']
        except:
            creator = '无相关信息'
        if 'pixiv' in source:  # 不标准的pixiv来源
            pattern = re.compile(r'\d+')
            illust = pattern.findall(source)[0]
            NAO_result = (
                MessageSegment.text("检测到图源于Pixiv\n")
                +MessageSegment.image(f"file:///{pic_url}]\n")
                +MessageSegment.text(f'相似系数：{similarity}\n')
                +MessageSegment.text(f"插画画师：{creator}\n")
                +MessageSegment.text(f'插画ID：{illust}\n')
                +MessageSegment.text(f'Pixiv源址：{source}')
            )
        elif 'pixiv_id' in result['results'][0]['data']:  # 标准的pixiv来源
            creator = result['results'][0]['data']['member_name']
            source = result['results'][0]['data']['ext_urls'][0]
            illust = result['results'][0]['data']['pixiv_id']
            title = result['results'][0]['data']['title']
            NAO_result = (
                MessageSegment.text("检测到图源于Pixiv\n")
                +MessageSegment.image(f"file:///{pic_url}]\n")
                +MessageSegment.text(f'相似系数：{similarity}\n')
                +MessageSegment.text(f'插画名称：{title}\n')
                +MessageSegment.text(f"插画画师：{creator}\n")
                +MessageSegment.text(f'插画ID：{illust}\n')
                +MessageSegment.text(f'Pixiv源址：{source}')
            )
        else:  # 其他来源
            source = result['results'][0]['data']['ext_urls'][0]
            NAO_result = (
                MessageSegment.image(f"file:///{pic_url}]\n")
                +MessageSegment.text(f'相似系数：{similarity}\n')
                +MessageSegment.text(f'图片作者：{creator}\n')
                +MessageSegment.text(f'图片源址：{source}')
            )
        return (numst+1, NAO_result)
