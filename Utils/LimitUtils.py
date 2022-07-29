from datetime import datetime
from random import randint
from math import pow


async def timeLimit(lastTime:datetime,LimitTime:int) -> bool:
    """
    :说明:

        冷却时间CD（s）并返回为bool

    :参数:

        lastTime, LimitTime
    """
    try:
        delta = (datetime.now()-lastTime).seconds
    except:   #初次启动
        lastTime = datetime.now()
        return True
    else:
        if  delta>= LimitTime:
            lastTime = datetime.now()
            return True     #已达到冷却时间
        else:
            return False    #未达到冷却时间

async def mathBuilder(num:int) ->tuple[str, str]:
    """
    :说明:

        出题

    :参数:

        num
    """
    a = randint(int(pow(10, num)), int(pow(10, num+1)))
    b = randint(int(pow(10, num)), int(pow(10, num+1)))
    problem = f"{a}+{b}=？"
    return(problem,str(a+b))