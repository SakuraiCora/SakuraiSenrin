"""
Author: SakuraiCora
Date: 2024-12-28 11:54:53
LastEditors: SakuraiCora
LastEditTime: 2024-12-28 12:03:12
Description: 全局消息钩子
"""

from pathlib import Path

import nonebot

sub_plugins = nonebot.load_plugins(str(Path(__file__).parent.resolve()))
