"""
Author: SakuraiCora
Date: 2024-12-21 02:25:48
LastEditors: SakuraiCora
LastEditTime: 2024-12-28 19:46:12
Description: 消息模版构建器
"""

from datetime import datetime
from typing import Optional

from nonebot.adapters.onebot.v11 import Message

from src.config.general_config import general_config


class AlertTemplate:
    @staticmethod
    def build_exception_notification(
        user_input: str,
        exception_type: str,
        help_command: str,
        timestamp: datetime = datetime.now(),
    ) -> str:
        """
        构造异常消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param user_input: 用户的不合预期的输入内容。
        :param exception_type: 错误类型的简短描述，例如 "格式错误" 或 "未知命令"。
        :param help_command: 提供给用户的帮助文档指令。
        :param timestamp: 错误发生的时间，默认为当前时间。
        :return: 格式化的异常消息字符串。
        """

        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        message = (
            f"🚫【错误提醒】🚫\n"
            f"哎呀！您刚才的输入似乎有点问题哦~ (；´Д｀)\n\n"
            f"📝 输入内容: {user_input}\n"
            f"❌ 错误类型: {exception_type}\n"
            f"🕒 时间: {formatted_time}\n\n"
            f"👉 请查看帮助文档，了解正确的输入格式:\n"
            f"📖 指令: {help_command}\n\n"
            f"如果需要进一步帮助，请加入反馈群「{general_config.support_group_id}」💬。\n"
            f"—— 来自 SakuraiSenrin (•◡•) /💕"
        )

        return message

    @staticmethod
    def build_tip_notification(
        event_name: Optional[str],
        event_details: Optional[str | Message],
        timestamp: datetime = datetime.now(),
    ) -> Message:
        """
        构造通知消息模板，用于发送给管理员。

        :param event_name: 事件的名称，例如 "用户登录失败"。
        :param event_details: 事件的详细信息，例如 "用户尝试登录 3 次失败"。
        :param admin_name: 管理员的名字，用于个性化通知。
        :param timestamp: 事件发生的时间，默认为当前时间。
        :return: 格式化的消息字符串。
        """

        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        event_name = event_name or "未知事件"
        event_details = event_details or "未知事件"
        message = Message(
            Message.template("🌸【{}】🌸\n").format(event_name)
            + Message.template("管理员, (✿◕‿◕) 您好呀！\n\n").format(event_name)
            + Message.template("✨ 事件名称: {}\n").format(event_name)
            + Message.template("🕒 时间: {}\n").format(formatted_time)
            + Message.template("📋 详情: {}\n\n").format(event_details)
            + Message.template("请及时处理哦！(•◡•) /💕\n").format(event_name)
            + Message.template("—— 由 SakuraiSenrin 发出 💌").format(event_name)
        )

        return message

    @staticmethod
    def build_uncaught_exception_report(
        exception_id: int,
        pending_nums: int,
        total_nums: int,
        user_input: str,
        event_log: str,
        user_id: str,
        group_id: str,
        exception_type: str,
        traceback_info: str,
        exception_source: Optional[str] = None,
        timestamp: datetime = datetime.now(),
    ) -> str:
        """
        构造发送给管理员的错误报告消息，包含用户输入、错误类型和关键的traceback部分。

        :param exception_id: 异常的ID。
        :param pending_nums: 异常数量。
        :param total_nums: 总异常数量。
        :param user_input: 用户的输入内容或bot的操作描述。
        :param event_log: 用户的日志信息。
        :param user_id: 用户的ID。
        :param group_id: 群组的ID。
        :param exception_type: 错误类型的简短描述。
        :param traceback_info: 异常的traceback信息。
        :param exception_source: 发生错误的源头描述，默认为"未知"。
        :param timestamp: 错误发生的时间，默认为当前时间。
        :return: 格式化的管理员错误报告消息字符串。
        """

        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        exception_source = exception_source if exception_source else "未知"

        message = (
            f"🚨【异常警告】🚨\n"
            f"⚠️ 检测到未捕获的异常情况！\n\n"
            f"🔖 异常ID: {exception_id}\n"
            f"📊 未处理异常: {pending_nums} / {total_nums}\n"
            f"👤 用户输入: {user_input}\n"
            f"📝 日志: {event_log}\n"
            f"🆔 用户ID: {user_id}\n"
            f"📱 群组ID: {group_id}\n"
            f"❌ 错误类型: {exception_type}\n"
            f"📌 错误源: {exception_source}\n"
            f"🕒 时间: {formatted_time}\n"
            f"📄 Traceback:\n{traceback_info}\n"
            f"请尽快处理此问题！\n"
            f"—— SakuraiSenrin 警告系统"
        )

        return message


