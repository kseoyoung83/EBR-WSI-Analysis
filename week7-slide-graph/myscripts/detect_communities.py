# myscripts/detect_communities.py

import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
from collections import Counter, defaultdict
import sys

CLASS_COLORS = {
    0: (0.9, 0.9, 0.9), 1: (0.5, 0.9, 0.5), 2: (0.8, 0.7, 0.4),
    3: (0.8, 0.1, 0.1), 4: (1.0, 0.8, 0.4), 5: (0.6, 0.4, 0.8),
    6: (0.9, 0.5, 0.5), 7: (0.2, 0.5, 0.8), 8: (0.4, 0.7, 0.4),
}

CLASS_NAMES = {
    0: "BACK", 1: "NORM", 2: "DEB", 3: "TUM",
    4: "ADI", 5: "MUC", 6: "MUS", 7: "STR", 8: "LYM"
}


def load_graph(graph_file):
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    print(f"✓ Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def detect_communities(G):
    """
    Louvain 알고리즘으로 커뮤니티 탐지
    그래프 구조(연결 패턴)만으로 군집 찾기
    """
    from networkx.algorithms import community
    
    print("\nDetecting communities using Louvain algorithm...")
    communities = community.louvain_communities(G, seed=42)
    
    print(f"✓ Found {len(communities)} communities")
    
    # 커뮤니티 ID를 노드에 할당
    community_map = {}
    for comm_id, comm_nodes in enumerate(communities):
        for node in comm_nodes:
            community_map[node] = comm_id
    
    return communities, community_map


def analyze_community_composition(G, communities, community_map):
    """각 커뮤니티의 조직 타입 구성 분석"""
    print("\n" + "="*60)
    print("Community Composition Analysis")
    print("="*60)
    
    for comm_id, comm_nodes in enumerate(communities):
        print(f"\nCommunity {comm_id} ({len(comm_nodes)} nodes):")
        
        # 이 커뮤니티의 조직 타입 분포
        class_counts = Counter([G.nodes[n]['prediction'] for n in comm_nodes])
        
        for cls in sorted(class_counts.keys()):
            count = class_counts[cls]
            percentage = count / len(comm_nodes) * 100
            print(f"  {CLASS_NAMES[cls]:6s} ({cls}): {count:4d} nodes ({percentage:5.1f}%)")
    
    print("="*60 + "\n")
    
    return analyze_purity(G, communities)


def analyze_purity(G, communities):
    """
    커뮤니티 순도(Purity) 분석
    각 커뮤니티가 얼마나 "순수"한가? (한 조직 타입으로만 구성)
    """
    purity_scores = []
    
    for comm_id, comm_nodes in enumerate(communities):
        class_counts = Counter([G.nodes[n]['prediction'] for n in comm_nodes])
        
        # 가장 많은 조직 타입의 비율 = 순도
        dominant_count = max(class_counts.values())
        purity = dominant_count / len(comm_nodes)
        purity_scores.append(purity)
    
    avg_purity = np.mean(purity_scores)
    
    print(f"Average community purity: {avg_purity:.3f}")
    print(f"  (1.0 = perfect, each community has only one tissue type)")
    print(f"  (0.5 = random, communities are mixed)")
    
    return purity_scores


def visualize_communities(G, communities, community_map, output_file):
    """커뮤니티를 색상으로 시각화"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 커뮤니티별 색상 (무지개)
    num_communities = len(communities)
    colors = plt.cm.tab20(np.linspace(0, 1, num_communities))
    
    node_colors = [colors[community_map[node]] for node in G.nodes()]
    
    # 엣지
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5,
                          edge_color='gray', ax=ax)
    
    # 노드
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                          node_size=120, alpha=0.9,
                          edgecolors='black', linewidths=0.5, ax=ax)
    
    ax.invert_yaxis()
    ax.set_title(f'Community Detection\n({len(communities)} communities found by Louvain algorithm)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    
    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=colors[i], edgecolor='black',
              label=f'Community {i} ({len(comm)} nodes)')
        for i, comm in enumerate(communities)
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=9, framealpha=0.9)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def visualize_community_vs_tissue(G, communities, community_map, output_file):
    """
    커뮤니티 vs 실제 조직 타입 비교
    Side-by-side 시각화
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 왼쪽: 실제 조직 타입
    tissue_colors = [G.nodes[n]['color'] for n in G.nodes()]
    
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5,
                          edge_color='gray', ax=ax1)
    nx.draw_networkx_nodes(G, pos, node_color=tissue_colors,
                          node_size=120, alpha=0.9,
                          edgecolors='black', linewidths=0.5, ax=ax1)
    
    ax1.invert_yaxis()
    ax1.set_title('Ground Truth: Actual Tissue Types\n(From AI model prediction)', 
                  fontsize=13, pad=15)
    ax1.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax1.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 오른쪽: 커뮤니티
    num_communities = len(communities)
    comm_colors_palette = plt.cm.tab20(np.linspace(0, 1, num_communities))
    comm_colors = [comm_colors_palette[community_map[n]] for n in G.nodes()]
    
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5,
                          edge_color='gray', ax=ax2)
    nx.draw_networkx_nodes(G, pos, node_color=comm_colors,
                          node_size=120, alpha=0.9,
                          edgecolors='black', linewidths=0.5, ax=ax2)
    
    ax2.invert_yaxis()
    ax2.set_title('Community Detection: Graph Structure Only\n(No tissue type information used)', 
                  fontsize=13, pad=15)
    ax2.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax2.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 범례 (조직 타입)
    from matplotlib.patches import Patch
    present_classes = set(G.nodes[n]['prediction'] for n in G.nodes())
    legend_elements = [
        Patch(facecolor=CLASS_COLORS[cls], edgecolor='black',
              label=f'{CLASS_NAMES[cls]} ({cls})')
        for cls in sorted(present_classes)
    ]
    fig.legend(handles=legend_elements, loc='upper center',
              ncol=len(legend_elements), fontsize=10,
              framealpha=0.9, bbox_to_anchor=(0.5, 0.98))
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def save_community_statistics(G, communities, community_map, 
                              purity_scores, output_file):
    """통계 저장"""
    with open(output_file, 'w') as f:
        f.write("Community Detection Statistics\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Total nodes: {G.number_of_nodes()}\n")
        f.write(f"Total communities: {len(communities)}\n")
        f.write(f"Average purity: {np.mean(purity_scores):.3f}\n\n")
        
        f.write("Community composition:\n")
        f.write("-"*60 + "\n")
        
        for comm_id, comm_nodes in enumerate(communities):
            f.write(f"\nCommunity {comm_id} ({len(comm_nodes)} nodes):\n")
            
            class_counts = Counter([G.nodes[n]['prediction'] for n in comm_nodes])
            
            for cls in sorted(class_counts.keys()):
                count = class_counts[cls]
                percentage = count / len(comm_nodes) * 100
                f.write(f"  {CLASS_NAMES[cls]:6s} ({cls}): {count:4d} nodes ({percentage:5.1f}%)\n")
            
            f.write(f"  Purity: {purity_scores[comm_id]:.3f}\n")
    
    print(f"✓ Statistics saved: {output_file}")


