from nonebot.adapters.onebot.v11.message import MessageSegment, Message

async def RandomSetuMsg(userID, Rmodle, num, level) -> Message:

    handle_msg = (
    MessageSegment.at(userID)+MessageSegment.text("随机涩图触发\n")
    +MessageSegment.text(f"触发方式：{Rmodle}\n")
    +MessageSegment.text(f"图片分级：{level}\n")
    +MessageSegment.text(f"图片数量：{num}\n")
    +MessageSegment.text("Loading......（约3秒钟）")
    )
    return handle_msg

async def SearchSetuMsg(userID, Smodle, keywords, num) -> Message:
    handle_msg = (
    MessageSegment.at(userID)+MessageSegment.text("定向涩图触发\n")
    +MessageSegment.text(f"触发方式：{Smodle}\n")
    +MessageSegment.text(f"关键词：{keywords}\n")
    +MessageSegment.text(f"图片数量：{num}\n")
    +MessageSegment.text("Loading......（约3秒钟）")
    )
    return handle_msg

def SetuCommandTypeChecker(arg) -> bool:  # 检查涩图命令格式
    if arg:
        if arg[1] == 'random':
            try:
                level = int(arg[2])
                num = int(arg[3])
            except:
                check_type = False
            else:
                if level in [1, 2, 0] and num <= 5:
                    check_type = True
                else:
                    check_type = False
        elif arg[1] == 'search':
            try:
                num = int(arg[3])
            except:
                check_type = False
            else:
                check_type = True if num <= 10 else False
        else:
            check_type = False
    else:
        check_type = False
    return check_type