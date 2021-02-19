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
> ### Datalog.py
>+ 群聊发言次数记录及查询
>### Help.py
>+ 提供帮助文档
>### Notice.py
>+ 通知上报
>### PictureAppraisal.py
>+ 通过调用 **百度内容识别API** 来完成违规图识别
>### Pixiv.py
>+ ~~涩图（移植中，未填坑）~~
>### study.py
>+ 词库学习、调用、操作、展示

## 按功能分类
>有待完善

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
                           └── Study.py

<hr>

# 鸣谢
[Richard Chien](https://github.com/richardchien):  SDK -> [NoneBot2](https://github.com/nonebot/nonebot2)

[Mrs4s](https://github.com/Mrs4s): 运行框架 ->  [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

[KaguraYayoi](https://github.com/Fjaxzhy): ~~精神支持~~ [ReadMe.md](https://github.com/Hajimarino-HOPE/SakuraiZer0/blob/main/README.md) 编写

以及群内提供建议、技术支持的各位沙雕群友
