import pandas as pd
import networkx as nx
import pickle

# 1. [핵심 추가] 3번(No. 7)에서 저장했던 그래프 객체 G 로드하기
with open('result/networkx_graph.pkl', 'rb') as f:
    G = pickle.load(f)

print("--- [No.8] 그래프 객체 로드 완료 ---")
print(f"불러온 그래프 노드 수: {G.number_of_nodes()}, 엣지 수: {G.number_of_edges()}\n")

# 2. PageRank 연산 (엣지 가중치 반영)
pagerank_dict = nx.pagerank(G, weight='weight')

# 3. 매개 중심성(Betweenness Centrality) 연산
# NetworkX에서 중심성 계산 시 가중치는 '거리'로 해석되므로, 
# 빈도가 높을수록 거리가 가깝다(1/weight)는 개념을 적용해 'distance' 속성을 정의합니다.
for u, v, d in G.edges(data=True):
    G[u][v]['distance'] = 1.0 / d['weight'] if d['weight'] > 0 else float('inf')

betweenness_dict = nx.betweenness_centrality(G, weight='distance')

# 4. 결과를 데이터프레임으로 통합 및 정리
df_centrality = pd.DataFrame({
    'Keyword': pagerank_dict.keys(),
    'PageRank(시장지배력)': pagerank_dict.values(),
    'Betweenness_Centrality(브릿지지수)': [betweenness_dict[k] for k in pagerank_dict.keys()]
})

# 5. 시장 지배력(PageRank) 기준으로 내림차순 정렬 후 저장
df_centrality = df_centrality.sort_values(by='PageRank(시장지배력)', ascending=False)
df_centrality.to_csv('result/centrality_metrics_result.csv', index=False)

print("--- [No.8] 중심성 지표 연산 및 결과셋 저장 완료 (Top 5 기술 스택) ---")
print(df_centrality.head(5))