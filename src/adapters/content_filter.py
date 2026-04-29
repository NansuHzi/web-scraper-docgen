import re
from typing import Tuple, Optional


class ContentFilter:
    """内容安全过滤器 - 检测并过滤敏感内容"""

    SENSITIVE_PATTERNS = [
        (r'色情|淫秽|黄色|se情|成人内容', '色情内容'),
        (r'赌博|博彩|彩票|投注', '赌博内容'),
        (r'毒品|鸦片|大麻|化学合成', '毒品相关内容'),
        (r'暴力|血腥|恐怖|杀人', '暴力内容'),
        (r'诈骗|欺诈|钓鱼|木马', '诈骗内容'),
        (r'邪教|反动|颠覆|分裂', '违法内容'),
    ]

    URL_BLOCKLIST = [
        'xxx', 'porn', 'sex', 'gambling', 'casino',
        'betting', 'drug', 'violence', 'scam', 'phishing'
    ]

    @classmethod
    def check_url_safety(cls, url: str) -> Tuple[bool, Optional[str]]:
        """
        检查URL安全性
        :param url: 目标URL
        :return: (是否安全, 违规原因)
        """
        url_lower = url.lower()

        for blocked in cls.URL_BLOCKLIST:
            if blocked in url_lower:
                return False, f"URL包含禁止关键词: {blocked}"

        return True, None

    @classmethod
    def detect_sensitive_content(cls, content: str) -> Tuple[bool, Optional[str]]:
        """
        检测内容中的敏感信息
        :param content: 待检测内容
        :return: (是否合规, 违规原因)
        """
        if not content:
            return True, None

        for pattern, category in cls.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return False, f"检测到{category}"

        return True, None

    @classmethod
    def filter_content(cls, content: str, replace_char: str = '[内容已过滤]') -> str:
        """
        过滤内容中的敏感词
        :param content: 原始内容
        :param replace_char: 替换字符
        :return: 过滤后的内容
        """
        filtered = content

        for pattern, _ in cls.SENSITIVE_PATTERNS:
            filtered = re.sub(pattern, replace_char, filtered, flags=re.IGNORECASE)

        return filtered

    @classmethod
    def validate_request(cls, url: str, content: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        全面验证请求安全性
        :param url: 目标URL
        :param content: 可选的内容检测
        :return: (是否通过, 错误信息)
        """
        url_safe, url_error = cls.check_url_safety(url)
        if not url_safe:
            return False, url_error

        if content:
            content_safe, content_error = cls.detect_sensitive_content(content)
            if not content_safe:
                return False, content_error

        return True, None