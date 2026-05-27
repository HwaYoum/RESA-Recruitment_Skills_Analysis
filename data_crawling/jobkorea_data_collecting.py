# data_crawling/jobkorea_data_collecting.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html2text
import io
import os
import base64
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from data_crawling.constants import DEFAULT_HEADERS, BASE_URL, TARGET_EXTRACTION_FIELDS
from data_crawling.logger import setup_logger

# 환경 변수 로드
load_dotenv()

logger = setup_logger("data_collecting")

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-nano")

def get_iframe_url(job_url, session):
    """채용공고 상세 페이지에서 실제 데이터가 담긴 iframe URL을 추출합니다."""
    try:
        # 0. URL에서 Gno 추출 (백업 및 확인용)
        gno_match = re.search(r'/GI_Read/(\d+)', job_url, re.IGNORECASE)
        gno = gno_match.group(1) if gno_match else None

        response = session.get(job_url, headers=DEFAULT_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 일반적인 iframe 태그 시도
        iframe_tag = soup.select_one('iframe[src*="/Recruit/GI_Read_Comt_Ifrm"]')
        if iframe_tag:
            return urljoin(BASE_URL, iframe_tag['src'])
            
        # 2. 스크립트 내에 숨겨진 URL 시도 (패턴 매칭)
        # [^"\'\s]+ 로 변경하여 백slash(\)를 허용함으로써 \u0026 (ampersand)가 포함된 전체 URL을 캡처
        pattern = r'/Recruit/GI_Read_Comt_Ifrm[^"\'\s]+'
        matches = re.findall(pattern, response.text)
        
        if matches:
            # Gno가 포함된 URL을 우선적으로 선택
            best_match = None
            for m in matches:
                # 대소문자 구분 없이 gno= 혹은 해당 공고의 특정 Gno가 포함되어 있는지 확인
                if 'gno=' in m.lower() or (gno and gno in m):
                    best_match = m
                    break
            
            if not best_match:
                # Gno가 포함된 것이 없다면 가장 긴 URL 선택
                best_match = max(matches, key=len)
                
            # \u0026 -> & 변환 및 불필요한 이스케이프 문자 제거
            url = best_match.replace('\\u0026', '&').replace('\\u002b', '+').rstrip('\\')
            iframe_url = urljoin(BASE_URL, url)
            logger.info(f"패턴 매칭으로 iframe URL 발견: {iframe_url}")
            return iframe_url
            
        # 3. 모든 시도가 실패했지만 Gno를 알고 있다면 직접 생성
        if gno:
            iframe_url = urljoin(BASE_URL, f"/Recruit/GI_Read_Comt_Ifrm?Gno={gno}")
            logger.info(f"Gno를 이용하여 iframe URL 직접 생성: {iframe_url}")
            return iframe_url

        return None
    except Exception as e:
        logger.error(f"iframe URL 추출 중 오류 발생: {e}")
        return None

def analyze_image_with_llm(img_url, session):
    """이미지 URL에서 이미지를 다운로드 후 멀티모달 LLM을 통해 정보를 직접 추출합니다."""
    try:
        logger.info(f"📷 이미지 공고 감지. 멀티모달 LLM 분석 시작: {img_url}")
        response = session.get(img_url, headers=DEFAULT_HEADERS)
        image_content = response.content
        base64_image = base64.b64encode(image_content).decode('utf-8')

        prompt = f"""
        당신은 채용 공고 분석 전문가입니다. 주어진 채용 공고 이미지에서 다음 항목들을 추출하여 JSON 형식으로 응답해주세요.
        
        JSON의 키는 반드시 다음 항목 명칭과 정확히 일치해야 합니다:
        {', '.join(TARGET_EXTRACTION_FIELDS)}
        
        응답은 반드시 순수 JSON 형태여야 하며, 추가적인 설명은 생략하세요.
        """

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"이미지 LLM 분석 중 오류 발생: {e}")
        return {field: "분석 실패" for field in TARGET_EXTRACTION_FIELDS}

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
            return "error", "본문 영역을 찾을 수 없습니다."

        # 1. 이미지 공고인지 확인 (본문 영역 내 큰 이미지가 있는지)
        img_tag = content_area.select_one('img')
        logger.info(f"content_area text 길이: {len(content_area.get_text(strip=True))}")
        # 이미지 태그가 존재하고, 텍스트 길이가 매우 짧은 경우 통이미지로 간주
        if img_tag and len(content_area.get_text(strip=True)) < 100:
            img_url = img_tag['src']
            if img_url.startswith('//'):
                img_url = "https:" + img_url
            elif not img_url.startswith('http'):
                img_url = urljoin(BASE_URL, img_url)
            return "image_analysis", analyze_image_with_llm(img_url, session)
        
        # 2. 텍스트 공고인 경우 HTML -> Text 변환
        else:
            return "text", extract_text_from_html(str(content_area))
    except Exception as e:
        logger.error(f"본문 파싱 중 오류 발생: {e}")
        return "error", "본문 파싱 실패"

