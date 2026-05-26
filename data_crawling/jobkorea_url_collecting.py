# data_crawling/jobkorea_url_collecting.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from data_crawling.constants import REQUEST_URL, BASE_URL, DEFAULT_HEADERS, REFERER_URL, SEARCH_CONDITIONS
from data_crawling.logger import setup_logger

logger = setup_logger("url_collecting")

def collect_job_urls():
    """
    조건에 맞는 채용 공고 URL 리스트를 수집합니다.
    SEARCH_CONDITIONS['duty'] 리스트를 순회하며 모든 URL을 모읍니다.
    """
    all_collected_data = []
    duties = SEARCH_CONDITIONS.get('duty', [])
    
    # duty가 리스트가 아니면 리스트로 변환 (방어적 코드)
    if not isinstance(duties, list):
        duties = [duties]

    try:
        session = requests.Session()
        logger.info("메인 페이지 접속 중 (쿠키 획득)...")
        session.get(REFERER_URL, headers=DEFAULT_HEADERS)

        for duty_code in duties:
            logger.info(f"직무 코드 [{duty_code}] 데이터 요청 중...")
            
            payload = {
                "isDefault": SEARCH_CONDITIONS.get('isDefault', "true"),
                "condition[duty]": duty_code,
                "condition[career]": SEARCH_CONDITIONS.get('career'),
                "page": SEARCH_CONDITIONS.get('page', "1"),
                "pagesize": SEARCH_CONDITIONS.get('pagesize', "40"),
                "order": SEARCH_CONDITIONS.get('order', "20"),
                "direct": SEARCH_CONDITIONS.get('direct', "0"),
                "tabindex": SEARCH_CONDITIONS.get('tabindex', "0"),
                "onePick": SEARCH_CONDITIONS.get('onePick', "0"),
                "confirm": SEARCH_CONDITIONS.get('confirm', "0"),
                "profile": SEARCH_CONDITIONS.get('profile', "0")
            }

            response = session.post(REQUEST_URL, data=payload, headers=DEFAULT_HEADERS)
            
            if response.status_code != 200:
                logger.error(f"직무 [{duty_code}] 요청 실패. 상태 코드: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.select('td.tplTit div.titBx strong a.link')
            
            for element in job_elements:
                title = element.get_text(strip=True)
                relative_url = element.get('href')
                full_url = urljoin(BASE_URL, relative_url)
                
                # 중복 수집 방지
                if not any(item['url'] == full_url for item in all_collected_data):
                    all_collected_data.append({
                        "title": title,
                        "url": full_url
                    })
            
            logger.info(f"직무 [{duty_code}]: {len(job_elements)}개 URL 수집됨")
            
        logger.info(f"전체 총 {len(all_collected_data)}개의 유니크한 공고 URL 수집 완료")
        return all_collected_data

    except Exception as e:
        logger.exception(f"URL 수집 중 오류 발생: {e}")
        return []

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("--- URL 수집 단위 테스트 시작 ---")
    urls = collect_job_urls()
    for i, item in enumerate(urls[:5], 1):
        print(f"[{i}] {item['title']}: {item['url']}")
    print(f"총 {len(urls)}개 수집됨.")
