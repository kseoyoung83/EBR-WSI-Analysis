# myscripts/visualize_graph.py

import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
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


def visualize_basic_graph(G, output_file):
    """기본 그래프 시각화"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # 노드 위치: 실제 좌표
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    node_colors = [data['color'] for node, data in G.nodes(data=True)]
    
    # 엣지 먼저 그리기
    nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5, 
                          edge_color='gray', ax=ax)
    
    # 노드 그리기
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                          node_size=120, alpha=0.9,
                          edgecolors='black', linewidths=0.5, ax=ax)
    
    ax.invert_yaxis()
    ax.set_title('Slide Graph Structure\n(Nodes: Tissue Patches, Edges: Spatial Adjacency)', 
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


def visualize_connectivity(G, output_file):
    """연결성 맵 (degree 기반)"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    degrees = dict(G.degree())
    node_degrees = [degrees[node] for node in G.nodes()]
    
    nx.draw_networkx_edges(G, pos, alpha=0.15, width=0.5,
                          edge_color='gray', ax=ax)
    
    nodes = nx.draw_networkx_nodes(G, pos, node_color=node_degrees,
                                   node_size=150, cmap='YlOrRd',
                                   vmin=min(node_degrees),
                                   vmax=max(node_degrees),
                                   edgecolors='black', linewidths=0.5, ax=ax)
    
    cbar = plt.colorbar(nodes, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Node Degree (Number of Connections)', fontsize=11)
    
    ax.invert_yaxis()
    ax.set_title('Graph Connectivity Map\n(Node color: Number of neighbors)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def compare_with_week6(G, output_file):
    """Week 6 vs Week 7 비교"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    node_colors = [data['color'] for node, data in G.nodes(data=True)]
    
    # 왼쪽: Week 6 스타일
    coords = np.array([data['pos'] for node, data in G.nodes(data=True)])
    ax1.scatter(coords[:, 0], coords[:, 1], c=node_colors, s=120,
               alpha=0.9, edgecolors='black', linewidths=0.5)
    ax1.invert_yaxis()
    ax1.set_title('Week 6: Spatial Map\n(Independent patches)', 
                  fontsize=13, pad=15)
    ax1.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax1.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 오른쪽: Week 7 그래프
    nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5,
                          edge_color='gray', ax=ax2)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                          node_size=120, alpha=0.9,
                          edgecolors='black', linewidths=0.5, ax=ax2)
    ax2.invert_yaxis()
    ax2.set_title('Week 7: Slide Graph\n(Connected patches with relationships)', 
                  fontsize=13, pad=15)
    ax2.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax2.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 범례
    from matplotlib.patches import Patch
    present_classes = set(data['prediction'] for node, data in G.nodes(data=True))
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


def main():
    if len(sys.argv) > 1:
        wsi_name = sys.argv[1]
    else:
        wsi_name = "CMU-1-Small-Region"
    
    print(f"\n{'='*60}")
    print(f"Visualizing Graph: {wsi_name}")
    print(f"{'='*60}\n")
    
    input_dir = Path("/results") / wsi_name
    graph_file = input_dir / "graph.pkl"
    
    G = load_graph(graph_file)
    
    print("\n[1/3] Creating basic graph visualization...")
    visualize_basic_graph(G, input_dir / "graph_structure.png")
    
    print("\n[2/3] Creating connectivity map...")
    visualize_connectivity(G, input_dir / "connectivity_map.png")
    
    print("\n[3/3] Creating Week 6 vs Week 7 comparison...")
    compare_with_week6(G, input_dir / "week6_vs_week7_comparison.png")
    
    print(f"\n{'='*60}")
    print(f"✓ Completed: {wsi_name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()