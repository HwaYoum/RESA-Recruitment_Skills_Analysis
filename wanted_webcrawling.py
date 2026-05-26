import time
import random
import pandas as pd
import requests

# ==========================================
# 1. 글로벌 설정 및 API 엔드포인트 정의
# ==========================================
LIST_URL = "https://www.wanted.co.kr/api/chaos/navigation/v1/results"
DETAIL_URL_TEMPLATE = "https://www.wanted.co.kr/api/chaos/jobs/v1/{job_id}/details"
OUTPUT_FILE = "wanted_raw_id_dataset_refined.csv" # 저장용 파일명

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.wanted.co.kr",
    "Referer": "https://www.wanted.co.kr/"
}

def get_bulk_job_ids(job_group_id=518, max_pages=30):
    """지정된 페이지 수만큼 목록 API를 순회하여 공고 ID 풀을 확보합니다."""
    print(f"📢 [Phase 1] 공고 목록 조회 시작 (목표: {max_pages} 페이지)...")
    job_ids_pool = []
    limit = 20
    
    for page in range(max_pages):
        offset = page * limit
        params = {
            "job_group_id": job_group_id,
            "country": "kr",
            "job_sort": "job.latest_order",
            "years": "0",
            "locations": "all",
            "limit": limit,
            "offset": offset
        }
        try:
            response = requests.get(LIST_URL, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if not data: break
                for item in data:
                    job_ids_pool.append({
                        "job_id": item.get("id"),
                        "company": item.get("company", {}).get("name"),
                        "position": item.get("position")
                    })
            else: break
        except Exception as e:
            print(f"   💥 예외 발생: {e}")
            break
        time.sleep(random.uniform(0.5, 1.0))
    return job_ids_pool

# ==========================================
# 2. 2단계: 상세 API 호출 및 항목별 분리 정제 추출
# ==========================================
def fetch_bulk_job_details_separated(job_list):
    """
    공고 상세 API에서 자격요건과 우대사항을 믹스하지 않고
    각각 개별적인 데이터 필드로 완전 분리하여 수집 데이터프레임 구조를 형성합니다.
    """
    print(f"\n📢 [Phase 2] 총 {len(job_list)}개 공고 대상 항목별(자격요건 vs 우대사항) 분리 적재 시작...")
    
    refined_dataset = []
    total_requests = len(job_list)
    
    for idx, base_job in enumerate(job_list, 1):
        job_id = base_job["job_id"]
        company = base_job["company"]
        position = base_job["position"]
        
        detail_url = DETAIL_URL_TEMPLATE.format(job_id=job_id)
        
        try:
            response = requests.get(detail_url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                detail_data = response.json().get("job", {})
                job_detail = detail_data.get("detail", {})
                
                # 🎯 [구분 적재 구조 변경] 단일 텍스트로 합치지 않고 각각 원천 데이터 유지
                requirements = job_detail.get("requirements", "").strip()      # 자격 요건
                preferred = job_detail.get("preferred_points", "").strip()     # 우대 사항
                
                refined_dataset.append({
                    "job_id": job_id,
                    "company": company,
                    "position": position,
                    "requirements": requirements, # 컬럼 분리 1
                    "preferred": preferred        # 컬럼 분리 2
                })
                print(f"   🚀 [{idx}/{total_requests}] 분리 성공: {company} - {position}")
                
            elif response.status_code == 429:
                print(f"   🛑 [{idx}/{total_requests}] 차단 감지 (HTTP 429)")
                
        except Exception as e:
            print(f"   💥 [{idx}/{total_requests}] 예외 발생: {e}")
            
        time.sleep(random.uniform(1.5, 2.5))
        
        # 50개 단위 중간 백업 시에도 분리된 구조 유지
        if idx % 50 == 0 and refined_dataset:
            pd.DataFrame(refined_dataset).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            
    return refined_dataset

if __name__ == "__main__":
    TARGET_PAGES = 30 
    bulk_job_pool = get_bulk_job_ids(job_group_id=518, max_pages=TARGET_PAGES)
    
    if bulk_job_pool:
        final_dataset = fetch_bulk_job_details_separated(bulk_job_pool)
        if final_dataset:
            df = pd.DataFrame(final_dataset)
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            print(f"\n🎉 [수정 완료] 자격요건과 우대사항이 완벽히 분리된 파일이 생성되었습니다: '{OUTPUT_FILE}'")