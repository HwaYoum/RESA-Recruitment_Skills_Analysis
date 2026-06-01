# data_crawling/jobkorea_url_collecting.py

import requests
import csv
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from data_crawling.constants import REQUEST_URL, BASE_URL, DEFAULT_HEADERS, REFERER_URL, SEARCH_CONDITIONS
from data_crawling.logger import setup_logger

logger = setup_logger("url_collecting")

def get_existing_urls(filename="jobkorea_results.csv"):
    """CSV 파일에서 이미 수집된 URL 목록을 가져옵니다."""
    existing_urls = set()
    if os.path.isfile(filename):
        try:
            with open(filename, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'url' in row:
                        existing_urls.add(row['url'])
            logger.info(f"📂 기존 파일에서 {len(existing_urls)}개의 URL을 로드했습니다.")
        except Exception as e:
            logger.error(f"기존 URL 로드 중 오류 발생: {e}")
    return existing_urls

def collect_job_urls():
    """
    조건에 맞는 채용 공고 URL 리스트를 수집합니다.
    SEARCH_CONDITIONS['duty'] 리스트를 순회하며 모든 URL을 모읍니다.
    """
    all_collected_data = []
    duties = SEARCH_CONDITIONS.get('duty', [])
    
    # 기존 수집된 URL 로드 (중복 수집 방지)
    existing_urls = get_existing_urls()

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

            duty_cnt = 0
            for p in range(1,100):
                payload["page"] = p
                response = session.post(REQUEST_URL, data=payload, headers=DEFAULT_HEADERS)
                
                if response.status_code != 200:
                    logger.error(f"직무 [{duty_code}] 요청 실패. 상태 코드: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                # job_elements = soup.select('td.tplTit div.titBx strong a.link')
                job_elements = soup.select('td.tplTit div.titBx')

                if not len(job_elements):
                    break
                
                batch_cnt = 0
                for element in job_elements:
                    title = element.select_one('strong a.link').get_text(strip=True)
                    relative_url = element.select_one('strong a.link').get('href')
                    full_url = urljoin(BASE_URL, relative_url)
                    dsc_tags = element.select_one('p.dsc')
                    categorys = dsc_tags.get_text(strip=True) if dsc_tags else ""
                    
                    # 중복 수집 방지 (현재 세션 및 기존 파일 내역 확인)
                    if full_url not in existing_urls and not any(item['url'] == full_url for item in all_collected_data):
                        all_collected_data.append({
                            "title": title,
                            "url": full_url,
                            "categorys": categorys,
                        })
                        batch_cnt += 1
                
                duty_cnt += batch_cnt
                # 한 페이지 내의 모든 데이터가 이미 존재한다면 다음 직무로 넘어가는 것도 고려할 수 있으나, 
                # 정렬 순서에 따라 중간에 새 공고가 낄 수 있으므로 일단 페이지 끝까지 확인
                
            logger.info(f"직무 [{duty_code}]: {duty_cnt}개 신규 URL 수집됨")
            logger.info(f"현재 총 신규 수집 개수: {len(all_collected_data)}")
            
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
        print(f"[{i}] {item['title']}: {item['url']} {item['categorys']}")
    print(f"총 {len(urls)}개 수집됨.")
