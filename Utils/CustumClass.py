from typing import Literal, List, Dict
from pydantic import BaseModel
from nonebot.adapters.onebot.v11.adapter import Adapter
from nonebot.adapters.onebot.v11.event import NoticeEvent

class OfflineFile(BaseModel):

    name:str
    size:int
    url:str


class OfflineFileEvent(NoticeEvent):

    notice_type: Literal["offline_file"]
    user_id:int
    time:int
    file:OfflineFile

Adapter.add_custom_model(OfflineFileEvent)


class Ans(BaseModel):
    value: str = ""
    auth: str = ""
    time: str = ""

class Friend(BaseModel):
    __root__: Dict[str, List[Ans]]


class Group(BaseModel):
    __root__: Dict[str, List[Ans]]


class AtMsgReply(BaseModel):
    normal: List[str]
    annoy: List[str]
    rage: List[str]


class PokeMsgReply(BaseModel):
    normal: List[str]
    annoy: List[str]
    rage: List[str]


class Preinstall(BaseModel):
    at_msg_reply: AtMsgReply
    poke_msg_reply: PokeMsgReply
    handle_new_member: List[str]


class Wordkbank(BaseModel):
    friend: Dict[str, Friend]
    group: Dict[str, Group]
    preinstall: Preinstall

class ReverseItem(BaseModel):
    key: str
    auth: str
    time: str
    limit: str
    value: str
    effective_range: str


class ReverseDict(BaseModel):
    __root__: Dict[str,List[ReverseItem]]


class ReverseLib(BaseModel):
    k: ReverseDict
    a: ReverseDict
    t: ReverseDict
    v: ReverseDict