import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init(apscheduler_autostart=True)
nonebot.init(apscheduler_config={"apscheduler.timezone": "Asia/Shanghai"})

app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# nonebot.load_plugins("Plugins")
nonebot.load_plugin("Plugins.Study")

if __name__ == "__main__":
    nonebot.run()