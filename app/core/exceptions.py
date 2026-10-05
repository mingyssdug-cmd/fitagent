class AppException(Exception):
    """所有业务异常的基类。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ValidationError(AppException):
    """参数校验失败。"""

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(code=1001, message=message)


class UnauthorizedError(AppException):
    """未登录或 token 无效。"""

    def __init__(self, message: str = "未登录或 token 无效"):
        super().__init__(code=1002, message=message)


class ForbiddenError(AppException):
    """无权访问。"""

    def __init__(self, message: str = "无权访问"):
        super().__init__(code=1003, message=message)


class NotFoundError(AppException):
    """资源不存在。"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=1004, message=message)


class ConflictError(AppException):
    """资源冲突（如手机号已注册）。"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(code=1005, message=message)


class ProfileIncompleteError(AppException):
    """用户档案不完整。"""

    def __init__(self, message: str = "用户档案不完整"):
        super().__init__(code=2001, message=message)


class CalorieTooLowError(AppException):
    """热量低于安全阈值。"""

    def __init__(self, message: str = "计划热量低于安全下限"):
        super().__init__(code=2002, message=message)


class ForbiddenExerciseError(AppException):
    """计划包含禁忌动作。"""

    def __init__(self, message: str = "计划包含禁忌动作"):
        super().__init__(code=2003, message=message)