<div align="center">
        <img style="border-radius: 50%;" 
        src="https://cdn.jsdelivr.net/gh/ Hajimarino-HOPE/SakuraiZer0/docs/img/Senrin-code-Complete.PNG" 
        width="150px" 
        height="150px" 
        alt="SakuraiZer0-Logo"/>

# SakuraiZer0
### 打造一款服务于GalGame玩家的轻量级QQ机器人

[![](https://img.shields.io/badge/Lang-Python-FF1493)](https://python.org)
[![](https://img.shields.io/badge/Frame-go_cqhttp-7B68EE)](https://github.com/Mrs4s/go-cqhttp)
[![](https://img.shields.io/badge/SDK-NoneBot2-3CB371)](https://github.com/nonebot/nonebot2)
[![](https://img.shields.io/badge/Author-SakuraiCora-F08080)](https://github.com/Hajimarino-HOPE)
[![](https://img.shields.io/github/license/Hajimarino-HOPE/SakuraiZer0)](https://github.com/Hajimarino-HOPE/SakuraiZer0/blob/main/LICENSE)

</div>
<hr>

# 概览
### 本项目作为第一代(使用NoneBot1)的升级项目
### 由于程序写法的大幅度改变，所有功能正在从第一代移植中......
###	DemoQQ：1768641952
	> 好友验证码：Senrin（注意区分大小写）

---
# 更新
- 2021.7.2
  - 樱井千凛人设V1.0发布
- 2021.6.30  
  - 完成移植 **GalGame随即推荐** 功能
  - 更改目录结构

---
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

# 使用手册 （带*的为新功能！！！）

## 按文件分类

<details><summary>文件详情</summary>

>### [Datalog.py](.\src\plugins\Datalog.py)
>+ 群聊发言次数记录及查询
>### [GalRecommend.py*](.\src\plugins\GalRecommend.py)
>+ 基于 **恋爱游戏网** 的GalGame随机推荐*
>### [Help.py](.\src\plugins\Help.py)
>+ 提供帮助文档
>### [Info.py](.\src\plugins\Info.py)
>+ 制作简单的资料卡
>### [Notice.py](.\src\plugins\Notice.py)
>+ 通知上报、自动校时、整点报时
>### [PictureAppraisal.py](.\src\plugins\PictureAppraisal.py)
>+ 通过调用 **百度内容识别API** 来完成违规图识别
>### [SearchPic.py](.\src\plugins\SearchPic.py)
>+ 通过 **SauceNAO** 提供的API进行搜图
>### [Setu.py](.\src\plugins\Setu.pyy)
>+ 通过调用 **Lolicon API** 来获取涩图
>### [Study.py](.\src\plugins\Study.py)
>+ 词库学习、调用、操作、展示
>### [TextAppraisa.py](.\src\plugins\TextAppraisa.py)
>+ 初步 **处理** 并 **鉴定** 所发的文字中是否包含 **链接**
</details>


## 按功能分类
<details><summary>被动触发型集合</summary>

>1. 违规图识别
>2. 蓝链检测
>3. 通知上报

</details>

<details><summary>帮助文档</summary>

- #help &lt;FunctionID>

  > 示例：#help AWHD
	- 发送 **功能代码** 为 ***functionID*** 的帮助文档
	- 若FunctionID为空，则发送 **功能代码列表**


</details>

<details><summary>词库学习</summary>

- #study module Q A

  > 示例：#study A Zer0 nmd叫我搞锤子？！

  - 让Zer0在用户发送 **Q** 的对于 **module** 回答 **A**
  - mudule参数：A（全局相应）P（个人相应）
  - Q为感知语（不能含有空格，默认严格匹配，区分大小写）
  - A为应答语（不能含有空格）

- lib_manage show（仅bot管理员）

  > 示例：#lib_manage show

  - 以图片的格式展示词库 

- #lib_manage del class uesr_id key（仅bot管理员）

  > 示例：#lib_manage del public all_users Zer0

	- 删除 **studylib['class']['user_id']** 对应的词库条例
	- class参数：public（全局相应）private（个人响应）
	- user_id参数：
  	- 若class为public， 则填入 **all_users**
    - 若class为private，则填入 **用户QQ号**

</details>

<details><summary>群聊发言次数查询</summary>

- #water <@user>

  > 示例：#water
  >
  > 示例：#water @Zer0

	- 获取@对象的当天在本群的发言次数
	- 若<@user>为空，则获取自己的发言次数

- #water list

  > 示例：#water list

	- 获取当天在本群的 **发言次数排行榜** （由于是at对方，慎用）

</details>

<details><summary>随机/定向 涩图</summary>

- #setu random level num

  > 示例：#setu random 1 10

	- 获取 num 张分级为 level 的涩图
	- level参数：0（非R18）1（R18）2（混合）
	- num参数：1-10

- #setu search keyword num（指令模式）

  > 示例：#setu 白丝萝莉 10

	- 获取 num 张关键词为 keyword 的涩图
	- keyword参数：关键字
	- num参数：1-10（可能会因为API库存原因而小于这个值）

- regex （正则匹配）

	- 以正则匹配的方法处理信息后，向内部函数传参来获取涩图
	- 随机涩图：

      > 示例：来点涩图 
      >
      > 示例：整点活儿 
      >
      > 示例：冲 
      >
      > 示例：冲亿发

      - 从本地库中随机抽取一张涩图 （CD为5s）
      - 正则表达式：^[来整]点[涩色活好康][的图儿]$|^[色涩]图来$|^冲[亿1一]发$|^冲$|^[色涩黄]图$

	- 定向涩图：

      > 示例：来点**白丝萝莉**涩图
      >
      > 示例：整**十**张**白丝萝莉**涩图
      >
      - 从API中获取 ***num*** 张 ***keyword*** 的涩图 （CD为60s）
      - 正则表达式：^[来整]点.\S*[色涩黄]图$|^[来整][几.\S*][张份个]\S*[色涩黄]图$


**温馨提示：年轻人要学会控制自己的欲望！！！**

**温馨提示：年轻人要学会控制自己的欲望！！！**

**温馨提示：年轻人要学会控制自己的欲望！！！**

</details>

<details><summary>制作资料卡</summary>

- **#info \<@user>** 

  > 示例：#info
  >
  > 示例：#info @Zer0

  - 根据有限的信息制作简单资料卡 
  - 若\<@user>为空，则制作自己的资料卡 
  - ~~（你甚至可以看看Zer0的资料卡）~~ 

</details>

<details><summary>搜图</summary>

  >示例：~~示不出来~~

- 【Reply】回复想搜的图
	- 通过 **SauceNAO** 提供的API进行搜图 
	- 搜图结果以**私聊**方式送达
	- 若持续未收到结果，请添加Zer0为好友
	> 好友验证码：Senrin（注意区分大小写）

</details>

<details><summary>随机GalGame推荐</summary>

- 土方法，基于[恋爱游戏网](https://lianaiyx.com)的GalGame推荐插件
- #gal random

  >示例：#gal random 

	- 随机推荐一个GalGame

- #gal tag tag

  > 示例：#gal tag 萝莉

  - 推荐一个标签为 tag 的GalGame
  - tag参数：
    3D ACT NTR RPG 傲娇 百合 变身 病娇 策略 超能力 传奇 穿越 纯爱 催泪 大小姐 岛 电波作 恶魔 复仇 公主 怪物 怪物娘 馆 鬼畜 国产 过激 和风 黑暗向 后宫 护士 幻想 机器人 架空世界 姐妹 解谜 姐系 禁忌恋 近未来 剧情 咖啡店 开店 科幻 科学幻想 老师 恋爱 猎奇 另类 灵异 轮回 萝莉 冒险 美少女养成游戏 妹系 魔法 魔法少女 魔幻 模拟经营 模拟养成 魔女 末世 魔物娘 内涵 女仆 女神 女性视角 女性向 女战士 女装 女子＊＊ 偶像 妻 奇幻 蔷薇向 青春 青梅竹马 青涩三角关系 社团 兽耳 双子 探险 天使 田园 甜作 童话 同居 网络世界 伪娘 未亡人 巫女 喜剧 吸血鬼 夏 校园 新娘 悬疑 悬疑推理 学园 养成 异世界 音乐 御姐战斗 蒸汽朋克 职场 治愈 致郁 重口


</details>

<hr>

## 树状结构

### 扫描层数：4

        SakuraiZer0
        ├── bot.py
        ├── config.py
        ├── costrule.py
        ├── DataBase
        │   ├── HeadIMG
        │   ├── HelpTXT(帮助文档省略)
        │   ├── Json
        │   │   ├── datalog.json
        │   │   ├── picture_lib.json
        │   │   └── studylib.json
        │   ├── msyh.ttc
        │   └── SearchIMG
        ├── docker-compose.yml
        ├── Dockerfile
        ├── LICENSE
        ├── logo.jpg
        ├── pyproject.toml
        ├── README.md
        └── src
        └── plugins
                ├── Datalog.py
                ├── GalRecommend.py
                ├── Help.py
                ├── Info.py
                ├── Notices.py
                ├── PictureAppraisal.py
                ├── SearchPic.py
                ├── Setu.py
                ├── Study.py
                └── TextAppraisal.py

<hr>


# 鸣谢
[yanyongyu](https://github.com/yanyongyu):  方便易用利于扩展的SDK -> [Nonebot/NoneBot2](https://github.com/nonebot/nonebot2)

[Mrs4s](https://github.com/Mrs4s): 更新迭代快如疯狗的运行框架 ->  [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

[KaguraYayoi](https://github.com/Fjaxzhy): ~~提供超级高效稳定的精神支持~~ [ReadMe.md](https://github.com/Hajimarino-HOPE/SakuraiZer0/blob/main/README.md) 编写

以及群内提供建议、技术支持的各位沙雕群友
