import random

from nonebot.typing import T_State
from nonebot.params import CommandArg
from nonebot.plugin import on_command, on_message
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent


from Utils.ImageUtils import WordBankImg
from Utils.CustomRule import check_white_list, only_master

from .StudyClass import StudyCmd, LibCmd, studylib

study = on_command("study", priority=5,rule=check_white_list())
get_march = on_message(rule=check_white_list(), priority=5)
lib_manage = on_command('lib_manage', priority=5,rule=only_master())

async def study_opt(state):
    study_cmd:StudyCmd = state['study_cmd']
    setattr(study_cmd, state['_next_target'], await StudyCmd.handleCQ(str(state[state['_next_target']])))
    try:
        study_cmd.checker()
    except Exception as e:
        return str(e)


@study.handle()
async def _study_handle(event:MessageEvent, state: T_State, args:Message = CommandArg()):
    try:
        if arg := await StudyCmd.study_command_init(args):
            arg.user_id = event.get_user_id()
            if isinstance(event, GroupMessageEvent):
                arg.key_id = str(event.group_id)
            else:
                arg.model = 'm'
                arg.block = 't'
                arg.key_id = event.get_user_id()
            for key in arg.__dict__:
                state[key] = getattr(arg,key)
            state['study_cmd'] = arg
            arg.checker()
    except Exception as e:
        await study.finish(str(e))


@study.got('model', prompt="请选择模式：\n  A（公共词库）\n  M（私人词库）")
async def _stduy_got_model(state: T_State):
    if _:=await study_opt(state):
        await study.reject(_)
    if str(state['model']).lower() == 'm':
        state['block'] = 't'


@study.got('block', prompt="是否开启群组隔离？\n  T（开启隔离）\n  F（关闭隔离）")
async def _stduy_got_block(state: T_State):
    if _:=await study_opt(state):
        await study.reject(_)


@study.got('question', prompt="问题呢？")
async def _stduy_got_question(state: T_State):
    if _:=await study_opt(state):
        await study.reject(_)


@study.got('answer', prompt="答案呢？")
async def _stduy_got_answer(state: T_State):
    if _:=await study_opt(state):
        await study.reject(_)


@study.got('study_cmd')
async def _stduy_got_cmd(state: T_State):
    global studylib
    study_cmd:StudyCmd = state['study_cmd']
    try:
        studylib = study_cmd.update(studylib)
        msg = f"好耶！学会了新东西！\n"\
            f"model: {study_cmd.model}\n"\
            f"keywd: {study_cmd.question}\n"\
            f"value: {study_cmd.answer}\n"\
            f"block: {study_cmd.block}\n"\
            f"limit: {study_cmd.key_id}\n"
    except ValueError as e:
        msg = str(e)
    await study.finish(Message(msg))


@get_march.handle()
async def _get_march(event: MessageEvent):
    """回复优先级：
    私人词库 > 群组隔离词库 > 群组共有词库
    """
    march_message = None
    rcv_message = await StudyCmd.handleCQ(str(event.get_message()))
    try:
        march_message = random.choice(studylib.friend[event.get_user_id()].__root__[rcv_message]).value
    except:
        if isinstance(event, GroupMessageEvent):
            try:
                march_message = random.choice(studylib.group[str(event.group_id)].__root__[rcv_message]).value
            except:
                try:
                    march_message = random.choice(studylib.group['global'].__root__[rcv_message]).value
                except:...
    if march_message:
        await get_march.finish(Message(march_message))   #TODO
    else:
        await get_march.finish()


@lib_manage.handle()
async def _lib_manage_handle(state:T_State ,args:Message = CommandArg()):
    arg = str(args).strip().split(" ")
    if arg[0].lower() == 'show':
        try:
            git_link = await LibCmd.get_gist_link()
        except Exception as e:
            await lib_manage.finish(str(e))
        else:
            await lib_manage.finish(f"现有词库如下：\n{git_link}")

    elif arg[0].lower() == 'search':
        """搜索模式：
        搜索范围：k v a t
        关键词：str
        """
        lib_cmd = LibCmd()
        try:
            lib_cmd.lib_cmd_init(arg[1:])
        except ValueError as e:
            await lib_manage.finish(str(e))
        else:
            if result:=lib_cmd.result:
                if len(result) > 1:
                    await lib_manage.send(f"搜索结果共有{len(result)}页，请指定页数")
                    state['func'] = 'search'
                    state['keywd'] = lib_cmd.keywd
                    state['result'] = result
                else:
                    msg = MessageSegment.image(WordBankImg().wordBankResultImg(lib_cmd.keywd, result))
                    await lib_manage.finish(msg)
            else:
                await lib_manage.finish("未找到与关键词匹配的词库T_T")

    elif arg[0].lower() == 'del':
        ...

    else:
        await lib_manage.finish()


@lib_manage.got('page')
async def _lib_manage_page(state: T_State):
    try:
        page = int(state['page'])
        if not(0 < page < len(state['result'])):
            raise Exception
    except:
        await lib_manage.reject(f"页数不符合预期，共{len(state['result'])}页")
    else:
        msg = MessageSegment.image(WordBankImg().wordBankResultImg(state['keywd'], state['result'], page))
        await lib_manage.send(msg)
        if state['func'] == 'search':
            await lib_manage.finish()


@lib_manage.got('index_', prompt="请输入要删除的词条序号")
async def _lib_manage_del(state: T_State):
    ...