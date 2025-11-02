from typing import Optional

import nonebot
from pydantic import BaseModel


class Config(BaseModel):
    saucenao_api_key: Optional[str]
    ascii2d_api_key: Optional[str]


picsearch_config = nonebot.get_plugin_config(Config)
