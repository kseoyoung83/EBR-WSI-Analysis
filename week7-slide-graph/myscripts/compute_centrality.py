# myscripts/compute_centrality.py

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
    with open(graph_file, 'rb') as f:
        G = pickle.load(f)
    print(f"✓ Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def compute_centralities(G):
    """
    중심성 계산
    1. Degree centrality: 연결 개수
    2. Betweenness centrality: 경로의 중심
    """
    print("\nComputing centralities...")
    
    # Degree centrality (빠름)
    print("  - Degree centrality...")
    degree_cent = nx.degree_centrality(G)
    
    # Betweenness centrality (느림, 큰 그래프에서는 시간 걸림)
    print("  - Betweenness centrality (this may take a while)...")
    betweenness_cent = nx.betweenness_centrality(G)
    
    print("✓ Centralities computed")
    
    return degree_cent, betweenness_cent


def analyze_centrality_statistics(G, degree_cent, betweenness_cent):
    """중심성 통계 분석"""
    print("\n" + "="*60)
    print("Centrality Statistics")
    print("="*60)
    
    # Degree centrality
    degree_values = list(degree_cent.values())
    print(f"\nDegree Centrality:")
    print(f"  Mean: {np.mean(degree_values):.4f}")
    print(f"  Max:  {np.max(degree_values):.4f}")
    print(f"  Min:  {np.min(degree_values):.4f}")
    
    # Top 5 degree centrality nodes
    top_degree = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\nTop 5 nodes by degree centrality:")
    for node, cent in top_degree:
        tissue = CLASS_NAMES[G.nodes[node]['prediction']]
        pos = G.nodes[node]['pos']
        print(f"  Node {node:4d} ({tissue:6s}): {cent:.4f} at position {pos}")
    
    # Betweenness centrality
    between_values = list(betweenness_cent.values())
    print(f"\nBetweenness Centrality:")
    print(f"  Mean: {np.mean(between_values):.4f}")
    print(f"  Max:  {np.max(between_values):.4f}")
    print(f"  Min:  {np.min(between_values):.4f}")
    
    # Top 5 betweenness centrality nodes
    top_between = sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\nTop 5 nodes by betweenness centrality:")
    for node, cent in top_between:
        tissue = CLASS_NAMES[G.nodes[node]['prediction']]
        pos = G.nodes[node]['pos']
        print(f"  Node {node:4d} ({tissue:6s}): {cent:.4f} at position {pos}")
    
    print("="*60 + "\n")
    
    return top_degree, top_between


def find_boundary_nodes(G):
    """경계 노드 찾기 (서로 다른 조직과 연결된 노드)"""
    boundary_nodes = set()
    
    for node in G.nodes():
        node_class = G.nodes[node]['prediction']
        neighbors = list(G.neighbors(node))
        
        # 이웃 중 다른 클래스가 있는지 확인
        for neighbor in neighbors:
            if G.nodes[neighbor]['prediction'] != node_class:
                boundary_nodes.add(node)
                break
    
    return boundary_nodes


def analyze_boundary_centrality(G, degree_cent, betweenness_cent):
    """경계 노드의 중심성 분석"""
    boundary_nodes = find_boundary_nodes(G)
    
    print(f"Boundary nodes: {len(boundary_nodes)} ({len(boundary_nodes)/G.number_of_nodes()*100:.1f}%)")
    
    # 경계 노드의 평균 중심성
    boundary_degree = [degree_cent[n] for n in boundary_nodes]
    boundary_between = [betweenness_cent[n] for n in boundary_nodes]
    
    # 내부 노드의 평균 중심성
    internal_nodes = set(G.nodes()) - boundary_nodes
    internal_degree = [degree_cent[n] for n in internal_nodes]
    internal_between = [betweenness_cent[n] for n in internal_nodes]
    
    print(f"\nBoundary vs Internal nodes:")
    print(f"  Degree centrality:")
    print(f"    Boundary: {np.mean(boundary_degree):.4f}")
    print(f"    Internal: {np.mean(internal_degree):.4f}")
    print(f"  Betweenness centrality:")
    print(f"    Boundary: {np.mean(boundary_between):.4f}")
    print(f"    Internal: {np.mean(internal_between):.4f}")
    
    return boundary_nodes


def visualize_degree_centrality(G, degree_cent, output_file):
    """Degree centrality 시각화"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 중심성에 따라 노드 크기와 색상
    node_sizes = [degree_cent[node] * 3000 for node in G.nodes()]
    node_colors = [degree_cent[node] for node in G.nodes()]
    
    # 엣지
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5,
                          edge_color='gray', ax=ax)
    
    # 노드
    nodes = nx.draw_networkx_nodes(G, pos,
                                   node_color=node_colors,
                                   node_size=node_sizes,
                                   cmap='YlOrRd',
                                   vmin=min(node_colors),
                                   vmax=max(node_colors),
                                   edgecolors='black',
                                   linewidths=0.5,
                                   ax=ax)
    
    # 컬러바
    cbar = plt.colorbar(nodes, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Degree Centrality', fontsize=11)
    
    ax.invert_yaxis()
    ax.set_title('Degree Centrality Map\n(Node size/color: Number of connections)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def visualize_betweenness_centrality(G, betweenness_cent, output_file):
    """Betweenness centrality 시각화"""
    fig, ax = plt.subplots(figsize=(14, 12))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 중심성에 따라 노드 크기와 색상
    node_sizes = [betweenness_cent[node] * 10000 + 50 for node in G.nodes()]
    node_colors = [betweenness_cent[node] for node in G.nodes()]
    
    # 엣지
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5,
                          edge_color='gray', ax=ax)
    
    # 노드
    nodes = nx.draw_networkx_nodes(G, pos,
                                   node_color=node_colors,
                                   node_size=node_sizes,
                                   cmap='plasma',
                                   vmin=min(node_colors),
                                   vmax=max(node_colors),
                                   edgecolors='black',
                                   linewidths=0.5,
                                   ax=ax)
    
    # 컬러바
    cbar = plt.colorbar(nodes, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Betweenness Centrality', fontsize=11)
    
    ax.invert_yaxis()
    ax.set_title('Betweenness Centrality Map\n(Node size/color: Importance in network paths)', 
                 fontsize=14, pad=20)
    ax.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def visualize_combined_centrality(G, degree_cent, betweenness_cent, 
                                  boundary_nodes, output_file):
    """통합 시각화: 경계 노드 + 중심성"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    pos = {node: data['pos'] for node, data in G.nodes(data=True)}
    
    # 왼쪽: Degree centrality + 경계 노드
    boundary_list = list(boundary_nodes)
    internal_list = [n for n in G.nodes() if n not in boundary_nodes]
    
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5,
                          edge_color='gray', ax=ax1)
    
    # 내부 노드 (작게)
    if internal_list:
        internal_sizes = [degree_cent[n] * 1500 for n in internal_list]
        internal_colors = [degree_cent[n] for n in internal_list]
        nx.draw_networkx_nodes(G, pos, nodelist=internal_list,
                              node_color=internal_colors,
                              node_size=internal_sizes,
                              cmap='YlOrRd', alpha=0.6,
                              edgecolors='gray', linewidths=0.3, ax=ax1)
    
    # 경계 노드 (크게, 강조)
    if boundary_list:
        boundary_sizes = [degree_cent[n] * 2000 for n in boundary_list]
        boundary_colors = [degree_cent[n] for n in boundary_list]
        nx.draw_networkx_nodes(G, pos, nodelist=boundary_list,
                              node_color=boundary_colors,
                              node_size=boundary_sizes,
                              cmap='YlOrRd', alpha=1.0,
                              edgecolors='red', linewidths=1.5, ax=ax1)
    
    ax1.invert_yaxis()
    ax1.set_title('Degree Centrality\n(Red outline: boundary nodes)', 
                  fontsize=13, pad=15)
    ax1.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax1.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 오른쪽: Betweenness centrality + 경계 노드
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5,
                          edge_color='gray', ax=ax2)
    
    # 내부 노드
    if internal_list:
        internal_sizes = [betweenness_cent[n] * 5000 + 30 for n in internal_list]
        internal_colors = [betweenness_cent[n] for n in internal_list]
        nx.draw_networkx_nodes(G, pos, nodelist=internal_list,
                              node_color=internal_colors,
                              node_size=internal_sizes,
                              cmap='plasma', alpha=0.6,
                              edgecolors='gray', linewidths=0.3, ax=ax2)
    
    # 경계 노드
    if boundary_list:
        boundary_sizes = [betweenness_cent[n] * 6000 + 50 for n in boundary_list]
        boundary_colors = [betweenness_cent[n] for n in boundary_list]
        nx.draw_networkx_nodes(G, pos, nodelist=boundary_list,
                              node_color=boundary_colors,
                              node_size=boundary_sizes,
                              cmap='plasma', alpha=1.0,
                              edgecolors='red', linewidths=1.5, ax=ax2)
    
    ax2.invert_yaxis()
    ax2.set_title('Betweenness Centrality\n(Red outline: boundary nodes)', 
                  fontsize=13, pad=15)
    ax2.set_xlabel('X coordinate (pixels)', fontsize=11)
    ax2.set_ylabel('Y coordinate (pixels)', fontsize=11)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved: {output_file}")


