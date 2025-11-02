import nonebot
from pydantic import BaseModel


class Config(BaseModel):
    support_vote_threshold: int = 5
    max_response_text: int = 200
    append_message: str = "这里是樱井千凛·Senrinです♡，您可以使用 #help 查看帮助信息。"
    send_approval_message_to_admin: bool = False


wordbank_config = nonebot.get_plugin_config(Config)
