# data_crawling/jobkorea_data_collecting.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html2text
from PIL import Image
import pytesseract
import io
import os
from data_crawling.constants import DEFAULT_HEADERS, BASE_URL, TARGET_EXTRACTION_FIELDS
from data_crawling.logger import setup_logger

logger = setup_logger("data_collecting")

def get_iframe_url(job_url, session):
    """채용공고 상세 페이지에서 실제 데이터가 담긴 iframe URL을 추출합니다."""
    try:
        response = session.get(job_url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 일반적인 iframe 태그 시도
        iframe_tag = soup.select_one('iframe[src*="/Recruit/GI_Read_Comt_Ifrm"]')
        if iframe_tag:
            return urljoin(BASE_URL, iframe_tag['src'])
            
        # 2. 스크립트 내에 숨겨진 URL 시도 (패턴 매칭)
        import re
        pattern = r'/Recruit/GI_Read_Comt_Ifrm[^"\\\s]+'
        matches = re.findall(pattern, response.text)
        
        if matches:
            # Gno가 포함된 URL을 우선적으로 선택, 없으면 가장 긴 URL 선택
            best_match = None
            for m in matches:
                if 'Gno=' in m:
                    best_match = m
                    break
            if not best_match:
                best_match = max(matches, key=len)
                
            url = best_match.replace('\\u0026', '&')
            iframe_url = urljoin(BASE_URL, url)
            logger.info(f"패턴 매칭으로 iframe URL 발견: {iframe_url}")
            return iframe_url
            
        return None
    except Exception as e:
        logger.error(f"iframe URL 추출 중 오류 발생: {e}")
        return None

def extract_text_from_image(img_url, session):
    """이미지 URL에서 이미지를 다운로드 후 OCR을 통해 텍스트를 추출합니다."""
    try:
        logger.info(f"📷 이미지 공고 감지. OCR 추출 시작: {img_url}")
        response = session.get(img_url, headers=DEFAULT_HEADERS)
        
        img = Image.open(io.BytesIO(response.content))
        # 한국어(kor)와 영어(eng)를 함께 인식하도록 설정
        # 주의: Tesseract OCR 엔진이 시스템에 설치되어 있어야 함
        text = pytesseract.image_to_string(img, lang='kor+eng')
        return text
    except Exception as e:
        logger.error(f"OCR 처리 중 오류 발생: {e}")
        return "이미지 분석 실패"

def extract_text_from_html(html_content):
    """HTML 구조를 html2text를 이용해 텍스트로 변환합니다."""
    logger.info("📄 텍스트 기반 공고 감지. HTML 정규화 시작.")
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.body_width = 0 
    
    return h.handle(html_content)

def parse_job_content(iframe_url, session):
    """iframe에 접속하여 이미지인지 텍스트인지 판단 후 내용을 추출합니다."""
    try:
        response = session.get(iframe_url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 잡코리아 채용 본문 영역 확인
        content_area = soup.select_one('div.secDetailWrap') or soup.select_one('div.detailReadImg')
        
        if not content_area:
            return "본문 영역을 찾을 수 없습니다."

        # 1. 이미지 공고인지 확인 (본문 영역 내 큰 이미지가 있는지)
        img_tag = content_area.select_one('img')
        
        # 이미지 태그가 존재하고, 텍스트 길이가 매우 짧은 경우 통이미지로 간주
        if img_tag and len(content_area.get_text(strip=True)) < 100:
            img_url = img_tag['src']
            if img_url.startswith('//'):
                img_url = "https:" + img_url
            elif not img_url.startswith('http'):
                img_url = urljoin(BASE_URL, img_url)
            return extract_text_from_image(img_url, session)
        
        # 2. 텍스트 공고인 경우 HTML -> Text 변환
        else:
            return extract_text_from_html(str(content_area))
    except Exception as e:
        logger.error(f"본문 파싱 중 오류 발생: {e}")
        return "본문 파싱 실패"

def scrape_job_detail(url, session=None):
    """
    개별 채용 공고 페이지에서 데이터를 수집합니다.
    iframe 접근 -> 이미지/텍스트 판별 -> 내용 추출 -> LLM 분석 순으로 진행합니다.
    """
    try:
        logger.info(f"공고 상세 페이지 접속 중: {url}")
        
        if session is None:
            session = requests.Session()
            
        # 1. 회사명 등 기본 정보 추출 (메인 상세 페이지)
        response = session.get(url, headers=DEFAULT_HEADERS)
        if response.status_code != 200:
            logger.error(f"페이지 접속 실패: {url} (상태 코드: {response.status_code})")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # 잡코리아 회사명 선택자 (페이지 구조에 따라 다를 수 있음)
        # company_name = soup.select_one('div.info-company a.name') or soup.select_one('span.company-name')
        company_name = soup.select_one('div[data-sentry-component="CompanyName"]')
        # 2. 실제 본문 내용이 있는 iframe URL 획득
        iframe_url = get_iframe_url(url, session)
        
        if iframe_url:
            # 3. iframe 내부에서 본문 텍스트 추출 (OCR 또는 HTML2Text)
            raw_content = parse_job_content(iframe_url, session)
        else:
            logger.warning("iframe을 찾을 수 없습니다. 메인 페이지 본문 시도.")
            content_area = soup.select_one('div.job-detail-content')
            raw_content = content_area.get_text() if content_area else "본문 없음"
        
        # 4. LLM 분석 (추출된 텍스트 기반)
        analysis_result = analyze_with_llm(raw_content)
        
        data = {
            "company": company_name.get_text(strip=True) if company_name else "정보 없음",
            "raw_content_length": len(raw_content),
            "analysis": analysis_result
        }
        
        logger.info(f"데이터 수집 완료: {data['company']}")
        return data

    except Exception as e:
        logger.exception(f"데이터 수집 중 오류 발생 ({url}): {e}")
        return None

def analyze_with_llm(text):
    """
    LLM을 사용하여 텍스트를 분석합니다. 
    현재는 검토 단계이므로 비용 절감을 위해 더미 데이터를 반환합니다.
    """
    logger.debug("LLM 분석 수행 중 (더미 모드)")
    # TARGET_EXTRACTION_FIELDS 기반의 더미 응답 생성
    dummy_response = {field: "분석된 내용 예시입니다." for field in TARGET_EXTRACTION_FIELDS}
    dummy_response["summary"] = f"글자수 {len(text)}의 공고 분석 결과입니다."
    return dummy_response

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    test_url = "https://www.jobkorea.co.kr/Recruit/GI_Read/49074852"
    print(f"--- 상세 데이터 수집 단위 테스트 시작 ({test_url}) ---")
    
    session = requests.Session()
    result = scrape_job_detail(test_url, session=session)
    
    print("\n=== 최종 수집 결과 ===")
    if result:
        import json
        print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print("수집 실패")