def save_centrality_statistics(G, degree_cent, betweenness_cent,
                               top_degree, top_between, boundary_nodes, 
                               output_file):
    """통계 저장"""
    with open(output_file, 'w') as f:
        f.write("Centrality Analysis Statistics\n")
        f.write("="*60 + "\n\n")
        
        # Degree centrality
        degree_values = list(degree_cent.values())
        f.write("Degree Centrality:\n")
        f.write(f"  Mean: {np.mean(degree_values):.4f}\n")
        f.write(f"  Max:  {np.max(degree_values):.4f}\n")
        f.write(f"  Min:  {np.min(degree_values):.4f}\n\n")
        
        f.write("Top 10 nodes by degree centrality:\n")
        top_10_degree = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
        for node, cent in top_10_degree:
            tissue = CLASS_NAMES[G.nodes[node]['prediction']]
            pos = G.nodes[node]['pos']
            f.write(f"  Node {node:4d} ({tissue:6s}): {cent:.4f} at {pos}\n")
        
        # Betweenness centrality
        between_values = list(betweenness_cent.values())
        f.write(f"\nBetweenness Centrality:\n")
        f.write(f"  Mean: {np.mean(between_values):.4f}\n")
        f.write(f"  Max:  {np.max(between_values):.4f}\n")
        f.write(f"  Min:  {np.min(between_values):.4f}\n\n")
        
        f.write("Top 10 nodes by betweenness centrality:\n")
        top_10_between = sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:10]
        for node, cent in top_10_between:
            tissue = CLASS_NAMES[G.nodes[node]['prediction']]
            pos = G.nodes[node]['pos']
            f.write(f"  Node {node:4d} ({tissue:6s}): {cent:.4f} at {pos}\n")
        
        # Boundary analysis
        boundary_degree = [degree_cent[n] for n in boundary_nodes]
        boundary_between = [betweenness_cent[n] for n in boundary_nodes]
        internal_nodes = set(G.nodes()) - boundary_nodes
        internal_degree = [degree_cent[n] for n in internal_nodes]
        internal_between = [betweenness_cent[n] for n in internal_nodes]
        
        f.write(f"\nBoundary vs Internal nodes:\n")
        f.write(f"  Boundary nodes: {len(boundary_nodes)} ({len(boundary_nodes)/G.number_of_nodes()*100:.1f}%)\n")
        f.write(f"  Internal nodes: {len(internal_nodes)} ({len(internal_nodes)/G.number_of_nodes()*100:.1f}%)\n\n")
        f.write(f"  Degree centrality:\n")
        f.write(f"    Boundary: {np.mean(boundary_degree):.4f}\n")
        f.write(f"    Internal: {np.mean(internal_degree):.4f}\n")
        f.write(f"  Betweenness centrality:\n")
        f.write(f"    Boundary: {np.mean(boundary_between):.4f}\n")
        f.write(f"    Internal: {np.mean(internal_between):.4f}\n")
    
    print(f"✓ Statistics saved: {output_file}")


