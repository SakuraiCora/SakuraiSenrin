import asyncio
import base64
import io
import json
import random
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from httpx import AsyncClient
from jinja2 import Template
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_fixed

from src.config.general_config import general_config
from src.utils.common_helper import CommonHelper
from src.utils.enums import WordbankExtraActionEnum

from .cache import image_cache
from .config import wordbank_config
from .database import Response, WordbankFTS


def message_to_string(message: Message):
    final_message_list = []
    image_url_list = []
    message_length = 0
    for segment in message:
        match segment.type:
            case "image":
                file = segment.data["file"]
                url = f"https://raw.githubusercontent.com/SakuraiCora/SakuraiSenrinPic/main/img/{file}"
                final_message_list.append(
                    {
                        "type": "image",
                        "file": file,
                        "url": url,
                    }
                )
                image_url_list.append((file, segment.data.get("url", url)))
                message_length += 20
            case "text":
                final_message_list.append(
                    {"type": "text", "text": segment.data["text"]}
                )
                message_length += len(segment.data["text"])
            case "face":
                final_message_list.append({"type": "face", "id": segment.data["id"]})
                message_length += 1
            case "at":
                final_message_list.append({"type": "at", "qq": segment.data["qq"]})
                message_length += 1
            case _:
                pass
    return (
        json.dumps(final_message_list, ensure_ascii=False),
        message_length,
        image_url_list,
    )


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3), reraise=True)
async def string_to_message(message_string: str) -> Message:
    message_list = json.loads(message_string)
    message = Message()
    for item in message_list:
        match item["type"]:
            case "image":
                if not (img := image_cache.get_image(item["url"])):
                    img = (
                        await AsyncClient(proxy=general_config.proxy, verify=False).get(
                            item["url"]
                        )
                    ).read()
                    image_cache.set_image(item["url"], img)
                message_segment = MessageSegment.image(img)
                message.append(message_segment)
            case "text":
                message.append(MessageSegment.text(item["text"]))
            case "face":
                message.append(MessageSegment.face(item["id"]))
            case "at":
                message.append(MessageSegment.at(item["qq"]))
            case _:
                pass

    return message


async def process_extra_info(user_id: str, extra_info: dict) -> Message:
    return_message = Message()
    match extra_info.get("action"):
        case WordbankExtraActionEnum.AT_MENTIONED.value:
            return_message.append(MessageSegment.at(user_id))
        case WordbankExtraActionEnum.POKE_MENTIONED.value:
            return_message.append(MessageSegment.at(user_id))
        case WordbankExtraActionEnum.GROUP_JOIN.value:
            return_message.append(MessageSegment.text(wordbank_config.append_message))
            return_message.append(MessageSegment.at(user_id))
            return_message.append(
                MessageSegment.image(await CommonHelper.get_qq_avatar(user_id))
            )
        case WordbankExtraActionEnum.GROUP_LEAVE.value:
            return_message.append(MessageSegment.text(user_id))
            return_message.append(
                MessageSegment.image(await CommonHelper.get_qq_avatar(user_id))
            )
        case _:
            pass

    return return_message


@retry(stop=stop_after_attempt(3), wait=wait_fixed(3), reraise=True)
async def upload_image_to_github(filename: str, image_url: str):
    if image_cache.check_image(filename):
        return
    headers = {
        "Authorization": f"Bearer {general_config.gist_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json",
    }

    response = await AsyncClient(verify=False).get(
        image_url.replace("https://", "http://", 1)
    )
    image_content = response.read()

    await AsyncClient(proxy=general_config.proxy, verify=False).put(
        url=f"https://api.github.com/repos/SakuraiCora/SakuraiSenrinPic/contents/img/{filename}",
        json={
            "message": "file",
            "content": base64.b64encode(image_content).decode(),
        },
        headers=headers,
        timeout=20,
    )
    image_cache.set_image(filename, image_content)


def select_random_response(responses: List[Response]) -> Optional[Response]:
    """
    根据响应的权重随机选择一个响应

    :param responses: 响应列表，每个响应包含一个 "weight" 属性，例如:
                        [
                            {"response": "Response 1", "weight": 1},
                            {"response": "Response 2", "weight": 3},
                            {"response": "Response 3", "weight": 2}
                        ]
    :return: 根据权重随机选择的响应字典，如果没有找到则返回 None
    """
    if not responses:
        return None

    weights = [response.weight for response in responses]
    items = [response for response in responses]

    selected_response = random.choices(items, weights=weights, k=1)

    return selected_response[0]


