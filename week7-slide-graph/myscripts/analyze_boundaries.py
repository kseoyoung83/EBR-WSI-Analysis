
# myscripts/analyze_boundaries.py

import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
from collections import Counter
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
    """저장된 Graph 로드"""
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    print(f"✓ Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def find_boundary_edges(G):
    """
    조직 경계 엣지 찾기
    서로 다른 클래스를 연결하는 엣지 = 경계
    """
    boundary_edges = []
    boundary_types = []
    
    for u, v in G.edges():
        class_u = G.nodes[u]['prediction']
        class_v = G.nodes[v]['prediction']
        
        if class_u != class_v:
            boundary_edges.append((u, v))
            
            # 경계 타입 기록 (작은 번호를 앞에)
            boundary_type = tuple(sorted([class_u, class_v]))
            boundary_types.append(boundary_type)
    
    print(f"✓ Found {len(boundary_edges)} boundary edges ({len(boundary_edges)/G.number_of_edges()*100:.1f}%)")
    
    return boundary_edges, boundary_types


def analyze_boundary_statistics(G, boundary_edges, boundary_types):
    """경계 통계 분석"""
    print("\n" + "="*50)
    print("Boundary Statistics")
    print("="*50)
    
    # 전체 통계
    total_edges = G.number_of_edges()
    boundary_count = len(boundary_edges)
    internal_count = total_edges - boundary_count
    
    print(f"\nTotal edges: {total_edges}")
    print(f"  Boundary edges: {boundary_count} ({boundary_count/total_edges*100:.1f}%)")
    print(f"  Internal edges: {internal_count} ({internal_count/total_edges*100:.1f}%)")
    
    # 경계 타입별 통계
    boundary_counter = Counter(boundary_types)
    print(f"\nBoundary types (top 10):")
    
    for (cls1, cls2), count in boundary_counter.most_common(10):
        name1 = CLASS_NAMES[cls1]
        name2 = CLASS_NAMES[cls2]
        print(f"  {name1:6s} - {name2:6s}: {count:4d} edges ({count/boundary_count*100:.1f}%)")
    
    print("="*50 + "\n")
    
    return boundary_counter


def visualize_boundaries(G, boundary_edges, output_file):
    """경계 엣지 시각화"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    node_colors = [data['color'] for node, data in G.nodes(data=True)]
    
    # 내부 엣지 (회색, 얇게)
    internal_edges = [(u, v) for u, v in G.edges() 
                     if (u, v) not in boundary_edges and (v, u) not in boundary_edges]
    
    nx.draw_networkx_edges(G, pos, edgelist=internal_edges,
                          alpha=0.1, width=0.3, edge_color='lightgray', ax=ax)
    
    # 경계 엣지 (빨강, 굵게)
    nx.draw_networkx_edges(G, pos, edgelist=boundary_edges,
                          alpha=0.6, width=1.5, edge_color='red', ax=ax)
    
    # 노드
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                          node_size=100, alpha=0.8,
                          edgecolors='black', linewidths=0.5, ax=ax)
    
    ax.invert_yaxis()
    ax.set_title(f'Tissue Boundary Detection\n(Red edges: boundaries between different tissue types, {len(boundary_edges)} edges)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    
    # 범례
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    
    present_classes = set(data['prediction'] for node, data in G.nodes(data=True))
    legend_elements = [
        Patch(facecolor=CLASS_COLORS[cls], edgecolor='black',
              label=f'{CLASS_NAMES[cls]} ({cls})')
        for cls in sorted(present_classes)
    ]
    legend_elements.append(Line2D([0], [0], color='red', linewidth=2, 
                                  label='Boundary edge'))
    legend_elements.append(Line2D([0], [0], color='lightgray', linewidth=1, 
                                  label='Internal edge'))
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=9, framealpha=0.9)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def visualize_boundary_nodes(G, boundary_edges, output_file):
    """
    경계 노드 시각화
    경계 엣지에 연결된 노드를 강조
    """
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 경계 노드 찾기
    boundary_nodes = set()
    for u, v in boundary_edges:
        boundary_nodes.add(u)
        boundary_nodes.add(v)
    
    # 노드 분류
    boundary_node_list = list(boundary_nodes)
    internal_node_list = [n for n in G.nodes() if n not in boundary_nodes]
    
    # 엣지 그리기
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5,
                          edge_color='gray', ax=ax)
    
    # 내부 노드 (작고 연하게)
    if internal_node_list:
        internal_colors = [G.nodes[n]['color'] for n in internal_node_list]
        nx.draw_networkx_nodes(G, pos, nodelist=internal_node_list,
                              node_color=internal_colors, node_size=80,
                              alpha=0.4, edgecolors='gray', 
                              linewidths=0.3, ax=ax)
    
    # 경계 노드 (크고 진하게)
    if boundary_node_list:
        boundary_colors = [G.nodes[n]['color'] for n in boundary_node_list]
        nx.draw_networkx_nodes(G, pos, nodelist=boundary_node_list,
                              node_color=boundary_colors, node_size=150,
                              alpha=1.0, edgecolors='red',
                              linewidths=1.5, ax=ax)
    
    ax.invert_yaxis()
    ax.set_title(f'Boundary Nodes\n({len(boundary_nodes)} nodes at tissue boundaries, red outline)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    
    # 범례
    from matplotlib.patches import Patch
    present_classes = set(data['prediction'] for node, data in G.nodes(data=True))
    legend_elements = [
        Patch(facecolor=CLASS_COLORS[cls], edgecolor='black',
              label=f'{CLASS_NAMES[cls]} ({cls})')
        for cls in sorted(present_classes)
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=10, framealpha=0.9)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def save_boundary_statistics(G, boundary_edges, boundary_types, 
                             boundary_counter, output_file):
    """통계를 텍스트 파일로 저장"""
    with open(output_file, 'w') as f:
        f.write(f"Boundary Analysis Statistics\n")
        f.write("="*50 + "\n\n")
        
        total_edges = G.number_of_edges()
        boundary_count = len(boundary_edges)
        internal_count = total_edges - boundary_count
        
        f.write(f"Total edges: {total_edges}\n")
        f.write(f"  Boundary edges: {boundary_count} ({boundary_count/total_edges*100:.1f}%)\n")
        f.write(f"  Internal edges: {internal_count} ({internal_count/total_edges*100:.1f}%)\n")
        f.write("\n")
        
        f.write("Boundary types (all):\n")
        for (cls1, cls2), count in sorted(boundary_counter.items(), 
                                         key=lambda x: x[1], reverse=True):
            name1 = CLASS_NAMES[cls1]
            name2 = CLASS_NAMES[cls2]
            f.write(f"  {name1:6s} - {name2:6s}: {count:4d} edges ({count/boundary_count*100:.1f}%)\n")
    
    print(f"✓ Statistics saved: {output_file}")


def main():
    if len(sys.argv) > 1:
        wsi_name = sys.argv[1]
    else:
        wsi_name = "CMU-1-Small-Region"
    
    print(f"\n{'='*60}")
    print(f"Analyzing Boundaries: {wsi_name}")
    print(f"{'='*60}\n")
    
    input_dir = Path("/results") / wsi_name
    graph_file = input_dir / "graph.pkl"
    
    # 1. 그래프 로드
    G = load_graph(graph_file)
    
    # 2. 경계 엣지 찾기
    print("\nFinding boundary edges...")
    boundary_edges, boundary_types = find_boundary_edges(G)
    
    # 3. 통계 분석
    boundary_counter = analyze_boundary_statistics(G, boundary_edges, boundary_types)
    
    # 4. 시각화 1: 경계 엣지
    print("\n[1/2] Creating boundary edge visualization...")
    visualize_boundaries(G, boundary_edges, input_dir / "boundary_edges.png")
    
    # 5. 시각화 2: 경계 노드
    print("\n[2/2] Creating boundary node visualization...")
    visualize_boundary_nodes(G, boundary_edges, input_dir / "boundary_nodes.png")
    
    # 6. 통계 저장
    print("\nSaving statistics...")
    save_boundary_statistics(G, boundary_edges, boundary_types, 
                            boundary_counter, input_dir / "boundary_statistics.txt")
    
    print(f"\n{'='*60}")
    print(f"✓ Completed: {wsi_name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
