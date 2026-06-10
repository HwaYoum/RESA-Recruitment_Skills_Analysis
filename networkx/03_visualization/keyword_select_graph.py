import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import itertools
import platform

# 1. 운영체제 확인 후 폰트 설정
system_name = platform.system()
if system_name == "Windows":
    plt.rc('font', family='Malgun Gothic')
elif system_name == "Darwin":
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드 및 그래프 생성
print("데이터 로딩 및 그래프 구축 중...")
df = pd.read_csv('../00_input_data/jobdata_after_preprocessing.csv')
df['requirements_preferred'] = df['requirements_preferred'].fillna('')

G = nx.Graph()

for row in df['requirements_preferred']:
    skills = [s.strip() for s in str(row).split(',') if s.strip()]
    if len(skills) > 1:
        for u, v in itertools.combinations(skills, 2):
            u, v = sorted([u, v])
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)

print(f"그래프 구축 완료 (전체 노드: {G.number_of_nodes()}, 전체 엣지: {G.number_of_edges()})")

# 3. 사용자 입력 받기
print("\n=== 그래프 분석 옵션 입력 ===")
user_input = input("분석할 키워드 입력 (쉼표로 구분): ")
target_keywords = [k.strip() for k in user_input.split(',')]

try:
    threshold = int(input("최소 동시 출현 횟수(임계값)를 입력하세요 (예: 3): "))
except ValueError:
    threshold = 1
    print("숫자 입력이 잘못되어 기본값 1로 설정합니다.")

# 4. 부분 그래프 추출
nodes_to_keep = set()
for kw in target_keywords:
    if kw in G:
        nodes_to_keep.add(kw)
        nodes_to_keep.update(G.neighbors(kw))

# 서브 그래프 생성
sub_G = G.subgraph(nodes_to_keep).copy()

# 엣지 가중치 필터링 (임계값 미만인 엣지 삭제)
edges_to_remove = [(u, v) for u, v, d in sub_G.edges(data=True) if d['weight'] < threshold]
sub_G.remove_edges_from(edges_to_remove)

# [수정된 부분] 엣지 유효성 검사 로직
if sub_G.number_of_edges() == 0:
    print(f"\n오류: '{', '.join(target_keywords)}' 키워드와 '{threshold}'회 이상 연관된 기술 관계를 찾을 수 없습니다.")
    print("   임계값을 낮추거나 키워드를 다시 확인해주세요.")
else:
    # 5. 시각화
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(sub_G, k=1.5, seed=42)
    
    node_colors = ['salmon' if node in target_keywords else 'skyblue' for node in sub_G.nodes()]
    
    nx.draw_networkx_nodes(sub_G, pos, node_size=1500, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(sub_G, pos, width=1.0, alpha=0.3, edge_color='gray')
    nx.draw_networkx_labels(sub_G, pos, font_family='Malgun Gothic', font_weight='bold', font_size=10)
    
    plt.title(f"입력 키워드 중심 네트워크: {', '.join(target_keywords)} (임계값: {threshold}회 이상)", fontsize=15, fontweight='bold')
    plt.axis('off')
    plt.show()
    print(f"\n'{threshold}'회 이상 연관된 기술들로 구성된 네트워크 그래프가 생성되었습니다.")