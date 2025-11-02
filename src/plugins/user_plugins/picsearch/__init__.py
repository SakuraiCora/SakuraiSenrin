from httpx import AsyncClient
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11.helpers import Cooldown, CooldownIsolateLevel
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Arg
from nonebot.plugin import PluginMetadata, on_fullmatch
from PicImageSearch import Network, SauceNAO

from src.config.general_config import general_config
from src.plugins.user_plugins.picsearch.config import picsearch_config
from src.utils.enmus import PluginPermissionEnum, TriggerTypeEnum
from src.utils.message_builder import NoticeBuilder

name = "图片搜索"
description = """
图片搜索:
  搜图
""".strip()

usage = f"""
📖 ===== {name} =====

命令前缀: 无

1.搜图 🔍
  回复包含有图片的消息，即可搜索对应图片，冷却时间 30s

⚠️ 注意事项:
1. 搜索结果中可能包含有不安全的图片，请自行判断是否合适。
2. 如果有多张图片，可以使用空格分割序号，最多允许 3 张图片。
3. 如需进一步支持，请联系管理员，或加入反馈群「{general_config.support_group_id}」💬。
""".strip()


__plugin_meta__ = PluginMetadata(
    name=name,
    description=description,
    usage=usage,
    extra={
        "author": "SakuraiCora",
        "version": "0.1.0",
        "trigger": TriggerTypeEnum.ACTIVE,
        "permission": PluginPermissionEnum.EVERYONE,
    },
)

picsearch_matcher = on_fullmatch(
    ("搜图"),
    ignorecase=True,
    priority=5,
    block=False,
)


@picsearch_matcher.handle(
    parameterless=[
        Cooldown(
            cooldown=30,
            isolate_level=CooldownIsolateLevel.USER,
            prompt=NoticeBuilder.warning("冷却时间 30s，请耐心等待 qwq"),
        )
    ]
)
async def _(event: MessageEvent, matcher: Matcher):
    if not event.reply:
        await picsearch_matcher.finish()
    picture_message = Message()
    for segment in event.reply.message:
        if segment.type == "image":
            picture_message += segment
    if len(picture_message) == 1:
        matcher.set_arg("index", Message("1"))
    matcher.set_arg("picture", picture_message)


@picsearch_matcher.got(
    "index",
    prompt="检测到有多张图片，请输入对应的序号，最多允许 3 张，可以使用空格进行分割：",
)
async def _(matcher: Matcher, index: Message = Arg()):
    if not (picutre_message := matcher.get_arg("picture")):
        await picsearch_matcher.finish()
    if len((index_message := index.extract_plain_text().split(" "))) > 3:
        await picsearch_matcher.reject(
            NoticeBuilder.warning("最多允许 3 张图片，请重新输入。")
        )

    result_message = Message("SauceNAO 搜索结果：\n")
    for index_text in index_message:
        await picsearch_matcher.send(
            NoticeBuilder.info(f"正在搜索第 {index_text} 张图片，请稍后...")
        )
        async with Network(proxies=general_config.proxy) as network:
            resp = await SauceNAO(
                api_key=picsearch_config.saucenao_api_key, client=network
            ).search(url=picutre_message[int(index_text) - 1].data["url"])
        if resp.status_code == 200 and resp.raw:
            search_result = resp.raw[0]
            async with AsyncClient(proxy=general_config.proxy) as client:
                thumbnail_bytes = (await client.get(search_result.thumbnail)).read()
            result_message += (
                Message.template(
                    (
                        f"第 {index_text} 张图片搜索结果：\n"
                        "{}\n"
                        f"相似度：{search_result.similarity}%\n"
                        f"标题：{search_result.title}\n"
                        f"作者：{search_result.author}\n"
                        f"图片链接：{search_result.source}"
                    )
                )
            ).format(MessageSegment.image(thumbnail_bytes))
    await picsearch_matcher.finish(result_message, reply_message=True)
