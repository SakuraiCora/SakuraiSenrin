"""
    此处填写 config

    BAIDU_CLIENT_ID & BAIDU_CLIENT_SECRET请从 https://cloud.baidu.com 获取
    LOLICON_API 请从 https://api.lolicon.app 获取
    SAUCENAO_API 请从 https://saucenao.com 获取
"""

BAIDU_CLIENT_ID:str = ''
BAIDU_CLIENT_SECRET:str = ''

LOLICON_API:str = ''    
SAUCENAO_API:str = ''

REPORT_LIST:list[int] = [1479559098]   #消息上报的QQ号码
SETU_PATH:str = ''  #你的涩图本地储存路径   e.g: C:\\setu

PROXY:str = ''  #可能需要用到代理 e.g: http://127.0.0.1:10677 记得配置PAC，图片鉴定不能外网访问（代理配置错误直接给你404）

GIDS:dict[str,int] = {
}   #此处填写指定群聊

PAGIDS:dict[str,int] = {
}   #此处填写需要进行图片鉴定的群聊（考虑到鉴定次数有限）

'''
    指定群聊示例：

    GIDS:dict[str,int] = {
        "group1":123456,
        "group2":654321
    }

'''
