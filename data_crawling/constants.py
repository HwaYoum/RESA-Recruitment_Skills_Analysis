# data_crawling/constants.py

BASE_URL = "https://www.jobkorea.co.kr"
REQUEST_URL = "https://www.jobkorea.co.kr/Recruit/Home/_GI_List/"
REFERER_URL = "https://www.jobkorea.co.kr/recruit/joblist?menucode=duty"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": REFERER_URL,
    "X-Requested-With": "XMLHttpRequest"
}

# 검색 조건 설정
SEARCH_CONDITIONS = {
    "isDefault": "true",
    "duty": ["1000230"],    # 프론트엔드개발자 (리스트로 관리)
    "career": "1",          # 신입
    "page": "1",
    "pagesize": "40",
    "order": "20",
    "direct": "0",
    "tabindex": "0",
    "onePick": "0",
    "confirm": "0",
    "profile": "0"
}

# 로깅 설정
LOGGING_CONFIG = {
    "level": "INFO",
    "filename": "crawler.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# 수집할 정보 항목
TARGET_EXTRACTION_FIELDS = [
    "핵심 업무 (주요 역할)",
    "지원 자격 (필요 스택, 학력, 경력 등)",
    "우대 사항",
    "복지 및 근무 혜택"
]