class NoticeBuilder:
    @staticmethod
    def exception(content: str) -> str:
        """
        构造异常消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 异常内容。
        :return: 格式化的异常消息字符串。

        >>> NoticeBuilder.exception("异常内容")
        '🚨 异常：异常内容'
        """
        return f"🚨 异常：{content}"

    @staticmethod
    def warning(content: str) -> str:
        """
        构造警告消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 警告内容。
        :return: 格式化的警告消息字符串。

        >>> NoticeBuilder.warning("警告内容")
        '⚠️ 提示：警告内容'
        """
        return f"⚠️ 提示：{content}"

    @staticmethod
    def info(content: str) -> str:
        """
        构造信息消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 信息内容。
        :return: 格式化的信息消息字符串。

        >>> NoticeBuilder.info("信息内容")
        'ℹ️ 信息：信息内容'
        """
        return f"ℹ️ 信息：{content}"

    @staticmethod
    def success(content: str) -> str:
        """
        构造成功消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 成功内容。
        :return: 格式化的成功消息字符串。

        >>> NoticeBuilder.success("成功内容")
        '✅ 成功：成功内容'
        """
        return f"✅ 成功：{content}"

    @staticmethod
    def notification(content: str) -> str:
        """
        构造通知消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 通知内容。
        :return: 格式化的通知消息字符串。

        >>> NoticeBuilder.notification("通知内容")
        '🔔 通知：通知内容'
        """
        return f"🔔 通知：{content}"

    @staticmethod
    def critical(content: str) -> str:
        """
        构造危急消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 危急内容。
        :return: 格式化的危急消息字符串。

        >>> NoticeBuilder.critical("危急内容")
        '🔥 危急：危急内容'
        """
        return f"🔥 危急：{content}"

    @staticmethod
    def alert(content: str) -> str:
        """
        构造警报消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 警报内容。
        :return: 格式化的警报消息字符串。

        >>> NoticeBuilder.alert("警报内容")
        '🚨 警报：警报内容'
        """
        return f"🚨 警报：{content}"

    @staticmethod
    def caution(content: str) -> str:
        """
        构造注意消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 注意内容。
        :return: 格式化的注意消息字符串。

        >>> NoticeBuilder.caution("注意内容")
        '⚠️ 注意：注意内容'
        """
        return f"⚠️ 注意：{content}"

    @staticmethod
    def reminder(content: str) -> str:
        """
        构造提醒消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 提醒内容。
        :return: 格式化的提醒消息字符串。

        >>> NoticeBuilder.reminder("提醒内容")
        '⏰ 提醒：提醒内容'
        """
        return f"⏰ 提醒：{content}"

    @staticmethod
    def progress(content: str) -> str:
        """
        构造进度消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 进度内容。
        :return: 格式化的进度消息字符串。

        >>> NoticeBuilder.progress("进度内容")
        '⏳ 进度：进度内容'
        """
        return f"⏳ 进度：{content}"

    @staticmethod
    def update(content: str) -> str:
        """
        构造更新消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 更新内容。
        :return: 格式化的更新消息字符串。

        >>> NoticeBuilder.update("更新内容")
        '🔄 更新：更新内容'
        """
        return f"🔄 更新：{content}"

    @staticmethod
    def maintenance(content: str) -> str:
        """
        构造维护消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 维护内容。
        :return: 格式化的维护消息字符串。

        >>> NoticeBuilder.maintenance("维护内容")
        '🛠️ 维护：维护内容'
        """
        return f"🛠️ 维护：{content}"

    @staticmethod
    def approval(content: str) -> str:
        """
        构造审批消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 审批内容。
        :return: 格式化的审批消息字符串。

        >>> NoticeBuilder.approval("审批内容")
        '👍 审批：审批内容'
        """
        return f"👍 审批：{content}"

    @staticmethod
    @staticmethod
    def rejection(content: str) -> str:
        """
        构造拒绝消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 拒绝内容。
        :return: 格式化的拒绝消息字符串。

        >>> NoticeBuilder.rejection("拒绝内容")
        '❌ 拒绝：拒绝内容'
        """
        return f"❌ 拒绝：{content}"

    @staticmethod
    def suggestion(content: str) -> str:
        """
        构造建议消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 建议内容。
        :return: 格式化的建议消息字符串。

        >>> NoticeBuilder.suggestion("建议内容")
        '💡 建议：建议内容'
        """
        return f"💡 建议：{content}"

    @staticmethod
    def question(content: str) -> str:
        """
        构造问题消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 问题内容。
        :return: 格式化的问题消息字符串。

        >>> NoticeBuilder.question("问题内容")
        '❓ 问题：问题内容'
        """
        return f"❓ 问题：{content}"

    @staticmethod
    def feedback(content: str) -> str:
        """
        构造反馈消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 反馈内容。
        :return: 格式化的反馈消息字符串。

        >>> NoticeBuilder.feedback("反馈内容")
        '🗣️ 反馈：反馈内容'
        """
        return f"🗣️ 反馈：{content}"

    @staticmethod
    def debug(content: str) -> str:
        """
        构造调试消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 调试内容。
        :return: 格式化的调试消息字符串。

        >>> NoticeBuilder.debug("调试内容")
        '🐞 调试：调试内容'
        """
        return f"🐞 调试：{content}"

    @staticmethod
    def log(content: str) -> str:
        """
        构造日志消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 日志内容。
        :return: 格式化的日志消息字符串。

        >>> NoticeBuilder.log("日志内容")
        '📝 日志：日志内容'
        """
        return f"📝 日志：{content}"

    @staticmethod
    def access(content: str) -> str:
        """
        构造访问消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 访问内容。
        :return: 格式化的访问消息字符串。

        >>> NoticeBuilder.access("访问内容")
        '🔑 访问：访问内容'
        """
        return f"🔑 访问：{content}"

    @staticmethod
    def security(content: str) -> str:
        """
        构造安全消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 安全内容。
        :return: 格式化的安全消息字符串。

        >>> NoticeBuilder.security("安全内容")
        '🔐 安全：安全内容'
        """
        return f"🔐 安全：{content}"

    @staticmethod
    def feature(content: str) -> str:
        """
        构造功能消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 功能内容。
        :return: 格式化的功能消息字符串。

        >>> NoticeBuilder.feature("功能内容")
        '✨ 功能：功能内容'
        """
        return f"✨ 功能：{content}"

    @staticmethod
    def fix(content: str) -> str:
        """
        构造修复消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 修复内容。
        :return: 格式化的修复消息字符串。

        >>> NoticeBuilder.fix("修复内容")
        '🐛 修复：修复内容'
        """
        return f"🐛 修复：{content}"

    @staticmethod
    def performance(content: str) -> str:
        """
        构造性能消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 性能内容。
        :return: 格式化的性能消息字符串。

        >>> NoticeBuilder.performance("性能内容")
        '⚡️ 性能：性能内容'
        """
        return f"⚡️ 性能：{content}"

    @staticmethod
    def build(content: str) -> str:
        """
        构造构建消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 构建内容。
        :return: 格式化的构建消息字符串。

        >>> NoticeBuilder.build("构建内容")
        '🏗️ 构建：构建内容'
        """
        return f"🏗️ 构建：{content}"

    @staticmethod
    def deploy(content: str) -> str:
        """
        构造部署消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 部署内容。
        :return: 格式化的部署消息字符串。

        >>> NoticeBuilder.deploy("部署内容")
        '🚀 部署：部署内容'
        """
        return f"🚀 部署：{content}"

    @staticmethod
    def refactor(content: str) -> str:
        """
        构造重构消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 重构内容。
        :return: 格式化的重构消息字符串。

        >>> NoticeBuilder.refactor("重构内容")
        '♻️ 重构：重构内容'
        """
        return f"♻️ 重构：{content}"

    @staticmethod
    def test(content: str) -> str:
        """
        构造测试消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 测试内容。
        :return: 格式化的测试消息字符串。

        >>> NoticeBuilder.test("测试内容")
        '🧪 测试：测试内容'
        """
        return f"🧪 测试：{content}"

    @staticmethod
    def remove(content: str) -> str:
        """
        构造删除消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 删除内容。
        :return: 格式化的删除消息字符串。

        >>> NoticeBuilder.remove("删除内容")
        '🔥 删除：删除内容'
        """
        return f"🔥 删除：{content}"

    @staticmethod
    def style(content: str) -> str:
        """
        构造样式消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 样式内容。
        :return: 格式化的样式消息字符串。

        >>> NoticeBuilder.style("样式内容")
        '💄 样式：样式内容'
        """
        return f"💄 样式：{content}"

    @staticmethod
    def docs(content: str) -> str:
        """
        构造文档消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 文档内容。
        :return: 格式化的文档消息字符串。

        >>> NoticeBuilder.docs("文档内容")
        '📝 文档：文档内容'
        """
        return f"📝 文档：{content}"

    @staticmethod
    def config(content: str) -> str:
        """
        构造配置消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 配置内容。
        :return: 格式化的配置消息字符串。

        >>> NoticeBuilder.config("配置内容")
        '🔧 配置：配置内容'
        """
        return f"🔧 配置：{content}"

    @staticmethod
    def lint(content: str) -> str:
        """
        构造规范消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 规范内容。
        :return: 格式化的规范消息字符串。

        >>> NoticeBuilder.lint("规范内容")
        '🚨 规范：规范内容'
        """
        return f"🚨 规范：{content}"

    @staticmethod
    def experiment(content: str) -> str:
        """
        构造实验消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 实验内容。
        :return: 格式化的实验消息字符串。

        >>> NoticeBuilder.experiment("实验内容")
        '⚗️ 实验：实验内容'
        """
        return f"⚗️ 实验：{content}"

    @staticmethod
    def access_control(content: str) -> str:
        """
        构造权限消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 权限内容。
        :return: 格式化的权限消息字符串。

        >>> NoticeBuilder.access_control("权限内容")
        '🔒 权限：权限内容'
        """
        return f"🔒 权限：{content}"

    @staticmethod
    def localization(content: str) -> str:
        """
        构造本地化消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 本地化内容。
        :return: 格式化的本地化消息字符串。

        >>> NoticeBuilder.localization("本地化内容")
        '🌍 本地化：本地化内容'
        """
        return f"🌍 本地化：{content}"

    @staticmethod
    def welcome(content: str) -> str:
        """
        构造欢迎消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 欢迎内容。
        :return: 格式化的欢迎消息字符串。

        >>> NoticeBuilder.welcome("欢迎内容")
        '👋 欢迎：欢迎内容'
        """
        return f"👋 欢迎：{content}"

    @staticmethod
    def thanks(content: str) -> str:
        """
        构造感谢消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 感谢内容。
        :return: 格式化的感谢消息字符串。

        >>> NoticeBuilder.thanks("感谢内容")
        '🙏 感谢：感谢内容'
        """
        return f"🙏 感谢：{content}"

    @staticmethod
    def congratulation(content: str) -> str:
        """
        构造恭喜消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 恭喜内容。
        :return: 格式化的恭喜消息字符串。

        >>> NoticeBuilder.congratulation("恭喜内容")
        '🎉 恭喜：恭喜内容'
        """
        return f"🎉 恭喜：{content}"

    @staticmethod
    def update_available(content: str) -> str:
        """
        构造更新可用消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 更新可用内容。
        :return: 格式化的更新可用消息字符串。

        >>> NoticeBuilder.update_available("更新可用内容")
        '🔄 更新可用：更新可用内容'
        """
        return f"🔄 更新可用：{content}"

    @staticmethod
    def payment(content: str) -> str:
        """
        构造付款消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 付款内容。
        :return: 格式化的付款消息字符串。

        >>> NoticeBuilder.payment("付款内容")
        '💰 付款：付款内容'
        """
        return f"💰 付款：{content}"

    @staticmethod
    def invitation(content: str) -> str:
        """
        构造邀请消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 邀请内容。
        :return: 格式化的邀请消息字符串。

        >>> NoticeBuilder.invitation("邀请内容")
        '✉️ 邀请：邀请内容'
        """
        return f"✉️ 邀请：{content}"

    @staticmethod
    def achievement(content: str) -> str:
        """
        构造成就消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 成就内容。
        :return: 格式化的成就消息字符串。

        >>> NoticeBuilder.achievement("成就内容")
        '🏆 成就：成就内容'
        """
        return f"🏆 成就：{content}"

    @staticmethod
    def promotion(content: str) -> str:
        """
        构造优惠消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 优惠内容。
        :return: 格式化的优惠消息字符串。

        >>> NoticeBuilder.promotion("优惠内容")
        '🎁 优惠：优惠内容'
        """
        return f"🎁 优惠：{content}"

    @staticmethod
    def downtime(content: str) -> str:
        """
        构造停机消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 停机内容。
        :return: 格式化的停机消息字符串。

        >>> NoticeBuilder.downtime("停机内容")
        '🚧 停机：停机内容'
        """
        return f"🚧 停机：{content}"

    @staticmethod
    def security_alert(content: str) -> str:
        """
        构造警报消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 警报内容。
        :return: 格式化的警报消息字符串。

        >>> NoticeBuilder.security_alert("警报内容")
        '🔐 警报：警报内容'
        """
        return f"🔐 警报：{content}"

    @staticmethod
    def farewell(content: str) -> str:
        """
        构造告别消息模板，用于提示用户输入错误，并提供帮助文档或具体指令。

        :param content: 告别内容。
        :return: 格式化的告别消息字符串。

        >>> NoticeBuilder.farewell("告别内容")
        '👋 告别：告别内容'
        """
        return f"👋 告别：{content}"
