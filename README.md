<div align="center">
        <img style="border-radius: 50%;" src=".\logo.jpg" width="150px" height="150px" alt="SakuraiZer0-Logo"/>

# SakuraiZer0
### 打造一款服务于GalGame玩家的轻量级QQ机器人

[![](https://img.shields.io/badge/Lang-Python-important)](https://python.org)
[![](https://img.shields.io/badge/Frame-go_cqhttp-important)](https://github.com/Mrs4s/go-cqhttp)
[![](https://img.shields.io/badge/SDK-NoneBot2-important)](https://github.com/nonebot/nonebot2)
[![](https://img.shields.io/badge/Author-SakuraiCora-important)](https://github.com/Hajimarino-HOPE)
[![](https://img.shields.io/github/license/Hajimarino-HOPE/SakuraiZer0)](https://github.com/Hajimarino-HOPE/SakuraiZer0/blob/main/LICENSE)

</div>
<hr>

# 概览
### 本项目作为第一代(使用NoneBot1)的升级项目
### 由于程序写法的大幅度改变，所有功能正在从第一代移植中......

# 项目开源
### 采用GNU-GPLv3开源协议
+ 商业使用
+ 专利使用
+ 私人使用
+ 二次分发
+ 进行修改
>+ 二次分发必须包括版权申明与此协议
>+ 必须标注于何处修改
>+ 二次分发必须以相同协议

<hr>

# 使用手册
## 按文件分类
>### Datalog.py
>+ 群聊发言次数记录及查询
>### Help.py
>+ 提供帮助文档
>### Notice.py
>+ 通知上报、自动校时、整点报时
>### PictureAppraisal.py
>+ 通过调用 **百度内容识别API** 来完成违规图识别
>### Pixiv.py
>+ 通过调用 **Lolicon API** 来获取涩图
>### Study.py
>+ 词库学习、调用、操作、展示
>### TextAppraisa.py
>+ 初步 **处理** 并 **鉴定** 所发的文字中是否包含 **链接**

## 按功能分类
>### 被动触发
>+ 违规图识别
>+ 蓝链检测
>+ 通知上报

>### 主动触发
>#### 帮助文档
>+ **#help \<FunctionID>**
>>+ 发送 **功能代码** 为 ***functionID*** 的帮助文档
>>+ 若FunctionID为空，则发送 **功能代码列表**

>#### 词库学习
>+ **#study module Q A**
>>+ 让Zer0在用户发送 **Q** 的对于 **module** 回答 **A**
>>+ mudule参数：A（全局相应）P（个人相应）
>>+ Q为感知语（不能含有空格，默认严格匹配，区分大小写）
>>+ A为应答语（不能含有空格）
>+ **#lib_manage show（仅bot管理员）**
>>+ 以图片的格式展示词库 
>+ **#lib_manage del class uesr_id key（仅bot管理员）**
>>+ 删除 **studylib['class']['user_id']** 对应的词库条例
>>+ class参数：public（全局相应）private（个人响应）
>>+ user_id参数：
>>>+ 若class为public， 则填入 **all_users**
>>>+ 若class为private，则填入 **用户QQ号**

>#### 群聊发言次数查询
>+ **#water \<@user>**
>>+ 获取@对象的当天在本群的发言次数
>>+ 若\<@user>为空，则获取自己的发言次数
>+ **#water list**
>>+ 获取当天在本群的 **发言次数排行榜** （由于是at对方，慎用）

>### 随机/定向 涩图
>+ **#setu random level num**（指令模式）
>>+ 获取 num 张分级为 level 的涩图
>>+ level参数：0（非R18）1（R18）2（混合）
>>+ num参数：1-10
>+ **#setu search keyword num**（指令模式）
>>+ 获取 num 张关键词为 keyword 的涩图
>>+ keyword参数：关键字
>>+ num参数：1-10（可能会因为API库存原因而小于这个值）
>+ **regex** （正则匹配）
>>+ 以正则匹配的方法处理信息后，向内部函数传参来获取涩图
>>+ 随机涩图：
>>>+ 从本地库中随机抽取一张涩图 （CD为5s）
>>>+ ^[来整]点[涩色活好康][的图儿]$|^[色涩]图来$|^冲[亿1一]发$|^冲$|^[色涩黄]图$
>>>+ 示例：来点涩图 整点活儿 冲 冲亿发
>>+ 定向涩图：
>>>+ 从API中获取 ***num*** 张 ***keyword*** 的涩图 （CD为60s）
>>>+ ^[来整]点.\S*[色涩黄]图$|^[来整][几.\S*][张份个]\S*[色涩黄]图$
>>>+ 示例：来点keyword涩图 整十张keyword涩图
>+ **温馨提示：年轻人要学会控制自己的欲望**

<hr>

## 树状结构
#### 扫描层数：3

        SakuraiZer0
                ├── .env
                ├── .env.dev
                ├── .env.prod
                ├── bot.py
                ├── costrule.py
                ├── Data_Base
                │   ├── datalog.json
                │   ├── help.json
                │   ├── msyh.ttc
                │   ├── picture_lib.json
                │   ├── send.jpg
                │   └── studylib.json
                ├── docker-compose.yml
                ├── Dockerfile
                ├── pyproject.toml
                └── src
                    └── plugins
                           ├── Datalog.py
                           ├── Help.py
                           ├── Notices.py
                           ├── PictureAppraisal.py
                           ├── Pixiv.py
                           ├── Study.py
                           └── TextAppraisal.py

<hr>

# 鸣谢
[Richard Chien](https://github.com/richardchien):  SDK -> [NoneBot2](https://github.com/nonebot/nonebot2)

[Mrs4s](https://github.com/Mrs4s): 运行框架 ->  [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

[KaguraYayoi](https://github.com/Fjaxzhy): ~~精神支持~~ [ReadMe.md](https://github.com/Hajimarino-HOPE/SakuraiZer0/blob/main/README.md) 编写

以及群内提供建议、技术支持的各位沙雕群友