def scrape_job_detail(url, session=None):
    """
    개별 채용 공고 페이지에서 데이터를 수집합니다.
    iframe 접근 -> 이미지/텍스트 판별 -> 내용 추출 (또는 LLM 직접 분석) 순으로 진행합니다.
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
        company_name = soup.select_one('div[data-sentry-component="CompanyName"]')
        
        # 2. 실제 본문 내용이 있는 iframe URL 획득
        iframe_url = get_iframe_url(url, session)
        
        analysis_result = None
        content_type = "unknown"
        raw_content_length = 0

        if iframe_url:
            # 3. iframe 내부에서 본문 처리 (이미지 직접 분석 또는 텍스트 추출)
            content_type, content_data = parse_job_content(iframe_url, session)
            
            if content_type == "image_analysis":
                analysis_result = content_data
            elif content_type == "text":
                raw_content_length = len(content_data)
                analysis_result = analyze_with_llm(content_data)
            else:
                logger.warning(f"콘텐츠 처리 실패: {content_data}")
                analysis_result = {field: "데이터 없음" for field in TARGET_EXTRACTION_FIELDS}
        else:
            logger.warning("iframe을 찾을 수 없습니다. 메인 페이지 본문 시도.")
            content_area = soup.select_one('div.job-detail-content')
            raw_content = content_area.get_text() if content_area else "본문 없음"
            raw_content_length = len(raw_content)
            analysis_result = analyze_with_llm(raw_content)
        
        data = {
            "company": company_name.get_text(strip=True) if company_name else "정보 없음",
            "content_type": content_type,
            "raw_content_length": raw_content_length,
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
    """
    try:
        logger.info("🤖 텍스트 기반 LLM 분석 시작.")
        
        prompt = f"""
        당신은 채용 공고 분석 전문가입니다. 다음 채용 공고 텍스트에서 주요 정보를 추출하여 JSON 형식으로 응답해주세요.
        
        JSON의 키는 반드시 다음 항목 명칭과 정확히 일치해야 합니다:
        {', '.join(TARGET_EXTRACTION_FIELDS)}
        
        [채용 공고 텍스트]
        {text}
        
        응답은 반드시 순수 JSON 형태여야 하며, 추가적인 설명은 생략하세요.
        """

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "당신은 채용 공고 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"텍스트 LLM 분석 중 오류 발생: {e}")
        return {field: "분석 실패" for field in TARGET_EXTRACTION_FIELDS}

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    test_url = "https://www.jobkorea.co.kr/Recruit/GI_Read/49231627?rPageCode=SL&logpath=21&sn=6&sc=612"
    print(f"--- 상세 데이터 수집 단위 테스트 시작 ({test_url}) ---")
    
    session = requests.Session()
    result = scrape_job_detail(test_url, session=session)
    
    print("\n=== 최종 수집 결과 ===")
    if result:
        import json
        print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print("수집 실패")
