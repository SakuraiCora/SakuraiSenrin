from datetime import datetime


async def Limit(lastTime:datetime,LimitTime:int) -> bool:
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