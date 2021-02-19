#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.cqhttp import Bot
gids = {}  # 此处放入指定群聊

nonebot.init(apscheduler_autostart=True)
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter("cqhttp", Bot)
nonebot.load_plugins("src/plugins")


config = nonebot.get_driver().config
config.GroupList = gids

if __name__ == "__main__":
    nonebot.run(app="bot:app")
