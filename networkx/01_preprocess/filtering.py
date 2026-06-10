import pandas as pd

# 1. No. 5에서 생성한 동시 출현 행렬 로드
co_matrix = pd.read_csv('result/co_occurrence_matrix.csv', index_col=0)

# 2. 임계값(Threshold) 설정 
# 두 기술 스택이 최소 30회 이상 동시에 출현한 경우만 유의미한 연결 관계로 인정
threshold = 30

filtered_matrix = co_matrix.copy()

# 3. 대각 성분(자기 자신의 빈도)은 유지하고, 엣지 가중치(동시 출현 빈도)에만 필터링 적용
for col in filtered_matrix.columns:
    for idx in filtered_matrix.index:
        if idx != col:  # 자기 자신이 아닌 엣지 관계일 때
            if filtered_matrix.loc[idx, col] < threshold:
                filtered_matrix.loc[idx, col] = 0

# 4. 결과 저장
filtered_matrix.to_csv('result/filtered_co_occurrence_matrix.csv')
print(f"--- [No.6] 임계값(>{threshold}) 필터링 완료 및 노이즈 제거 완료 ---")