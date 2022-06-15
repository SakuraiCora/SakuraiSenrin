from nonebot.adapters.cqhttp.event import MessageEvent


async def ScanNumber(event: MessageEvent):
    
    """
    :说明:

        搜索可能存在于消息中的QQ号

    :参数:

        event
    """

    args_at = None
    args_text = None
    
    for _msg in event.message:
        if _msg.type == 'at': 
            args_at = int(_msg.data['qq'])
        elif _msg.type == 'text':
            try:
                args_text = int(_msg.data['text'])
            except:
                pass
    if args_at:
        args = args_at
    elif args_text:
        args = args_text
    elif args_at and args_text:
        args = args_at
    else:
        args = None
    return args

def SetuCommandTypeChecker(arg) -> bool:  # 检查涩图命令格式
    if arg:
        if arg[0] == 'random':
            try:
                level = int(arg[1])
                num = int(arg[2])
            except:
                check_type = False
            else:
                if level in [1, 2, 0] and num <= 10:
                    check_type = True
                else:
                    check_type = False
        elif arg[0] == 'search':
            try:
                num = int(arg[2])
            except:
                check_type = False
            else:
                check_type = True if num <= 10 else False
        else:
            check_type = False
    else:
        check_type = False
    return check_type