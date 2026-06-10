import pickle
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 1. 한글 폰트 설정 (시각화 시 한글 깨짐 방지)
# Windows 사용자는 'Malgun Gothic', Mac 사용자는 'AppleGothic' 설정
try:
    plt.rc('font', family='Malgun Gothic') # Windows
except:
    plt.rc('font', family='AppleGothic')   # Mac
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

# 2. 저장했던 그래프 객체 G 로드
with open('../02_analysis/result/networkx_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# 3. 시각화 레이아웃 정의 (spring_layout은 노드들을 스프링처럼 밀고 당겨 균형 있게 배치함)
pos = nx.spring_layout(G, k=3.0, iterations=50, seed=42)

# 4. 시각화 요소 정밀 튜닝 데이터 가공
# (1) 노드 크기: 해당 기술 스택의 총 등장 빈도(total_freq)에 비례하게 설정
node_sizes = [nx.get_node_attributes(G, 'total_freq')[node] * 3 for node in G.nodes()]

# (2) 엣지 굵기: 기술 스택 간 동시 출현 가중치(weight)에 비례하게 설정 (너무 두꺼워지지 않게 0.2를 곱함)
edge_widths = [d['weight'] * 0.2 for u, v, d in G.edges(data=True)]

# 5. 본격적인 그래프 그리기
plt.figure(figsize=(15, 12))
plt.title("IT 직무 기술 스택 동시 출현 네트워크 그래프", fontsize=20, fontweight='bold', pad=20)

# (1) 엣지(연결선) 그리기
nx.draw_networkx_edges(
    G, pos, 
    width=edge_widths, 
    edge_color='gainsboro', # 연한 회색으로 처리하여 복잡도 감소
    alpha=0.7
)

# (2) 노드(점) 그리기
nx.draw_networkx_nodes(
    G, pos, 
    node_size=node_sizes, 
    node_color='skyblue',   # 부드러운 스카이블루 톤
    edgecolors='dodgerblue',
    alpha=0.9
)

# (3) 라벨(기술 스택 텍스트) 그리기
nx.draw_networkx_labels(
    G, pos, 
    font_size=11, 
    font_family=plt.rcParams['font.family'][0],
    font_weight='bold'
)

# 6. 여백 조정 및 고해상도 이미지 파일로 저장
plt.axis('off')
plt.tight_layout()
plt.savefig('result/tech_network_graph.png', dpi=300)
plt.show()

print("--- 네트워크 그래프 시각화 이미지(tech_network_graph.png) 생성 완료 ---")