def find_first_matching_response(
    response_list: Dict[int, List[Response]], current_state: Dict[str, Any]
) -> List[Response]:
    """
    查找符合当前状态的所有响应，按照优先级顺序。
    如果在某个优先级中找到符合规则的响应，则匹配完当前优先级下的所有项后，
    停止检查后续优先级。

    :param response_list: 优先级字典，例如 {1: [...], 2: [...], ...}
    :param current_state: 当前状态的字典，例如 {"group_id": 123, "user_id": 456, "at_metioned": True}
    :return: 符合规则的响应字典，如果没有找到则返回 None
    """
    matching_responses: List[Response] = []

    for priority in sorted(response_list.keys()):
        responses = response_list[priority]

        has_matched = False

        for response in responses:
            if not response.availability:
                continue
            rule = response.response_rule_conditions
            if is_rule_valid(current_state, rule):
                matching_responses.append(response)
                has_matched = True

        if has_matched:
            break

    return matching_responses


def is_rule_valid(current_state: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    检查当前状态是否符合给定规则，支持复杂的比较操作和逻辑操作符

    :param current_state: 当前状态的字典。包含需要验证的键值对，例如：
        {
            "count": 150,
            "group_id": 123,
            "user_id": 456,
            "username": "test_name",
            "age": 20
        }

    :param rule: 规则字典。可以包含嵌套的逻辑操作符以及比较操作符。支持以下操作符：
        - "$eq": 等于操作符，检查值是否等于指定值。
            例如：{"user_id": {"$eq": 456}} 检查 "user_id" 是否等于 456。

        - "$ne": 不等于操作符，检查值是否不等于指定值。
            例如：{"user_id": {"$ne": 456}} 检查 "user_id" 是否不等于 456。

        - "$gt": 大于操作符，检查值是否大于指定值。
            例如：{"count": {"$gt": 100}} 检查 "count" 是否大于 100。

        - "$lt": 小于操作符，检查值是否小于指定值。
            例如：{"count": {"$lt": 200}} 检查 "count" 是否小于 200。

        - "$gte": 大于等于操作符，检查值是否大于或等于指定值。
            例如：{"count": {"$gte": 100}} 检查 "count" 是否大于或等于 100。

        - "$lte": 小于等于操作符，检查值是否小于或等于指定值。
            例如：{"count": {"$lte": 200}} 检查 "count" 是否小于或等于 200。

        - "$in": 包含操作符，检查值是否在指定的集合中。
            例如：{"group_id": {"$in": [123, 456]}} 检查 "group_id" 是否在 [123, 456] 集合中。

        - "$not_in": 不包含操作符，检查值是否不在指定的集合中。
            例如：{"group_id": {"$not_in": [789]}} 检查 "group_id" 是否不在 [789] 集合中。

        - "$contains": 包含子字符串操作符，仅对字符串有效，检查值是否包含指定的子字符串。
            例如：{"text": {"$contains": "keyword"}} 检查 "text" 是否包含 "keyword"。

        - "$startswith": 开头匹配操作符，仅对字符串有效，检查值是否以指定的子字符串开头。
            例如：{"text": {"$startswith": "start"}} 检查 "text" 是否以 "start" 开头。

        - "$endswith": 结尾匹配操作符，仅对字符串有效，检查值是否以指定的子字符串结尾。
            例如：{"text": {"$endswith": "end"}} 检查 "text" 是否以 "end" 结尾。

        - "$and": 逻辑与操作符，包含一个规则列表，要求所有规则都必须为 True。
            例如：{"$and": [{"count": {"$gt": 100}}, {"username": {"$eq": "test_name"}}]}

        - "$or": 逻辑或操作符，包含一个规则列表，只要任一规则为 True 即返回 True。
            例如：{"$or": [{"age": {"$lt": 18}}, {"age": {"$gte": 20}}]}

        - "$range": 范围操作符，包含两个值，第一个值为起始值，第二个值为结束值。
            例如：{"age": {"$range": [18, 20]}} 检查 "age" 是否在 18 到 20 之间。

    :return: 如果当前状态符合规则则返回 True，否则返回 False。

    :example:

    current_state = {
        "count": 150,
        "username": "test_name",
        "age": 20
    }

    rule = {
        "$and": [
            {"count": {"$gt": 100}},
            {"username": {"$eq": "test_name"}},
            {"$or": [
                {"age": {"$lt": 18}},
                {"age": {"$gte": 20}}
            ]}
        ]
    }

    result = is_rule_valid(current_state, rule)
    # result 将返回 True，因为所有条件都符合。
    """

    def evaluate_condition(current_value, op, value):
        """根据操作符判断当前值是否满足条件"""
        if op == "$eq":
            return current_value == value or value == "any"
        elif op == "$ne":
            return current_value != value
        elif op == "$gt":
            return current_value > value
        elif op == "$lt":
            return current_value < value
        elif op == "$gte":
            return current_value >= value
        elif op == "$lte":
            return current_value <= value
        elif op == "$in":
            return current_value in value
        elif op == "$not_in":
            return current_value not in value
        elif op == "$contains":
            return isinstance(current_value, str) and value in current_value
        elif op == "$startswith":
            return isinstance(current_value, str) and current_value.startswith(value)
        elif op == "$endswith":
            return isinstance(current_value, str) and current_value.endswith(value)
        elif op == "$range":
            return value[0] <= current_value <= value[1]
        else:
            return False

    for key, condition in rule.items():
        if key == "$and":
            if not all(
                is_rule_valid(current_state, sub_rule) for sub_rule in condition
            ):
                return False
        elif key == "$or":
            if not any(
                is_rule_valid(current_state, sub_rule) for sub_rule in condition
            ):
                return False
        else:
            if key not in current_state:
                return False

            current_value = current_state.get(key)
            for op, value in condition.items():
                if not evaluate_condition(current_value, op, value):
                    return False

    return True


def simplify_rule(rule: Union[Dict, Any]):
    if not isinstance(rule, dict):
        return rule

    if "$and" in rule:
        simplified_sub_rules: List[Dict] = []
        seen_rules = set()

        for sub_rule in rule["$and"]:
            simplified_sub_rule = simplify_rule(sub_rule)
            if isinstance(simplified_sub_rule, dict) and "$and" in simplified_sub_rule:
                simplified_sub_rules.extend(simplified_sub_rule["$and"])
            elif isinstance(simplified_sub_rule, dict):
                rule_hash = str(simplified_sub_rule)
                if rule_hash not in seen_rules:
                    seen_rules.add(rule_hash)
                    simplified_sub_rules.append(simplified_sub_rule)
            elif simplified_sub_rule is False:
                raise Exception("error")

        merged_conditions: Dict[str, Dict[str, Any]] = {}
        for sub_rule in simplified_sub_rules:
            if isinstance(sub_rule, dict) and len(sub_rule) == 1:
                field, condition = next(iter(sub_rule.items()))
                if field not in merged_conditions:
                    merged_conditions[field] = {}
                for op, value in condition.items():
                    if op in merged_conditions[field]:
                        if op == "$in":
                            merged_conditions[field][op] = list(
                                set(merged_conditions[field][op]).intersection(value)
                            )
                        elif op == "$not_in":
                            merged_conditions[field][op] = list(
                                set(merged_conditions[field][op]).union(value)
                            )
                        else:
                            if merged_conditions[field][op] != value:
                                raise Exception("error")
                    else:
                        merged_conditions[field][op] = value

        final_sub_rules: List[Dict] = []
        for sub_rule in simplified_sub_rules:
            if isinstance(sub_rule, dict) and len(sub_rule) == 1:
                field, condition = next(iter(sub_rule.items()))
                if field in merged_conditions:
                    continue
            final_sub_rules.append(sub_rule)

        for field, condition in merged_conditions.items():
            final_sub_rules.append({field: condition})

        if len(final_sub_rules) == 1:
            return final_sub_rules[0]

        return {"$and": final_sub_rules}

    if "$or" in rule:
        simplified_sub_rules: List[Dict] = []
        seen_rules = set()

        for sub_rule in rule["$or"]:
            simplified_sub_rule = simplify_rule(sub_rule)
            if isinstance(simplified_sub_rule, dict) and "$or" in simplified_sub_rule:
                simplified_sub_rules.extend(simplified_sub_rule["$or"])
            elif isinstance(simplified_sub_rule, dict):
                rule_hash = str(simplified_sub_rule)
                if rule_hash not in seen_rules:
                    seen_rules.add(rule_hash)
                    simplified_sub_rules.append(simplified_sub_rule)
            elif simplified_sub_rule is True:
                return {}

        if len(simplified_sub_rules) == 1:
            return simplified_sub_rules[0]

        return {"$or": simplified_sub_rules}

    return rule


def and_merge_rules(*rules) -> Union[Dict, bool]:
    if not rules:
        return {}

    if len(rules) == 1:
        return rules[0]

    merged_rule = {"$and": []}

    for rule in rules:
        if isinstance(rule, dict) and "$and" in rule:
            merged_rule["$and"].extend(rule["$and"])
        else:
            merged_rule["$and"].append(rule)

    return simplify_rule(merged_rule)


def or_merge_rules(*rules):
    if not rules:
        return {}

    if len(rules) == 1:
        return rules[0]

    merged_rule = {"$or": []}

    for rule in rules:
        if isinstance(rule, dict) and "$or" in rule:
            merged_rule["$or"].extend(rule["$or"])
        else:
            merged_rule["$or"].append(rule)

    return simplify_rule(merged_rule)


def parse_response_rule_conditions(preset_rules, rule_str: str) -> Dict[str, Any]:
    try:
        patterns = {
            "CALL_COUNT >": r"CALL_COUNT > (\d+)",
            "CALL_COUNT <": r"CALL_COUNT < (\d+)",
            "CALL_COUNT in": r"CALL_COUNT in \[(\d+),(\d+)\]",
            "LEVEL >": r"LEVEL > (\d+)",
            "LEVEL <": r"LEVEL < (\d+)",
            "LEVEL in": r"LEVEL in \[(\d+),(\d+)\]",
            "NICKNAME": r"(.+) in NICKNAME",
            "CARD_NAME": r"(.+) in CARD_NAME",
            "QQ_NUMBER": r"(.+) in QQ_NUMBER",
        }

        def parse_preset_and_advanced(rule: str) -> Dict[str, Any]:
            parsed_conditions = []
            for part in rule.split(","):
                part = part.strip()
                if part in preset_rules:
                    parsed_conditions.append(preset_rules[part])
                else:
                    for key, pattern in patterns.items():
                        matches = re.findall(pattern, part)
                        if matches:
                            for match in matches:
                                if key == "CALL_COUNT >":
                                    parsed_conditions.append(
                                        {"call_count": {"$gt": int(match)}}
                                    )
                                elif key == "CALL_COUNT <":
                                    parsed_conditions.append(
                                        {"call_count": {"$lt": int(match)}}
                                    )
                                elif key == "CALL_COUNT in":
                                    parsed_conditions.append(
                                        {
                                            "call_count": {
                                                "$range": [int(match[0]), int(match[1])]
                                            }
                                        }
                                    )
                                elif key == "LEVEL >":
                                    parsed_conditions.append(
                                        {"level": {"$gt": int(match)}}
                                    )
                                elif key == "LEVEL <":
                                    parsed_conditions.append(
                                        {"level": {"$lt": int(match)}}
                                    )
                                elif key == "LEVEL in":
                                    parsed_conditions.append(
                                        {
                                            "level": {
                                                "$range": [int(match[0]), int(match[1])]
                                            }
                                        }
                                    )
                                elif key == "NICKNAME":
                                    parsed_conditions.append(
                                        {"nickname": {"$contains": match}}
                                    )
                                elif key == "CARD_NAME":
                                    parsed_conditions.append(
                                        {"card_name": {"$contains": match}}
                                    )
                                elif key == "QQ_NUMBER":
                                    parsed_conditions.append(
                                        {"user_id": {"$contains": match}}
                                    )
            if len(parsed_conditions) == 1:
                return parsed_conditions[0]
            return {"$and": parsed_conditions} if parsed_conditions else {}

        blocks = rule_str.split(";")
        combined_conditions = []

        for block in blocks:
            parsed_block = parse_preset_and_advanced(block)
            if parsed_block:
                combined_conditions.append(parsed_block)

        if len(combined_conditions) == 1:
            return combined_conditions[0]
        return {"$or": combined_conditions} if combined_conditions else {}

    except Exception:
        return {}


def parse_trigger_config(rule: str) -> Dict[str, Any]:
    """
    解析触发词触发规则配置字符串，确保只能选择一个规则。

    :param rule: 用户输入的规则字符串。
    :return: 解析后的规则字典或错误提示。
    """
    normal_rules = {"1": {"probability": 0.5}, "2": {"probability": 1.0}}
    if normal_rules.get(rule):
        return normal_rules[rule]
    elif match := re.match(r"^P\s*=\s*\d+(\.\d+)?$", rule):
        probability = float(match.group(1))
        if 0 < probability <= 1:
            parsed_rule: Dict[str, float] = {"probability": probability}
        else:
            return {}
    else:
        return {}

    return parsed_rule


async def process_wordbank_fts_image_by_pillow(data: dict) -> bytes:
    padding = 40
    card_padding = 20
    column_gap = 20
    row_gap = 20
    max_width = 1200
    card_width = (max_width - padding * 2 - column_gap) // 2
    y_offset = padding
    font_path = "./resources/fonts/LXGW_NERD_NOTO.ttf"

    img = Image.new("RGB", (max_width, 3000), color=(26, 27, 38))
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(font_path, 40)
    header_font = ImageFont.truetype(font_path, 24)
    text_font = ImageFont.truetype(font_path, 18)
    small_font = ImageFont.truetype(font_path, 16)

    title = "SakuraiSenrin 词库检索"
    title_width = draw.textlength(title, font=title_font)
    draw.text(
        ((max_width - title_width) // 2, y_offset),
        title,
        font=title_font,
        fill=(122, 162, 247),
    )
    y_offset += 80

    page_info = f"当前第 {data['current_page']} 页，共 {data['total_pages']} 页！"
    page_width = draw.textlength(page_info, font=text_font)
    draw.text(
        ((max_width - page_width) // 2, y_offset),
        page_info,
        font=text_font,
        fill=(169, 177, 214),
    )
    y_offset += 60

    current_column = 0
    column_y = [y_offset, y_offset]
    max_card_height = 0

    wordbank_data = data["wordbank_data"]

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3), reraise=True)
    async def get_image(url: str, client: AsyncClient) -> tuple[str, bytes]:
        return url, (await client.get(url)).read()

    async with AsyncClient(proxy=general_config.proxy, verify=False) as client:
        tasks = [
            asyncio.create_task(get_image(url, client))
            for url in set(
                [
                    j["url"]
                    for i in wordbank_data
                    for x in ["trigger_text", "response_text"]
                    for j in i[x]
                    if j["type"] == "image"
                ]
            )
        ]
        image_response_dict = dict(await asyncio.gather(*tasks))

    for card_data in data["wordbank_data"]:
        x = padding + current_column * (card_width + column_gap)
        y = column_y[current_column]

        card_img = Image.new("RGB", (card_width, 1000), (36, 40, 59))  # 临时高度
        card_draw = ImageDraw.Draw(card_img)
        card_y = card_padding
        header = "编号："
        header_width = card_draw.textlength(text=header, font=header_font)
        card_draw.text(
            (card_padding, card_y), header, font=header_font, fill=(187, 154, 247)
        )
        item_index = f"#{(card_data['rowid'] or '无')}"
        card_draw.text(
            (card_padding + header_width, card_y),
            item_index,
            font=header_font,
            fill=(0xF7, 0x76, 0x8E),
        )
        card_y += 40

        content_items = [
            ("trigger_text", "触发文本"),
            ("response_text", "响应文本"),
            ("trigger_config", "触发配置"),
            ("response_rule_conditions", "响应规则"),
            ("extra_info", "附加信息"),
        ]

        for key, label in content_items:
            if not card_data.get(key):
                continue

            card_draw.text(
                (card_padding, card_y),
                f"{label}：",
                font=text_font,
                fill=(122, 162, 247),
            )
            tag_width = draw.textlength(f"{label}：", font=text_font)
            content_x = card_padding + tag_width
            content_width = card_width - content_x - card_padding

            if key in ["trigger_text", "response_text"]:
                for item in card_data[key]:
                    if item["type"] == "image":
                        try:
                            resp = image_response_dict[item["url"]]
                            image = Image.open(io.BytesIO(resp))
                            image.thumbnail((content_width, 100))
                            card_img.paste(image, (round(content_x), card_y))
                            card_y += image.height
                        except Exception:
                            pass
                    elif item["type"] == "text":
                        text = item["text"]
                        lines = textwrap.wrap(text, width=round(content_width // 10))
                        for line in lines:
                            card_draw.text(
                                (content_x, card_y),
                                line,
                                font=text_font,
                                fill=(192, 202, 245),
                            )
                            card_y += 30
                card_y += 10
            else:
                text = str(card_data.get(key))
                lines = textwrap.wrap(text, width=round(content_width // 10))
                for line in lines:
                    card_draw.text(
                        (content_x, card_y),
                        line,
                        font=text_font,
                        fill=(192, 202, 245),
                    )
                    card_y += 40

        card_draw.text(
            (card_padding, card_y),
            f"创建者：{card_data['created_by']}",
            font=text_font,
            fill=(122, 162, 247),
        )
        card_y += 40
        card_draw.text(
            (card_padding, card_y),
            f"创建时间：{card_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}",
            font=text_font,
            fill=(122, 162, 247),
        )
        card_y += 40

        actual_height = card_y + card_padding
        card_img = card_img.crop((0, 0, card_width, actual_height))

        img.paste(card_img, (x, y))

        column_y[current_column] += actual_height + row_gap
        if actual_height > max_card_height:
            max_card_height = actual_height

        current_column = 1 if current_column == 0 else 0

    total_height = max(column_y) + 50
    img = img.crop((0, 0, max_width, total_height))

    draw = ImageDraw.Draw(img)

    copyright_info = f"© {data['current_year']} SakuraiSenrin - 版权所有 ✿(≧▽≦)"
    copyright_width = draw.textlength(copyright_info, font=small_font)
    draw.text(
        ((max_width - copyright_width) // 2, total_height - 40),
        copyright_info,
        font=text_font,
        fill=(169, 177, 214),
    )

    img_byte_arr = io.BytesIO()
    # img.show()
    img.save(img_byte_arr, format="PNG")

    return img_byte_arr.getvalue()


async def generate_wordbank_fts_image_by_pillow(
    wordbank_fts_list: list[list[WordbankFTS]], page_number: int = 1
) -> Message:
    try:
        message = Message(
            MessageSegment.image(
                await process_wordbank_fts_image_by_pillow(
                    dict(
                        wordbank_data=[
                            {
                                "rowid": index,
                                "trigger_text": json.loads(wordbank_fts.trigger_text)
                                if wordbank_fts.trigger_text
                                else None,
                                "response_text": json.loads(wordbank_fts.response_text)
                                if wordbank_fts.response_text
                                else None,
                                "created_by": wordbank_fts.created_by,
                                "created_at": wordbank_fts.created_at,
                                "trigger_config": wordbank_fts.trigger_config,
                                "response_rule_conditions": wordbank_fts.response_rule_conditions,
                                "extra_info": wordbank_fts.extra_info,
                            }
                            for index, wordbank_fts in enumerate(
                                wordbank_fts_list[page_number - 1], start=1
                            )
                        ],
                        current_page=page_number,
                        total_pages=len(wordbank_fts_list),
                        current_year=datetime.now().year,
                    )
                )
            )
        )
    except Exception as e:
        message = Message(MessageSegment.text(f"截图失败：{e}"))
    return message


async def generate_wordbank_fts_image_by_playwright(
    wordbank_fts_list: list[list[WordbankFTS]], page_number: int = 1
) -> Message:
    with open(
        Path(__file__).parent / "wordbank_fts_template.html", "r", encoding="utf-8"
    ) as f:
        template_string = f.read()
    template = Template(template_string)
    rendered_html = template.render(
        wordbank_data=[
            {
                "rowid": index,
                "trigger_text": json.loads(wordbank_fts.trigger_text)
                if wordbank_fts.trigger_text
                else None,
                "response_text": json.loads(wordbank_fts.response_text)
                if wordbank_fts.response_text
                else None,
                "created_by": wordbank_fts.created_by,
                "created_at": wordbank_fts.created_at,
                "trigger_config": wordbank_fts.trigger_config,
                "response_rule_conditions": wordbank_fts.response_rule_conditions,
                "extra_info": wordbank_fts.extra_info,
            }
            for index, wordbank_fts in enumerate(
                wordbank_fts_list[page_number - 1], start=1
            )
        ],
        current_page=page_number,
        total_pages=len(wordbank_fts_list),
        current_year=datetime.now().year,
    )
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(proxy={"server": general_config.proxy})
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
