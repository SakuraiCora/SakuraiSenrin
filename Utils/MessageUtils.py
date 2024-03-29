from typing import Union, List
from nonebot.adapters.onebot.v11.event import MessageEvent


def ScanNumber(event: MessageEvent)->Union[int, None]:
    
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
            for _ in _msg.data['text'].split(" "):
                try:
                    args_text = int(_)
                except:
                    pass
                else:
                    break
    if args_at:
        args = args_at
    elif args_text:
        args = args_text
    elif args_at and args_text:
        args = args_at
    else:
        args = None
    return args


def split_list(input_list:List, size:int) -> List[List]:
    return [input_list[i:i+size] for i in range(0, len(input_list), size)]


def split_str(string, step=20) -> str:
    return '\n  '.join(string[i:i+step] for i in range(0, len(string), step))