def main():
    if len(sys.argv) > 1:
        wsi_name = sys.argv[1]
    else:
        wsi_name = "CMU-1-Small-Region"
    
    print(f"\n{'='*60}")
    print(f"Community Detection: {wsi_name}")
    print(f"{'='*60}\n")
    
    input_dir = Path("/results") / wsi_name
    graph_file = input_dir / "graph.pkl"
    
    # 1. 그래프 로드
    G = load_graph(graph_file)
    
    # 2. 커뮤니티 탐지
    communities, community_map = detect_communities(G)
    
    # 3. 커뮤니티 구성 분석
    purity_scores = analyze_community_composition(G, communities, community_map)
    
    # 4. 시각화 1: 커뮤니티
    print("\n[1/2] Creating community visualization...")
    visualize_communities(G, communities, community_map, 
                         input_dir / "communities.png")
    
    # 5. 시각화 2: 비교
    print("\n[2/2] Creating comparison visualization...")
    visualize_community_vs_tissue(G, communities, community_map,
                                 input_dir / "communities_vs_tissue.png")
    
    # 6. 통계 저장
    print("\nSaving statistics...")
    save_community_statistics(G, communities, community_map,
                             purity_scores, input_dir / "community_statistics.txt")
    
    print(f"\n{'='*60}")
    print(f"✓ Completed: {wsi_name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()