"""
    今天食堂吃什么
    1.随机选取菜单中的食物，按照一定规则搭配
        1.1.价格
        1.2.随机
        1.3.位置
        1.4.等待时间(0=数据缺失, 1-5分为5个等级，代表：很短 短 中 长 很长)
        1.5.类型(0=小吃, 1=正餐)
        1.6.暴力随机生成，仅需指出学校（富哥vivo50 T_T）
    2.自定义导入菜单，包含location, name, price, time
    3.手动导入后重载功能
    4.吃了什么->历史记录 #TODO
    5.菜单管理
"""
import asyncio
import json

from nonebot.plugin import on_command, on_notice
from nonebot.params import ArgPlainText
from nonebot.typing import T_State
from Utils.CustomRule import only_master, check_white_list, is_menu
from Utils.CostumClass import OfflineFileEvent
from httpx import AsyncClient
from .HandleMeal import *
from .MealClass import menuFile


eat = on_command("eat", aliases={"今天食堂吃什么", "吃什么", "怎么吃", "吃"}, priority=5, rule=check_white_list())
manage = on_command("menu_manage", rule=only_master())
menu_file = on_notice(rule=only_master()&is_menu())


@eat.handle()
async def _eat(state:T_State):
    mi:mealInfo = mealInfo()
    state['mi'] = mi
    await eat.send("又到了淦饭时间，加油，淦饭人~")
    await asyncio.sleep(0.5)
    await eat.send(f"今天恰哪个学校的食堂呢？\n{mealInfo.getSchool()}")

@eat.got("school")
async def _school_eat(state:T_State, school_name:str=ArgPlainText("school")):
    mi:mealInfo = state['mi']
    if mealInfo.supportSchool(school_name):
        mi.school = school_name.upper()
        await eat.send("好耶！")
        await asyncio.sleep(0.5)
        await eat.send(f"亲爱的{mi.school}学子，今天恰学校的哪个食堂呢(⑅˃◡˂⑅)\n{mealInfo.getLocation(mi.school)}")
        await asyncio.sleep(0.5)
        await eat.send("举棋不定的话，直接说“随便”就好啦！不想浪费太多时间？急着恰饭？想要简单粗暴一点？那就请说“速速速”吧！")
        state['mi'] = mi
    elif school_name == "不吃了":
        await eat.finish("一位淦饭人伤心地离开了……")
    else:
        await eat.reject(f"暂时没有“{school_name}”这个学校的菜单呢₍•Д•)\n你可以说“不吃了”来结束本次会话，否则请重新输入支持的学校")

@eat.got("location")
async def _location_eat(state:T_State, location_name:str=ArgPlainText("location")):
    mi:mealInfo = state['mi']
    if mealInfo.supportLocation(mi.school,location_name):
        mi.location=mealInfo.randomLocation(mi.school) if location_name == "随便" else location_name.upper()
        await eat.send(f"那就决定在”{mi.location}“吃了哦！")
        await asyncio.sleep(0.5)
        await eat.send("来都来了，恰点什么好呢，是小吃（0）还是主食（1）呢？\n请输入相应的数字吧！")
        await asyncio.sleep(0.5)
        await eat.send("举棋不定的话，就请说“随便”；如果无所谓的话，那就请说“都可以”吧！")
        state['mi'] = mi
    elif location_name == "不吃了":
        await eat.finish("一位淦饭人伤心地离开了……")
    elif location_name == '速速速':
        await eat.send("哇啊……那我尽量快一点想出方案……预算什么的已经无所谓了₍•Д•)")
        await eat.finish(mealInfo.getRandomMeal(mi))
    else:
        await eat.reject(f"欸……似乎学校里没有”{location_name}“这个食堂欸₍•Д•)\n你可以说“不吃了”来结束本次会话，否则请重新输入支持的食堂")

