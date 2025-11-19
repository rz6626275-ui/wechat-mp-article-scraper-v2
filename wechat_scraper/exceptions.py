"""
自定义异常类，用于更精确的错误处理
"""

class WeChatScraperException(Exception):
    """基础异常类"""
    pass

class AuthenticationError(WeChatScraperException):
    """认证失败异常"""
    pass

class RateLimitError(WeChatScraperException):
    """频率限制异常"""
    def __init__(self, message="触发频率限制", reset_time=None):
        self.reset_time = reset_time
        super().__init__(message)

class AccountNotFoundError(WeChatScraperException):
    """公众号未找到异常"""
    pass

class ArticleNotFoundError(WeChatScraperException):
    """文章未找到异常"""
    pass

class DownloadError(WeChatScraperException):
    """下载失败异常"""
    pass

class NetworkError(WeChatScraperException):
    """网络错误异常"""
    pass

class ContentParseError(WeChatScraperException):
    """内容解析错误异常"""
    pass
