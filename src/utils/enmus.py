"""
Author: SakuraiCora
Date: 2024-12-21 12:43:47
LastEditors: SakuraiCora
LastEditTime: 2024-12-27 21:40:21
Description: 枚举类
"""

from enum import Enum


class ExceptionStatusEnum(str, Enum):
    PROCESSED = "PROCESSED"
    PENDING = "PENDING"
    IGNORE = "IGNORE"


class InvitationStatusEnum(str, Enum):
    PENDING = "PENDING"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class GroupStatusEnum(str, Enum):
    REMOVE = "REMOVE"
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    LEAVE = "LEAVE"
    BAN = "BAN"
    UNAUTH = "UNAUTH"


class UserStatusEnum(str, Enum):
    DELETE = "DELETE"
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    BAN = "BAN"


class MemberStatusEnum(str, Enum):
    DISABLE = "DISABLE"
    ENABLE = "ENABLE"
    LEAVE = "LEAVE"
    BAN = "BAN"


class OnebotV11EventEnum(str, Enum):
    EVENT = "Event"
    MESSAGEEVENT = "MessageEvent"
    PRIVATEMESSAGEEVENT = "PrivateMessageEvent"
    GROUPMESSAGEEVENT = "GroupMessageEvent"
    NOTICEEVENT = "NoticeEvent"
    GROUPUPLOADNOTICEEVENT = "GroupUploadNoticeEvent"
    GROUPADMINNOTICEEVENT = "GroupAdminNoticeEvent"
    GROUPDECREASENOTICEEVENT = "GroupDecreaseNoticeEvent"
    GROUPINCREASENOTICEEVENT = "GroupIncreaseNoticeEvent"
    GROUPBANNOTICEEVENT = "GroupBanNoticeEvent"
    FRIENDADDNOTICEEVENT = "FriendAddNoticeEvent"
    GROUPRECALLNOTICEEVENT = "GroupRecallNoticeEvent"
    FRIENDRECALLNOTICEEVENT = "FriendRecallNoticeEvent"
    NOTIFYEVENT = "NotifyEvent"
    POKENOTIFYEVENT = "PokeNotifyEvent"
    LUCKYKINGNOTIFYEVENT = "LuckyKingNotifyEvent"
    HONORNOTIFYEVENT = "HonorNotifyEvent"
    REQUESTEVENT = "RequestEvent"
    FRIENDREQUESTEVENT = "FriendRequestEvent"
    GROUPREQUESTEVENT = "GroupRequestEvent"
    METAEVENT = "MetaEvent"
    LIFECYCLEMETAEVENT = "LifecycleMetaEvent"
    HEARTBEATMETAEVENT = "HeartbeatMetaEvent"


class TriggerTypeEnum(str, Enum):
    ACTIVE = "Active"
    PASSIVE = "Passive"


class PluginPermissionEnum(str, Enum):
    SUPERUSER = "SUPERUSER"
    GROUPADMIN = "GROUPADMIN"
    EVERYONE = "EVERYONE"


class ApprovalStatusEnum(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"

    def __str__(self):
        translations = {
            "Pending": "待审批 🕒",
            "Approved": "已通过 ✅",
            "Rejected": "已拒绝 ❌",
            "Withdrawn": "已撤回 🔄",
        }
        return translations.get(self.value, self.value)


class VoteOptionEnum(str, Enum):
    SUPPORT = "Support"
    OPPOSE = "Oppose"

    def __str__(self):
        translations = {
            "Support": "支持 👍",
            "Oppose": "反对 👎",
        }
        return translations.get(self.value, self.value)


class VoteStatusEnum(str, Enum):
    IN_PROGRESS = "In Progress"
    SUPPORT = "Support"
    OPPOSE = "Oppose"

    def __str__(self):
        translations = {
            "In Progress": "投票中 🔄",
            "Support": "支持 👍",
            "Oppose": "反对 👎",
        }
        return translations.get(self.value, self.value)
