import nonebot
from pydantic import BaseModel


class Config(BaseModel):
    use_playwright: bool = False


water_config = nonebot.get_plugin_config(Config)
