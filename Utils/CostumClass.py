from typing import Literal
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