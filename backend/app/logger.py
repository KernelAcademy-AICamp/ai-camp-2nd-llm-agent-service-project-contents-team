"""
중앙 집중식 로깅 설정 모듈
"""
import logging
import sys

# 로그 포맷 설정
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 컬러 코드 (터미널 출력용)
class LogColors:
    RESET = "\033[0m"
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"   # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[35m"  # Magenta


class ColoredFormatter(logging.Formatter):
    """컬러 출력을 지원하는 로그 포맷터"""

    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, LogColors.RESET)
        record.levelname = f"{log_color}{record.levelname}{LogColors.RESET}"
        return super().format(record)


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    로거 설정

    Args:
        name: 로거 이름 (보통 모듈명)
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False

    # 콘솔 핸들러 (컬러 출력)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # UTF-8 인코딩 설정 (Windows 한글 깨짐 방지)
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # Windows에서 ANSI 컬러 지원 (Python 3.10+에서는 자동 지원)
    try:
        import colorama
        colorama.init()
        console_formatter = ColoredFormatter(LOG_FORMAT, DATE_FORMAT)
    except ImportError:
        # colorama가 없으면 일반 포맷터 사용
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 로깅은 비활성화 (콘솔 출력만 사용)
    # 파일 로깅이 필요한 경우 아래 주석을 해제하세요
    # from pathlib import Path
    # LOG_DIR = Path(__file__).parent.parent / "logs"
    # LOG_DIR.mkdir(exist_ok=True)
    # file_handler = logging.FileHandler(LOG_DIR / f"{name}.log", encoding="utf-8")
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    # logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기 (이미 설정되어 있으면 재사용)

    Args:
        name: 로거 이름

    Returns:
        로거 객체
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
