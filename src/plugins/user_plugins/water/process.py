import asyncio
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

from httpx import AsyncClient
from jinja2 import Template
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed

from plugins.user_plugins.water.database import WaterInfo


async def generate_water_rank_image_by_pillow(
    bot: Bot, group_id: str, water_info_sqeuence: Sequence[WaterInfo]
) -> Message:
    water_info_list = [
        {
            "user_id": i.user_id,
            "group_id": i.group_id,
            "created_at": i.created_at.isoformat(),
        }
        for i in water_info_sqeuence
    ]
    BG_COLOR = (255, 217, 222)  # #ffd9de
    TEXT_COLOR = (180, 76, 76)  # #b44c4c
    ITEM_BG_COLOR = (255, 240, 245)  # #fff0f5
    WIDTH = 800
    PADDING = 30

    img = Image.new("RGB", (WIDTH, 2000), BG_COLOR)
    draw = ImageDraw.Draw(img)
    y = PADDING

    try:
        title_font = ImageFont.truetype("./resources/fonts/LXGW_NERD_NOTO.ttf", 36)
        text_font = ImageFont.truetype("./resources/fonts/LXGW_NERD_NOTO.ttf", 24)
        small_font = ImageFont.truetype("./resources/fonts/LXGW_NERD_NOTO.ttf", 20)
    except Exception:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    group_name = username = group_name = (
        await bot.get_group_info(group_id=int(group_id))
    ).get("group_name")

    title = f"「{group_name}」水王排行榜"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        ((WIDTH - title_bbox[2]) // 2, y), title, fill=TEXT_COLOR, font=title_font
    )
    y += title_bbox[3] + 40

    today = datetime.now().strftime("%Y-%m-%d")
    today_messages = [
        m
        for m in water_info_list
        if m["created_at"].startswith(today) and m["group_id"] == group_id
    ]

    user_message_count = {}
    for msg in today_messages:
        user_message_count[msg["user_id"]] = (
            user_message_count.get(msg["user_id"], 0) + 1
        )
    today_king = max(user_message_count.items(), key=lambda x: x[1], default=None)

    group_counts = {}
    for msg in water_info_list:
        group_counts[msg["group_id"]] = group_counts.get(msg["group_id"], 0) + 1
    sorted_groups = sorted(group_counts.items(), key=lambda x: -x[1])
    group_rank = next(
        i + 1 for i, (gid, _) in enumerate(sorted_groups) if gid == group_id
    )

    king_text = (
        f"今日水王: {
            (await get_user_name(bot, group_id=int(group_id), user_id=today_king[0]))
        } ({today_king[1]}次)"
        if today_king
        else "无"
    )
    rank_text = f"本群排名: 第{group_rank}名"

    for text in [king_text, rank_text]:
        draw.text((PADDING, y), text, fill=TEXT_COLOR, font=text_font)
        y += 40

    y += 20

    user_total = {}
    for msg in water_info_list:
        if msg["group_id"] == group_id:
            user_total[msg["user_id"]] = user_total.get(msg["user_id"], 0) + 1
    sorted_users = sorted(user_total.items(), key=lambda x: -x[1])[:10]

    item_height = 100
    chart_width = 300

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_avatar(user_id: str, client: AsyncClient) -> tuple[str, bytes]:
        return user_id, (
            await client.get(f"https://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100")
        ).read()

    async with AsyncClient(verify=False) as client:
        avatars = dict(
            await asyncio.gather(
                *[
                    asyncio.create_task(get_avatar(user_id, client))
                    for user_id in set(user_total.keys())
                ]
            )
        )

    for rank, (user_id, count) in enumerate(sorted_users, 1):
        draw.rounded_rectangle(
            (PADDING, y, WIDTH - PADDING, y + item_height),
            radius=15,
            fill=ITEM_BG_COLOR,
        )

        try:
            avatar_res = avatars[user_id]
            avatar = Image.open(BytesIO(avatar_res))
        except Exception:
            avatar = Image.new("RGB", (60, 60), (200, 200, 200))

        mask = Image.new("L", (60, 60), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 60, 60), fill=255)
        avatar = avatar.resize((60, 60)).convert("RGB")
        avatar.putalpha(mask)

        img.paste(avatar, (PADDING + 15, y + 20), avatar)

        username = await get_user_name(bot, group_id=int(group_id), user_id=user_id)
        text_y = y + 20
        draw.text(
            (PADDING + 100, text_y),
            f"{rank}. {username}",
            fill=TEXT_COLOR,
            font=text_font,
        )
        draw.text(
            (PADDING + 100, text_y + 40),
            f"发言次数: {count}",
            fill=TEXT_COLOR,
            font=small_font,
        )

        chart_img = generate_tile_chart(
            get_hourly_counts(water_info_list, user_id, group_id),
            chart_width,
            50,
            TEXT_COLOR,
        )
        img.paste(chart_img, (WIDTH - PADDING - chart_width - 15, y + 25))

        y += item_height + 20

    now = datetime.now()
    footer = [
        f"© 2020-{now.year} SakuraiSenrin. All rights reserved.",
        f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    for text in footer:
        draw.text((PADDING, y), text, fill=TEXT_COLOR, font=small_font)
        y += 30
    bytes_io = BytesIO()
    img = img.crop((0, 0, WIDTH, y + 30))
    img.save(bytes_io, format="PNG")
    return Message(MessageSegment.image(bytes_io))


async def get_user_name(bot: Bot, user_id: int, group_id: Optional[int] = None):
    if group_id:
        try:
            return (
                await bot.get_group_member_info(group_id=int(group_id), user_id=user_id)
            )["nickname"]
        except Exception:
            pass
    try:
        return (await bot.get_stranger_info(user_id=user_id))["nickname"]
    except Exception:
        return "未知用户"


def get_hourly_counts(water_info, user_id, group_id):
    counts = [0] * 24
    for msg in water_info:
        if msg["user_id"] == user_id and msg["group_id"] == group_id:
            hour = datetime.fromisoformat(msg["created_at"]).hour
            counts[hour] += 1
    return counts


def generate_tile_chart(data, width=300, height=90, base_color=(180, 76, 76)):
    """
    生成24小时瓷砖墙图表
    :param data: 24小时数据列表 [0-23]
    :param width: 图表宽度（推荐至少300px）
    :param height: 图表高度（推荐至少90px）
    :param base_color: 基准颜色 RGB元组
    :return: PIL Image对象
    """
    rows = 2
    cols = 12
    tile_spacing = 2
    max_alpha = 255
    min_alpha = 30

    tile_width = (width - (cols - 1) * tile_spacing) // cols
    tile_height = (height - (rows - 1) * tile_spacing) // rows

    img = Image.new("RGB", (width, height + 10), (255, 240, 245))
    draw = ImageDraw.Draw(img, "RGBA")

    max_count = max(data) or 1

    def get_alpha(count):
        return int(min_alpha + (max_alpha - min_alpha) * (count / max_count))

    for hour in range(24):
        row = hour // cols
        col = hour % cols

        x0 = col * (tile_width + tile_spacing)
        y0 = row * (tile_height + tile_spacing)
        x1 = x0 + tile_width
        y1 = y0 + tile_height

        alpha = get_alpha(data[hour])

        draw.rectangle(
            [x0, y0, x1, y1],
            fill=(*base_color, alpha),
            outline=(*base_color, 100),
            width=1,
        )

        label = str(hour).rjust(2, "0")
        font = ImageFont.load_default()
        text_width, text_height = font.getbbox(label)[2:]
        draw.text(
            (
                x0 + (tile_width - text_width) // 2,
                y0 + (tile_height - text_height) // 2,
            ),
            label,
            fill=(*base_color, min(alpha + 100, 255)),
            font=font,
        )

    return img


async def generate_water_rank_image_by_playwright(
    group_id: str, water_info_list: Sequence[WaterInfo]
) -> Message:
    with open(
        Path(__file__).parent / "water_rank_template.html", "r", encoding="utf-8"
    ) as f:
        template_string = f.read()
    template = Template(template_string)
    rendered_html = template.render(
        group_id=group_id,
        water_info_list=[
            {
                "user_id": i.user_id,
                "group_id": i.group_id,
                "created_at": i.created_at.isoformat(),
            }
            for i in water_info_list
        ],
    )
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.set_content(rendered_html)
            await page.wait_for_load_state("networkidle")
            message = Message(
                MessageSegment.image(await page.screenshot(full_page=True))
            )
        except Exception as e:
            await page.close()
            await browser.close()
            message = Message(MessageSegment.text(f"截图失败：{e}"))
        finally:
            await page.close()
            await browser.close()
        return message
