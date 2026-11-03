class AppException(Exception):
    """业务异常：由全局异常处理器统一转换为 {code, message, data} 响应"""

    def __init__(self, message: str, code: int = 400, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data
