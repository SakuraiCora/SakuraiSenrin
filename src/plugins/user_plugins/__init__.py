"""
Author: SakuraiCora
Date: 2024-12-28 11:54:53
LastEditors: SakuraiCora
LastEditTime: 2025-01-02 17:43:28
Description: None
"""

from pathlib import Path

import nonebot

sub_plugins = nonebot.load_plugins(str(Path(__file__).parent.resolve()))
