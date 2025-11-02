"""
Author: SakuraiCora
Date: 2024-12-25 19:17:08
LastEditors: SakuraiCora
LastEditTime: 2024-12-30 02:23:16
Description: 管理模块，后期预计加入 webui

预计的功能:
1. 好友管理
2. 群管理
3. 权限管理
4. 插件管理（低优先级）
5. 插件调用次数统计


6. 词库管理系统（分页）写入插件里面去
"""

from pathlib import Path

import nonebot

sub_plugins = nonebot.load_plugins(str(Path(__file__).parent.resolve()))
