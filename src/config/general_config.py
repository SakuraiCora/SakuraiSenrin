import nonebot
from pydantic import BaseModel


class GeneralConfig(BaseModel):
    gist_token: str
    proxy: str
    support_group_id: int

    pg_port: int
    pg_host: str
    pg_username: str
    pg_password: str
    pg_pool_size: int
    pg_max_overflow: int

    use_playwright: bool = False

    ignore_user_list: list[str]


general_config = nonebot.get_plugin_config(GeneralConfig)
