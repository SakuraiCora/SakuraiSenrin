import sqlite3
import random

from pydantic import BaseModel
from string import ascii_uppercase, digits
from typing import List, Tuple, Union, Dict


conn = sqlite3.connect("./Resources/db/menu.db")   #TODO
menu = conn.cursor()


class mealInfo:

    def __init__(self) -> None:
        self.name:str
        self.sub_name:str
        self.school:str
        self.location:str
        self.food_type:Union[int, str]
        self.food_symbol:int
        self.wait_time:int
        self.price:float
        self.balance:float
        self.who:int
        self.add_time:str

    @classmethod
    def commit_db(cls) -> None:
        conn.commit()

    def add_sql(self) -> None:
        sql = f"""REPLACE INTO "main"."{self.school}" ( "location", "name", "sub_name", "price", "wait_time", "food_type", "food_symbol", "add_time", "who_added" ) VALUES ( '{self.location}', '{self.name}', '{self.sub_name}', {self.price}, {self.wait_time}, {self.food_type}, {self.food_symbol}, '{self.add_time}', {self.who} )"""
        try:
            menu.execute(sql)
        except sqlite3.OperationalError:
            menu.execute(f"""CREATE TABLE "{self.school}" (
                "location" TEXT,
                "name" TEXT,
                "sub_name" TEXT,
                "price" REAL,
                "wait_time" integer,
                "food_type" integer,
                "food_symbol" integer,
                "add_time" TEXT,
                "who_added" integer,
                PRIMARY KEY ("location", "name"));""")
            self.add_sql()

    def safe_str(self) -> bool:
        for s in vars(self).items():
            if s[1] == None or s[0] == 'add_time': continue
            for x in str(s[1]):
                if not (x in (ascii_uppercase+digits+"_ .") or '\u4e00' <= x <= '\u9fa5'):
                    return False 
        return True

    @classmethod
    def getSchool(cls)->str:
        res = menu.execute("SELECT name FROM sqlite_master WHERE type ='table'").fetchall()
        _ = ''
        for x in res:
            _ += x[0] + "\n"
        return _.strip()

    @classmethod
    def supportSchool(cls, s:str)->bool:
        return (True if (s.upper(),) in menu.execute("SELECT name FROM sqlite_master WHERE type ='table'").fetchall() else False)

    @classmethod
    def getLocation(cls, school:str)->str:
        res = menu.execute(f"SELECT DISTINCT location FROM '{school}'").fetchall()
        _ = ''
        for x in res:
            _ += x[0] + "\n"
        return _.strip()

    @classmethod
    def supportLocation(cls, s:str, l:str)->bool:
        return (True if (l.upper(),) in menu.execute(f"SELECT DISTINCT location FROM '{s}'").fetchall() or l == "随便" else False)

    @classmethod
    def randomLocation(cls, s:str)->str:
        location = menu.execute(f"SELECT DISTINCT location FROM '{s}'").fetchall()
        return random.choice(location)[0]

    @classmethod
    def supportFoodType(cls, p:str)->bool:
        return True if p in ["0", "1", "随便", "都可以"] else False

    @classmethod
    def getFoodType(cls, p:str)->str:
        food_type_dict = {
            "0":"小吃",
            "1":"主食"
        }
        return food_type_dict[p]

    @classmethod
    def randomFoodType(cls)->tuple[int,str]:
        r = random.randint(0,1)
        return (r,cls.getFoodType(str(r)))

    @classmethod
    def supportWaitTime(cls, t:str)->bool:
        return True if t in ["0", "1", "2", "3", "4", "5"] else False

    @classmethod
    def getWaitState(cls, w:str)->str:
        wait_time_dict = {
        "0":"无所谓",
        "1":"急急国王",
        "2":"有点小急",
        "3":"是真的无所谓",
        "4":"可以慢慢品味一番",
        "5":"准备好好享受一番"
        }
        return  wait_time_dict[w]

    @classmethod
    def supportPrics(cls, m:str)->bool:
        try:
            float(m)
        except:
            return False
        else:
            if '.' in m:
                _ = m.split(".")
                if len(_) == 2:
                    return True if len(_[1]) == 1 else False
                else:
                    return False
            else:
                return True if float(m)<=1000.0 else False

    @classmethod
    def buildMealMsg(cls, mit:Tuple[List["mealInfo"], float])-> str:
        _ = mit[0][0].location+"\n"
        for i, mi in enumerate(mit[0]):
            _ += f"  {i+1}.{mi.name}-{mi.sub_name}-{mi.price}元\n"
        return f"经过一系列胡思乱想之后，得出了这样的结果：\n{_}余额{mit[1]}元"

    @classmethod
    def serMealInfo(cls, _:Tuple[str, str, str, float, int, int, int, str, int]) -> "mealInfo":
        res_mi:mealInfo = mealInfo()
        res_mi.location = _[0]
        res_mi.name = _[1]
        res_mi.sub_name = "" if _[2] == "none" else _[2]
        res_mi.price = _[3]
        res_mi.wait_time = _[4]
        res_mi.food_type = _[5]
        res_mi.food_symbol = _[6]
        res_mi.add_time = _[7]
        res_mi.who = _[8]
        return res_mi

    @classmethod
    def serMealInfoFromSQL(cls, tu:List[Tuple[str, str, str, float, int, int, int, str, int]]) -> List["mealInfo"]:
        r_list = []
        for _ in tu:
            r_list.append(cls.serMealInfo(_))
        return r_list

    @classmethod
    def getFinalMeal(cls, mi:"mealInfo") -> Tuple[List["mealInfo"], float]:
        mi.balance = mi.price                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
        food_handle_dict = {} #用于存储数据库中查询到的食物信息
        p_list = []   #储存可能的价格
        final_list:List[mealInfo] = []
        for _ in menu.execute(f"SELECT DISTINCT price FROM {mi.school} WHERE location = '{mi.location}' ORDER BY price").fetchall():
            if mi.balance >= _[0]:
                food_handle_dict[_[0]] = cls.serMealInfoFromSQL(menu.execute(f"SELECT * FROM {mi.school} WHERE (location='{mi.location}' AND (food_type='{mi.food_type}') AND price={_[0]} AND food_symbol = 0)").fetchall())
                continue
            break
        for p in list(food_handle_dict.keys())[::-1]:
            count = int(mi.balance // p)
            mi.balance -= p * count
            p_list += [p] * count
        for p in p_list:final_list.append(random.choice(food_handle_dict[p]))
        return (final_list, mi.balance)

    @classmethod
    def getRandomMeal(cls, mi:"mealInfo") -> str:
        return cls.buildMealMsg((cls.serMealInfoFromSQL(menu.execute(F"SELECT * FROM {mi.school} WHERE (location='{cls.randomLocation(mi.school)}' AND food_symbol = 0) ORDER BY RANDOM() limit 1").fetchall()),0))

class menuFile(BaseModel):

    Dict[str,Dict[str,List[str]]]