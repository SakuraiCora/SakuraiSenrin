class CannotModifyTriggerRuleConditionsException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DuplicateTriggerResponseException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PermissionDeniedException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
