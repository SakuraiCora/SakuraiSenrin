from random import randint
from math import pow


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