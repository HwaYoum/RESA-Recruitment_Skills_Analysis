# data_crawling/jobkorea_web_craling.py

import sys
import os
import time
import requests

# 현재 디렉토리를 path에 추가하여 모듈 임포트 가능하게 함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_crawling.jobkorea_url_collecting import collect_job_urls
from data_crawling.jobkorea_data_collecting import scrape_job_detail
from data_crawling.logger import setup_logger
from data_crawling.constants import DEFAULT_HEADERS

logger = setup_logger("main_crawler")

def run_crawler():
    """
    잡코리아 웹 크롤러 통합 실행기
    """
    logger.info("=== 잡코리아 크롤링 프로세스 시작 ===")
    
    # 1. URL 수집
    job_list = collect_job_urls()
    
    if not job_list:
        logger.warning("수집된 공고가 없습니다. 프로세스를 종료합니다.")
        return

    logger.info(f"{len(job_list)}개의 공고를 찾았습니다. 상세 정보 수집을 시작합니다.")

    # 2. 데이터 수집 (상세 페이지 요청 간 세션 유지 및 지연 시간 추가)
    results = []
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    
    try:
        for i, item in enumerate(job_list[:5], 1):
            detail = scrape_job_detail(item['url'], session=session)
            if detail:
                results.append({
                    "title": item['title'],
                    "url": item['url'],
                    **detail
                })
            
            # 요청 간 1초 지연 (서버 부하 방지 및 연결 안정성 확보)
            if i < len(job_list[:5]):
                time.sleep(1)
    finally:
        session.close()

    logger.info(f"=== 크롤링 프로세스 종료. 총 {len(results)}개 데이터 처리 완료 ===")
    
    # 결과 요약 출력
    for i, res in enumerate(results, 1):
        print(f"[{i}] {res['title']} ({res['company']})")
        print(f"    분석결과: {res['analysis']['summary']}")

if __name__ == "__main__":
    # 출력 인코딩 설정
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    run_crawler()
