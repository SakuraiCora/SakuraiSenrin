"""
Author: SakuraiCora
Date: 2024-12-28 14:41:29
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 19:38:51
Description: 通知事件处理
"""

from pathlib import Path

import nonebot

sub_plugins = nonebot.load_plugins(str(Path(__file__).parent.resolve()))
