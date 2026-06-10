import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

# 1. 데이터 로드
df_jobs = pd.read_csv('../00_input_data/jobdata_after_preprocessing.csv')

# 2. 확실하게 데이터가 많은 상위 단일 직무 5개 강제 지정
# (division_frequencies.csv 기준 가장 많은 5개 직무)
top_divisions = ['시스템 엔지니어', '소프트웨어 개발자', '보안 엔지니어', '네트워크 엔지니어', '백엔드 개발자']

# 3. 확실하게 데이터가 가득 찬 상위 키워드 5개 지정
# (keyword_frequencies.csv 기준 일반 단어를 제외한 IT 키워드)
target_skills = ['Python', 'Linux', '네트워크', 'C++', '서버']

# 4. 교차표(Contingency Table) 구성을 위한 빈도 집계
contingency_data = []

for div in top_divisions:
    # filtered_division 컬럼에 해당 직무명이 '포함'되어 있는지 검사 (복합 문자열 해결)
    df_div = df_jobs[df_jobs['filtered_division'].str.contains(div, na=False, regex=False)]
    
    div_counts = []
    for skill in target_skills:
        # 대소문자 구분 없이(case=False), 해당 기술 스택 단어가 포함되었는지 카운트
        count = df_div['requirements_preferred'].str.contains(skill, case=False, na=False, regex=False).sum()
        div_counts.append(int(count))
        
    contingency_data.append(div_counts)

# 데이터프레임 형태로 교차표 정의
df_contingency = pd.DataFrame(contingency_data, index=top_divisions, columns=target_skills)

print("--- [확인용] 생성된 교차표 내부 데이터 ---")
print(df_contingency)
print("---------------------------------------\n")

# 5. 카이제곱 독립성 검정 수행
# 모든 칸이 0이 되는 극단적인 상황을 방지하기 위해 데이터 유효성 검사 후 실행
if df_contingency.sum().sum() == 0:
    print("에러: 직무나 기술 스택 매칭에 실패하여 표의 데이터가 전부 0입니다.")
    print("requirements_preferred 컬럼의 실제 텍스트 형태를 다시 확인해야 합니다.")
else:
    chi2, p_value, dof, expected = chi2_contingency(df_contingency)

    # 6. 통계적 가설 검정 보고서 파일(.txt) 작성 및 서식 정렬
    report_filename = 'result/chi2_test_report.txt'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("=========================================================\n")
        f.write("          [No.9] 통계적 가설 검정 보고서 (오류 해결본)    \n")
        f.write("=========================================================\n\n")
        f.write(f"1. 분석 대상 직무 그룹 (Top 5): {', '.join(top_divisions)}\n")
        f.write(f"2. 분석 대상 기술 스택: {', '.join(target_skills)}\n\n")
        f.write("3. 직무별 기술 요구 조건 교차표 (Observed Frequencies):\n")
        f.write("---------------------------------------------------------\n")
        
        f.write(f"{'직무 분류':<20}\t" + "\t".join([f"{skill:<8}" for skill in target_skills]) + "\n")
        f.write("---------------------------------------------------------\n")
        for div in top_divisions:
            row_str = f"{div:<20}\t" + "\t".join([f"{df_contingency.loc[div, skill]:<8}" for skill in target_skills])
            f.write(row_str + "\n")
            
        f.write("---------------------------------------------------------\n\n")
        f.write("4. 카이제곱 가설 검정 결과:\n")
        f.write(f"  - 카이제곱 통계량 (Chi-squared): {chi2:.4f}\n")
        f.write(f"  - 유의확률 (P-value): {p_value:.4e}\n")
        f.write(f"  - 자유도 (Degrees of Freedom): {dof}\n\n")
        
        f.write("5. 최종 결론:\n")
        # P-value가 0.05보다 작으면 유의미함, 크면 의미 없음
        if p_value < 0.05:
            f.write("  -> P-value가 유의수준 0.05보다 훨씬 작으므로 귀무가설을 기각합니다.\n")
            f.write("  -> 결론적으로 직무 그룹과 기술 요구 조건 간에는 통계적으로 매우 유의미한 연관성이 존재합니다.\n")
        else:
            f.write("  -> P-value가 유의수준 0.05보다 크므로 귀무가설을 채택합니다.\n")
            f.write("  -> 결론적으로 직무 그룹과 기술 요구 조건 간에는 통계적으로 유의미한 연관성이 있다고 보기 어렵습니다.\n")

    print("--- [No.9] 검정 및 보고서 파일 저장 완료 ---")
    print(f"산출된 유의확률(P-value): {p_value:.4e}")
    if p_value < 0.05:
        print("성공: 직무와 기술 스택 간의 유의미한 연관성이 증명되었습니다!")
    else:
        print("주의: 여전히 결과가 유의미하지 않습니다. 데이터 매칭 단어를 조율해야 합니다.")