@eat.got("food_type")
async def _food_type_eat(state:T_State, food_type_name:str=ArgPlainText("food_type")):
    mi:mealInfo = state['mi']
    if mealInfo.supportFoodType(food_type_name):
        if food_type_name == "都可以":
            mi.food_type = "1' OR food_type = '0"
            await eat.send("wow，那就都可以吧！")
        else:
            if food_type_name == "随便":
                mi.food_type, _ = mealInfo.randomFoodType()
            else:
                mi.food_type = int(food_type_name)
                _ = mealInfo.getFoodType(food_type_name)
            await eat.send(f"那就决定吃“{_}”吧！")
        await asyncio.sleep(0.5)
        await eat.send("恰饭的快慢是有学问的！所以，你急不急着淦饭呢？\n请输入0-5之间代表理论上等待时间的数字\n0=数据缺失, 1-5分为5个等级，代表：很急 急 中 还有时间 时间还多")
        await asyncio.sleep(0.5)
        await eat.send("（为了节目效果，还是选0罢T_T")
        state['mi'] = mi
    elif food_type_name == "不吃了":
        await eat.finish("一位淦饭人伤心地离开了……")
    else:
        await eat.reject(f"欸？！{food_type_name}什么啊……是小吃还是主食呢……这让我很^啊……你可以说“不吃了”来结束本次会话，否则请重新输入支持的数字（0-1）")

@eat.got("wate_time")
async def _wate_time_eat(state:T_State, wate_time_len:str=ArgPlainText("wate_time")):
    mi:mealInfo = state['mi']
    if mealInfo.supportWaitTime(wate_time_len):
        mi.wait_time = int(wate_time_len)
        await eat.send(f"看样子你现在的状态是“{mealInfo.getWaitState(wate_time_len)}”呢！那么，咱来谈点伤感情的事，就是哪个……钱……怎么说=A=")
        await asyncio.sleep(0.5)
        await eat.send("请用1000以内的整数或一位小数表达你的预算吧(⑅˃◡˂⑅)")
        state['mi'] = mi
    elif wate_time_len == "不吃了":
        await eat.finish("一位淦饭人伤心地离开了……")
    else:
        await eat.reject(f"“{wate_time_len}”这种数字我可真的没见过，有点匪夷所思₍•Д•)\n你可以说“不吃了”来结束本次会话，否则请重新输入支持的数字（0-5）")

@eat.got("price")
async def _price_eat(state:T_State, price_money:str=ArgPlainText("price")):
    mi:mealInfo = state['mi']
    if mealInfo.supportPrics(price_money):
        await eat.send(f"预算是{price_money}元，让我想想吃点什么好呢……")
        mi.price = float(price_money)
        await eat.send(mealInfo.buildMealMsg(mealInfo.getFinalMeal(mi)))
        await asyncio.sleep(0.5)
        await eat.send("对于这份方案满意嘛 ⸜(๑'ᵕ'๑)⸝⋆*\n满意的话就请说“好”，如需更换就请说“更换”")
        state["mi"] = mi
    elif price_money == "不吃了":
        await eat.finish("一位淦饭人伤心地离开了……")
    else:
        await eat.reject(f"“{price_money}”是什么啊，好奇怪的东西，真的可以当钱花吗₍•Д•)\n你可以说“不吃了”来结束本次会话，否则请重新输入支持的数字（1000以内的整数、一位小数）")

@eat.got("ret")
async def _ret_eat(state:T_State, ret_state:str=ArgPlainText("ret")):
    mi:mealInfo = state['mi']
    if ret_state == "好":
        await eat.finish("好耶！！！(⑅˃◡˂⑅)")
    elif ret_state == "更换":
        await eat.send("那我再想想，吃什么好呢……")
        await eat.send(mealInfo.buildMealMsg(mealInfo.getFinalMeal(mi)))
        await asyncio.sleep(0.5)
        await eat.reject("对于这份方案满意嘛 ⸜(๑'ᵕ'๑)⸝⋆*\n满意的话就请说“好”，如需更换就请说“更换”")
    else:
        await eat.reject(f"“{ret_state}”是好还是不好呢……优质解答：我不知道(´இ皿இ｀)\n满意的话就请说“好”，如需更换就请说“更换”")

@menu_file.handle()
async def _menu_file(event:OfflineFileEvent):
    if event.file.size > 100000:
        await menu_file.finish("这个菜单似乎有点太大了啊₍•Д•)咱就是说只支持100kb以下的菜单哦")
    else:
        await menu_file.send("正在处理中❛‿˂̵✧")
        async with AsyncClient(proxies={}) as Client:
            res = (await Client.get(event.file.url)).read().decode("utf-8")
        try:
            fdic = json.loads(res)
            menuFile(**fdic)
        except:
            await menu_file.finish("这个菜单看起来怪怪的，我不认识₍•Д•)咱就是说请发送标准的json文件")
        else:
            await menu_file.finish(importMeal(fdic, event.user_id))