def main():
    if len(sys.argv) > 1:
        wsi_name = sys.argv[1]
    else:
        wsi_name = "CMU-1-Small-Region"
    
    print(f"\n{'='*60}")
    print(f"Centrality Analysis: {wsi_name}")
    print(f"{'='*60}\n")
    
    input_dir = Path("/results") / wsi_name
    graph_file = input_dir / "graph.pkl"
    
    # 1. 그래프 로드
    G = load_graph(graph_file)
    
    # 2. 중심성 계산
    degree_cent, betweenness_cent = compute_centralities(G)
    
    # 3. 통계 분석
    top_degree, top_between = analyze_centrality_statistics(G, degree_cent, betweenness_cent)
    
    # 4. 경계 노드 분석
    print("\nAnalyzing boundary nodes...")
    boundary_nodes = analyze_boundary_centrality(G, degree_cent, betweenness_cent)
    
    # 5. 시각화 1: Degree centrality
    print("\n[1/3] Creating degree centrality visualization...")
    visualize_degree_centrality(G, degree_cent, 
                               input_dir / "centrality_degree.png")
    
    # 6. 시각화 2: Betweenness centrality
    print("\n[2/3] Creating betweenness centrality visualization...")
    visualize_betweenness_centrality(G, betweenness_cent,
                                    input_dir / "centrality_betweenness.png")
    
    # 7. 시각화 3: 통합
    print("\n[3/3] Creating combined visualization...")
    visualize_combined_centrality(G, degree_cent, betweenness_cent,
                                  boundary_nodes, 
                                  input_dir / "centrality_combined.png")
    
    # 8. 통계 저장
    print("\nSaving statistics...")
    save_centrality_statistics(G, degree_cent, betweenness_cent,
                              top_degree, top_between, boundary_nodes,
                              input_dir / "centrality_statistics.txt")
    
    print(f"\n{'='*60}")
    print(f"✓ Completed: {wsi_name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()