#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
import datetime
import json
import os
from nonebot.adapters.onebot.v11 import Adapter

LogPath = os.path.join(os.getcwd(), 'Resources', 'Json', 'datalog.json')

with open(LogPath, 'r+', encoding='utf-8') as f:
    try:
        memdic = json.load(f)
    except:
        memdic = {}
    try:
        StartTime: str = memdic['StartTime']
    except:
        StartTime: str = str(datetime.datetime.now())
        memdic['StartTime'] = StartTime
        json.dump(memdic, f, indent=2, sort_keys=True, ensure_ascii=False)

nonebot.init(apscheduler_autostart=True)
nonebot.init(apscheduler_config={
    "apscheduler.timezone": "Asia/Shanghai"
})
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
nonebot.load_plugins("Plugins")

if __name__ == "__main__":
    nonebot.run()