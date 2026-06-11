import pandas as pd
import networkx as nx
import pickle

# 1. 필터링된 동시 출현 행렬 로드
filtered_matrix = pd.read_csv('../01_preprocess/result/filtered_co_occurrence_matrix.csv', index_col=0)

# 2. NetworkX 무방향 그래프(Graph) 객체 생성
G = nx.Graph()

# 3. 행렬 데이터를 순회하며 노드 및 가중치 기반 엣지 추가
for i, keyword_i in enumerate(filtered_matrix.index):
    # 노드 추가 및 해당 키워드의 자체 등장 빈도를 노드 속성으로 저장
    G.add_node(keyword_i, total_freq=int(filtered_matrix.loc[keyword_i, keyword_i]))
    
    for j, keyword_j in enumerate(filtered_matrix.columns):
        if i < j:  # 대칭 행렬이므로 중복 연산을 방지하기 위해 상삼각 영역만 순회
            weight = int(filtered_matrix.loc[keyword_i, keyword_j])
            if weight > 0:  # 임계값을 넘은 유효한 연결선만 추가
                G.add_edge(keyword_i, keyword_j, weight=weight)

# 4. [핵심 추가] 생성된 그래프 객체 G를 파일로 저장 (.pkl)
with open('result/networkx_graph.pkl', 'wb') as f:
    pickle.dump(G, f)

print("--- [No.7] NetworkX 그래프 객체 빌드 및 저장 완료 ---")
print(f"총 노드(기술 스택) 수: {G.number_of_nodes()}")
print(f"총 엣지(연결 관계) 수: {G.number_of_edges()}")
print("저장된 파일명: networkx_graph.pkl")