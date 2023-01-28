
from datetime import datetime as dt
from typing import List, Dict
from .MealClass import mealInfo

def importMeal(fdic:Dict[str,Dict[str,List[str]]], user:int) ->str:
    now = dt.now()
    time = f'{now.year}-{now.month}-{now.day}'
    tip = ""
    for school in fdic:
        for location in fdic[school]:
            for data in fdic[school][location]:
                _ = data.split(" ")
                try:
                    meal = mealInfo.serMealInfo((location, _[0], _[1], float(_[2]), int(_[3]), int(_[4]), int(_[5]), time, user))
                    meal.school = school
                    if not meal.safe_str():raise Exception()
                except:
                    tip += f"""{school}->{location}->{data}>>>添加失败，请检查格式是否符合要求！\n"""
                else:
                    meal.add_sql()
    tip += "菜单添加完成！"
    mealInfo.commit_db()
    print(tip)
    return tip