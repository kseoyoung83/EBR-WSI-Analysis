# myscripts/build_graph.py

import json
import numpy as np
import networkx as nx
import pickle
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
import sys

# 조직 타입별 색상
CLASS_COLORS = {
    0: (0.9, 0.9, 0.9),      # BACK - 회색
    1: (0.5, 0.9, 0.5),      # NORM - 초록
    2: (0.8, 0.7, 0.4),      # DEB - 황토색
    3: (0.8, 0.1, 0.1),      # TUM - 빨강
    4: (1.0, 0.8, 0.4),      # ADI - 노란색
    5: (0.6, 0.4, 0.8),      # MUC - 보라
    6: (0.9, 0.5, 0.5),      # MUS - 분홍
    7: (0.2, 0.5, 0.8),      # STR - 파랑
    8: (0.4, 0.7, 0.4),      # LYM - 연두
}

CLASS_NAMES = {
    0: "BACK", 1: "NORM", 2: "DEB", 3: "TUM",
    4: "ADI", 5: "MUC", 6: "MUS", 7: "STR", 8: "LYM"
}


def load_predictions(json_file):
    """Week 6 predictions.json 로드"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"✓ Loaded: {len(data['predictions'])} patches")
    return data


def compute_patch_centers(coordinates):
    """패치 좌상단 좌표 → 중심 좌표"""
    coords = np.array(coordinates)
    centers = coords[:, :2] + coords[:, 2:] / 2
    
    print(f"✓ Computed centers: shape {centers.shape}")
    return centers


def build_knn_graph(centers, features, predictions, k=8):
    """k-NN Graph 구축"""
    n_patches = len(centers)
    
    print(f"Finding {k} nearest neighbors...")
    nbrs = NearestNeighbors(n_neighbors=k+1, algorithm='ball_tree')
    nbrs.fit(centers)
    distances, indices = nbrs.kneighbors(centers)
    
    G = nx.Graph()
    
    # 노드 추가
    print("Adding nodes with attributes...")
    for i in range(n_patches):
        G.add_node(i,
                   pos=tuple(centers[i]),
                   feature=features[i].tolist(),
                   prediction=int(predictions[i]),
                   color=CLASS_COLORS[predictions[i]],
                   label=CLASS_NAMES[predictions[i]])
    
    # 엣지 추가
    print("Adding edges...")
    for i in range(n_patches):
        for j in range(1, k+1):
            neighbor = indices[i, j]
            distance = distances[i, j]
            
            if not G.has_edge(i, neighbor):
                G.add_edge(i, neighbor, weight=float(distance))
    
    print(f"✓ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return G


def save_graph(G, output_file):
    """Graph 저장"""
    with open(output_file, 'wb') as f:
        pickle.dump(G, f)
    print(f"✓ Graph saved: {output_file}")


def print_graph_statistics(G):
    """그래프 통계 출력"""
    print("\n" + "="*50)
    print("Graph Statistics")
    print("="*50)
    
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    
    if nx.is_connected(G):
        print("Graph is connected: Yes")
    else:
        components = list(nx.connected_components(G))
        print(f"Graph is connected: No ({len(components)} components)")
    
    from collections import Counter
    class_counts = Counter([G.nodes[n]['prediction'] for n in G.nodes()])
    print("\nClass distribution:")
    for cls in sorted(class_counts.keys()):
        print(f"  {CLASS_NAMES[cls]:6s} ({cls}): {class_counts[cls]:4d} nodes")
    
    boundary_edges = sum(1 for u, v in G.edges() 
                        if G.nodes[u]['prediction'] != G.nodes[v]['prediction'])
    
    print(f"\nBoundary edges: {boundary_edges} ({boundary_edges/G.number_of_edges()*100:.1f}%)")
    print("="*50 + "\n")


def main():
    if len(sys.argv) > 1:
        wsi_name = sys.argv[1]
    else:
        wsi_name = "CMU-1-Small-Region"
    
    print(f"\n{'='*60}")
    print(f"Building Graph: {wsi_name}")
    print(f"{'='*60}\n")
    
    # 경로 설정 (Week 6 결과 읽기)
    week6_dir = Path("/data/week6_results") / wsi_name
    predictions_file = week6_dir / "predictions" / "predictions.json"
    
    # Week 7 결과 저장
    output_dir = Path("/results") / wsi_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON 로드
    data = load_predictions(predictions_file)
    
    # 2. 중심 좌표 계산
    centers = compute_patch_centers(data['coordinates'])
    
    # 3. NumPy array 변환
    features = np.array(data['probabilities'])
    predictions = np.array(data['predictions'])
    
    # 4. k-NN Graph 구축
    G = build_knn_graph(centers, features, predictions, k=8)
    
    # 5. 통계 출력
    print_graph_statistics(G)
    
    # 6. 저장
    graph_file = output_dir / "graph.pkl"
    save_graph(G, graph_file)
    
    # 7. 통계 텍스트 저장
    stats_file = output_dir / "graph_statistics.txt"
    with open(stats_file, 'w') as f:
        f.write(f"Graph Statistics: {wsi_name}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Nodes: {G.number_of_nodes()}\n")
        f.write(f"Edges: {G.number_of_edges()}\n")
        f.write(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}\n")
        
        from collections import Counter
        class_counts = Counter([G.nodes[n]['prediction'] for n in G.nodes()])
        f.write("\nClass distribution:\n")
        for cls in sorted(class_counts.keys()):
            f.write(f"  {CLASS_NAMES[cls]:6s} ({cls}): {class_counts[cls]:4d} nodes\n")
    
    print(f"✓ Statistics saved: {stats_file}\n")
    print(f"{'='*60}")
    print(f"✓ Completed: {wsi_name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()