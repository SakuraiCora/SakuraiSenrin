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
    MESSAGE_EVENT = "MessageEvent"
    PRIVATE_MESSAGE_EVENT = "PrivateMessageEvent"
    GROUP_MESSAGE_EVENT = "GroupMessageEvent"
    NOTICE_EVENT = "NoticeEvent"
    GROUP_UPLOAD_NOTICE_EVENT = "GroupUploadNoticeEvent"
    GROUP_ADMIN_NOTICE_EVENT = "GroupAdminNoticeEvent"
    GROUP_DECREASE_NOTICE_EVENT = "GroupDecreaseNoticeEvent"
    GROUP_INCREASE_NOTICE_EVENT = "GroupIncreaseNoticeEvent"
    GROUP_BAN_NOTICE_EVENT = "GroupBanNoticeEvent"
    FRIEND_ADD_NOTICE_EVENT = "FriendAddNoticeEvent"
    GROUP_RECALL_NOTICE_EVENT = "GroupRecallNoticeEvent"
    FRIEND_RECALL_NOTICE_EVENT = "FriendRecallNoticeEvent"
    NOTIFY_EVENT = "NotifyEvent"
    POKE_NOTIFY_EVENT = "PokeNotifyEvent"
    LUCKY_KING_NOTIFY_EVENT = "LuckyKingNotifyEvent"
    HONOR_NOTIFY_EVENT = "HonorNotifyEvent"
    REQUEST_EVENT = "RequestEvent"
    FRIEND_REQUEST_EVENT = "FriendRequestEvent"
    GROUP_REQUEST_EVENT = "GroupRequestEvent"
    META_EVENT = "MetaEvent"
    LIFECYCLE_META_EVENT = "LifecycleMetaEvent"
    HEARTBEAT_META_EVENT = "HeartbeatMetaEvent"


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


class WordbankExtraActionEnum(str, Enum):
    AT_MENTIONED = "AT_MENTIONED"
    POKE_MENTIONED = "POKE_MENTIONED"
    GROUP_JOIN = "GROUP_JOIN"
    GROUP_LEAVE = "GROUP_LEAVE"
