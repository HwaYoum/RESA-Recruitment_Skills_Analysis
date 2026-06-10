import pandas as pd
import numpy as np
from itertools import combinations

# 1. 전처리 완료된 채용 데이터 및 키워드 빈도 데이터 로드
df_jobs = pd.read_csv('../00_input_data/jobdata_after_preprocessing.csv')
df_keywords = pd.read_csv('../00_input_data/keyword_frequencies.csv')

# 2. 분석에 활용할 상위 키워드 추출 (빈도수 기준 상위 50개 키워드 선택)
top_keywords = df_keywords['keyword'].head(50).tolist()

# 3. 빈 동시 출현 행렬(Co-occurrence Matrix) 초기화
co_matrix = pd.DataFrame(0, index=top_keywords, columns=top_keywords)

# 4. 각 채용 공고를 순회하며 동시 출현 빈도 계산
for idx, row in df_jobs.iterrows():
    if pd.isna(row['requirements_preferred']):
        continue
        
    # 공고 내 키워드 리스트 추출
    job_keywords = [k.strip() for k in str(row['requirements_preferred']).split(',')]
    
    # 상위 50개 분석 대상 키워드에 포함되는 것만 필터링 및 중복 제거
    valid_keywords = list(set([k for k in job_keywords if k in top_keywords]))
    
    # 2개씩 조합(Combination)을 만들어 행렬에 빈도 가산
    for k1, k2 in combinations(valid_keywords, 2):
        co_matrix.loc[k1, k2] += 1
        co_matrix.loc[k2, k1] += 1  # 대칭 행렬 설정
        
    # 자기 자신(대각 성분)은 해당 공고에 등장한 총 횟수로 누적
    for k in valid_keywords:
        co_matrix.loc[k, k] += 1

# 5. 산출물 저장
co_matrix.to_csv('result/co_occurrence_matrix.csv')
print("--- [No.5] 기술 스택 동시 출현 행렬 생성 완료 (상위 5개 샘플) ---")
print(co_matrix.iloc[:5, :5])