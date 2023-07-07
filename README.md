<div align="center">
        <img src="https://cdn.jsdelivr.net/gh/Hajimarino-HOPE/SakuraiSenrin/docs/img/Senrin-logo.png" width="150px" height="150px" width="150px" height="150px" alt="SakuraiSenrin-Logo"/>

# SenrinSenrin
### 打造一款服务于GalGame玩家的轻量级QQ机器人

[![](https://img.shields.io/badge/Lang-Python-FF1493)](https://python.org)
[![](https://img.shields.io/badge/Frame-go_cqhttp-7B68EE)](https://github.com/Mrs4s/go-cqhttp)
[![](https://img.shields.io/badge/SDK-NoneBot2-3CB371)](https://github.com/nonebot/nonebot2)
[![](https://img.shields.io/badge/Author-SakuraiCora-F08080)](https://github.com/Hajimarino-HOPE)
[![](https://img.shields.io/github/license/Hajimarino-HOPE/SakuraiSenrin)](https://github.com/Hajimarino-HOPE/SakuraiSenrin/blob/main/LICENSE)

</div>
<hr>

# 概览
### 本项目作为第一代(使用NoneBot1)的升级项目
### 由于程序写法的大幅度改变，所有功能正在从第一代移植中......
###	DemoQQ：1768641952（暂时关闭  **涩图**  功能）
	> 好友验证码：Senrin（注意区分大小写）

---
# 更新
- 2023.7.6
  - 老鸽子了🕊🕊🕊写了两个多月了现在才更新
  - NEW✨
    - 新增 **词库搜索** 功能
    - 新增 **群组隔离** 功能
    - 新增 **多词条** 功能
    - ~~把群群友们的词库端上来了（~~
  - FIX🔧
    - 重构 **study** 相关功能
    - 修复 **show** 相关问题
    - 修复 **菜单sql误判** 相关问题
- 2023.1.29
  - 新年快乐（吧）🎉
  - NEW✨
    - 新增 **今天食堂吃什么** 功能
    - 新增 **内置戳一戳** 词库
    - 新增 **随机美图** 功能
  - FIX🔧
    - 修复 **发言记录无法重置** 的问题
    - 重构 **Water** 功能
    - 重构 **涩图** 相关功能
    - 修复 **搜图** 意外错误
    - 修复 **异常处理** 方案
    - 修复 **Rule** 相关逻辑错误
    - ~~美化（？）项目结构和代码~~
- 2022.7.28
  - 修复Linux下数据库路径问题
  - adapter更换为onebotV11
  - 图片改为byteIO方式发送，减少空间占用
  - **链接鉴定** 功能移除
  - **搜图**移除私聊发送
- 2022.6.29
  - Gal功能回归，采用Sqlite3
  - 修复proxy问题
  - 修复图片消息不匹配问题，转为bytes发送
- 2022.6.15
  - 腾讯Σ
  - 增加异常处理（返回报错）
  - Gal功能因不可抗力归档
  - 大部分修改为MessageSegment构造，防止注入
  - 修复若干bug，优化消息文本
- 2022.6.9
  - 回坑
  - 修正  **ReadMe**  错别字
  - 更改目录结构
  - ......
- 2021.8.1
  - 完成消息版帮助文档
  - 修复路径bug
  - 新增内置词库
- 2021.7.2
  - 樱井千凛人设V1.0发布
- 2021.6.30  
  - 完成移植 **GalGame随机推荐** 功能
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


## 按功能分类
<details><summary>被动触发型集合</summary>

>1. 违规图识别
>2. ~~蓝链检测（已废弃）~~
>3. 通知上报
>4. 戳一戳随机回复
>5. at随机回复

</details>

<details><summary>帮助文档</summary>

- #help &lt;FunctionID>

  > 示例：#help AWHD
	- 发送 **功能代码** 为 ***functionID*** 的帮助文档
	- 若FunctionID为空，则发送 **功能代码列表**


</details>

<details><summary>词库学习</summary>

- #study module Q A

  > 示例：#study A Senrin nmd叫我搞锤子？！

  - 让Senrin在用户发送 **Q** 的对于 **module** 回答 **A**
  - mudule参数：A（全局相应）P（个人相应）
  - Q为感知语（不能含有空格，默认严格匹配，区分大小写）
  - A为应答语（不能含有空格）

- lib_manage show（仅bot管理员）

  > 示例：#lib_manage show

  - 以图片的格式展示词库 

- lib_manage search（仅bot管理员）

  > 示例：#lib_manage show

  - 以图片的格式展示词库 

<!-- - #lib_manage del class uesr_id key（仅bot管理员）

  > 示例：#lib_manage del public all_users Senrin

	- 删除 **studylib['class']['user_id']** 对应的词库条例
	- class参数：public（全局相应）private（个人响应）
	- user_id参数：
  	- 若class为public， 则填入 **all_users**
    - 若class为private，则填入 **用户QQ号** -->

</details>

<details><summary>群聊发言次数查询</summary>

- #water <@user>

  > 示例：#water
  >
  > 示例：#water @Senrin

	- 获取@对象的当天在本群的发言次数
	- 若<@user>为空，则获取自己的发言次数

- #water list

  > 示例：#water list

	- 获取当天在本群的 **发言次数排行榜** 

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
  > 示例：#info @Senrin

  - 根据有限的信息制作简单资料卡 
  - 若\<@user>为空，则制作自己的资料卡 
  - ~~（你甚至可以看看Senrin的资料卡）~~ 

</details>

<details><summary>搜图</summary>

  >示例：~~示不出来~~

- 【Reply】回复想搜的图
	- 通过 **SauceNAO** 提供的API进行搜图 

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
  
- #taglist

	>示例：#taglist
	
	
	- 列出tag参数
	
	
	

</details>

<details><summary>*今天食堂吃什么</summary>


  >示例：#eat

不知道今天吃什么？试试这个！仅需根据Senrin的指令即可~

- 添加菜单（名为menu.json，小于100kb的标准json文件）发送至Senrin即可

- ```json
  {
  "学校1":{
          "食堂1":[
              "菜名1 子菜名1 价格 等待时间 食物类型 标识",
              "菜名2 子菜名2 价格 等待时间 食物类型 标识",
              "菜名3 子菜名3 价格 等待时间 食物类型 标识"
          ],
          "食堂2":[
              "菜名4 子菜名4 价格 等待时间 食物类型 标识",
              "菜名5 子菜名5 价格 等待时间 食物类型 标识",
              "菜名6 子菜名6 价格 等待时间 食物类型 标识",
          ]
      }
  }
  ```

  以此类推，示例文件在 `Plugin/RandomEat/menu.json`

</details>

# 鸣谢
[yanyongyu](https://github.com/yanyongyu):  方便易用利于扩展的SDK -> [Nonebot/NoneBot2](https://github.com/nonebot/nonebot2)

[Mrs4s](https://github.com/Mrs4s): 更新迭代快如疯狗的运行框架 ->  [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)

[KaguraYayoi](https://github.com/Fjaxzhy): ~~提供超级高效稳定的精神支持~~ [ReadMe.md](https://github.com/Hajimarino-HOPE/SakuraiSenrin/blob/main/README.md) 编写

以及群内提供建议、技术支持的各位沙雕群友
