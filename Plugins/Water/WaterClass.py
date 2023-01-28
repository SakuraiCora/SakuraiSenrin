import sqlite3
import datetime

from io import BytesIO
from typing import List
from nonebot import get_bot
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from Utils.ImageUtils import get_water_card

conn = sqlite3.connect("./Resources/db/water.db")
water_db = conn.cursor()


class WaterInfo:

    def __init__(self) -> None:
        self.time:datetime.datetime = datetime.datetime.now()
        self.format_time:str = self.time.strftime("%Y-%m-%d")
        self.format_time_aps:str = (self.time+datetime.timedelta(days=-1)).strftime("%Y-%m-%d")

    async def getRank(self, group_id:int, symbol:bool) -> BytesIO:
        table = self.format_time_aps if symbol else self.format_time
        member_info:List[tuple[int,str,int]] = []
        bot = get_bot()
        for _ in water_db.execute(f"""SELECT qq,water FROM "{table}" WHERE group_id={group_id} ORDER BY water""").fetchall():
            try:
                info = await bot.get_group_member_info(group_id=group_id,user_id=_[0])
            except: 
                continue
            else:
                member_info.append((_[0], info['nickname'], _[1]))
        return await get_water_card(member_info)


class WaterInfoSub(WaterInfo):

    def __init__(self, event:GroupMessageEvent) -> None:
        super().__init__()
        self.group:int = event.group_id
        self.qq:int = event.user_id
        self.water:int
        try:
            self.water = water_db.execute(f"""SELECT water FROM "{self.format_time}" WHERE (group_id={self.group} AND qq={self.qq})""").fetchall()[0][0]
        except:
            self.water = 0


    def createTable(self) -> None:
        water_db.execute(f"""CREATE TABLE "{self.format_time}" (
                "group_id" integer NOT NULL,
                "qq" integer NOT NULL,
                "water" integer NOT NULL,
                "last_time" TEXT NOT NULL,
                PRIMARY KEY ("group_id", "qq"));""")

    def add(self) -> None:
        try:
            water_db.execute(f"""REPLACE INTO "main"."{self.format_time}" ("group_id", "qq", "water", "last_time") VALUES ({self.group}, {self.qq}, {self.water+1}, '{self.format_time}')""")
        except:
            self.createTable()
            self.add()
        conn.commit()

    def getPersonalWater(self, *qq:int) -> Message:
        if qq:
            self.qq = qq[0]
            try:
                self.water = water_db.execute(f"""SELECT water FROM "{self.format_time}" WHERE (group_id={self.group} AND qq={self.qq})""").fetchall()[0][0]
            except:
                self.water = 0
        return (
        MessageSegment.text("好耶！那就让我来康康宁有多氵\n")
        +MessageSegment.text("查询对象：")+MessageSegment.at(self.qq)+MessageSegment.text("\n")
        +MessageSegment.text(f"吹氵次数：{self.water}\n")
        +MessageSegment.text(f"起始时间：00:00:00\n")
        +MessageSegment.text(f"终止时间：{datetime.datetime.now().strftime('%H:%M:%S')}"))
