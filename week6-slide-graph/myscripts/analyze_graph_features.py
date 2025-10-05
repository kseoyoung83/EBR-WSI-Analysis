#!/usr/bin/env python3
"""
Week 6: Analyze extracted features for graph construction
Spatial pattern analysis and visualization
"""

import sys
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from collections import Counter
from tiatoolbox.wsicore.wsireader import WSIReader

# Kather 100k class definitions
CLASS_NAMES = {
    0: "BACK", 1: "NORM", 2: "DEB", 3: "TUM",
    4: "ADI", 5: "MUC", 6: "MUS", 7: "STR", 8: "LYM"
}

CLASS_NAMES_FULL = {
    0: "Background",
    1: "Normal colon mucosa",
    2: "Debris",
    3: "Colorectal adenocarcinoma (Tumor)",
    4: "Adipose tissue",
    5: "Mucus",
    6: "Smooth muscle",
    7: "Cancer-associated stroma",
    8: "Lymphocytes"
}

# Color map for visualization
CLASS_COLORS = {
    0: (0.9, 0.9, 0.9),    # BACK - light gray
    1: (0.3, 0.7, 0.3),    # NORM - green
    2: (0.6, 0.4, 0.2),    # DEB - brown
    3: (0.8, 0.1, 0.1),    # TUM - red
    4: (1.0, 0.8, 0.0),    # ADI - yellow
    5: (0.7, 0.5, 0.7),    # MUC - purple
    6: (0.9, 0.3, 0.5),    # MUS - pink
    7: (0.2, 0.5, 0.8),    # STR - blue
    8: (0.5, 0.2, 0.8),    # LYM - violet
}

def load_predictions(predictions_file):
    """Load predictions JSON"""
    with open(predictions_file, 'r') as f:
        data = json.load(f)
    return data

def analyze_class_distribution(predictions, output_dir):
    """Analyze and visualize class distribution"""
    print("\n" + "=" * 60)
    print("Class Distribution Analysis")
    print("=" * 60)
    
    output_dir = Path(output_dir)
    
    # Count classes
    class_counts = Counter(predictions)
    total = len(predictions)
    
    # Print statistics
    print(f"\nTotal patches: {total}")
    print("\nClass distribution:")
    for class_id in sorted(class_counts.keys()):
        count = class_counts[class_id]
        ratio = count / total * 100
        print(f"  {CLASS_NAMES[class_id]:6s} ({class_id}): {count:3d} patches ({ratio:5.1f}%)")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(12, 6))
    
    classes = sorted(class_counts.keys())
    counts = [class_counts[c] for c in classes]
    colors = [CLASS_COLORS[c] for c in classes]
    labels = [f"{CLASS_NAMES[c]}\n({CLASS_NAMES_FULL[c]})" for c in classes]
    
    bars = ax.bar(range(len(classes)), counts, color=colors, edgecolor='black', linewidth=1)
    ax.set_xticks(range(len(classes)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Number of patches', fontsize=12)
    ax.set_title('Tissue Type Distribution', fontsize=14, pad=15)
    
    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / "class_distribution.png", dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: class_distribution.png")

def visualize_spatial_map(coordinates, predictions, output_dir, patch_size=224):
    """Visualize spatial distribution with tissue types"""
    print("\n" + "=" * 60)
    print("Spatial Tissue Map")
    print("=" * 60)
    
    output_dir = Path(output_dir)
    coords = np.array(coordinates)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Draw patches as colored rectangles
    for coord, pred in zip(coords, predictions):
        x, y = coord[0], coord[1]
        color = CLASS_COLORS[pred]
        rect = Rectangle((x, y), patch_size, patch_size, 
                         facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.7)
        ax.add_patch(rect)
    
    # Set limits
    ax.set_xlim(coords[:, 0].min() - 50, coords[:, 0].max() + patch_size + 50)
    ax.set_ylim(coords[:, 1].min() - 50, coords[:, 1].max() + patch_size + 50)
    ax.invert_yaxis()
    
    ax.set_xlabel('X coordinate (pixels)', fontsize=12)
    ax.set_ylabel('Y coordinate (pixels)', fontsize=12)
    ax.set_title('Spatial Distribution of Tissue Types', fontsize=14, pad=15)
    ax.set_aspect('equal')
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=CLASS_COLORS[i], edgecolor='black', 
                             label=f"{CLASS_NAMES[i]}: {CLASS_NAMES_FULL[i]}")
                      for i in sorted(set(predictions))]
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=9, frameon=True)
    
    plt.tight_layout()
    plt.savefig(output_dir / "spatial_tissue_map.png", dpi=150, bbox_inches='tight')
    print(f"✓ Saved: spatial_tissue_map.png")

def analyze_uncertainty(probabilities, coordinates, predictions, output_dir):
    """Analyze prediction uncertainty (entropy)"""
    print("\n" + "=" * 60)
    print("Uncertainty Analysis")
    print("=" * 60)
    
    output_dir = Path(output_dir)
    probs = np.array(probabilities)
    coords = np.array(coordinates)
    
    # Calculate entropy for each patch
    epsilon = 1e-10
    entropy = -np.sum(probs * np.log(probs + epsilon), axis=1)
    
    # Normalize to 0-1
    max_entropy = np.log(9)  # 9 classes
    normalized_entropy = entropy / max_entropy
    
    # Statistics
    print(f"\nMean uncertainty: {normalized_entropy.mean():.3f}")
    print(f"Max uncertainty: {normalized_entropy.max():.3f}")
    print(f"Min uncertainty: {normalized_entropy.min():.3f}")
    
    # Find most uncertain patches
    uncertain_idx = np.argsort(normalized_entropy)[-5:]
    print("\nTop 5 most uncertain patches:")
    for idx in uncertain_idx[::-1]:
        pred_class = predictions[idx]
        max_prob = probs[idx].max()
        print(f"  Patch at {coords[idx]}: {CLASS_NAMES[pred_class]} "
              f"(confidence: {max_prob:.2f}, uncertainty: {normalized_entropy[idx]:.3f})")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(12, 10))
    scatter = ax.scatter(coords[:, 0], coords[:, 1], 
                        c=normalized_entropy, cmap='YlOrRd', 
                        s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
    ax.invert_yaxis()
    ax.set_xlabel('X coordinate', fontsize=12)
    ax.set_ylabel('Y coordinate', fontsize=12)
    ax.set_title('Prediction Uncertainty Map\n(Red = High uncertainty, Yellow = Low uncertainty)', 
                 fontsize=14, pad=15)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Normalized Entropy', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_dir / "uncertainty_map.png", dpi=150, bbox_inches='tight')
    print(f"✓ Saved: uncertainty_map.png")

def find_tumor_regions(coordinates, predictions, output_dir):
    """Identify and visualize tumor regions"""
    print("\n" + "=" * 60)
    print("Tumor Region Analysis")
    print("=" * 60)
    
    output_dir = Path(output_dir)
    coords = np.array(coordinates)
    
    # Find tumor patches (class 3)
    tumor_idx = [i for i, pred in enumerate(predictions) if pred == 3]
    
    if len(tumor_idx) == 0:
        print("No tumor patches found")
        return
    
    tumor_coords = coords[tumor_idx]
    
    print(f"\nTotal tumor patches: {len(tumor_idx)} ({len(tumor_idx)/len(predictions)*100:.1f}%)")
    print(f"Tumor region bounds:")
    print(f"  X: {tumor_coords[:, 0].min()} - {tumor_coords[:, 0].max()}")
    print(f"  Y: {tumor_coords[:, 1].min()} - {tumor_coords[:, 1].max()}")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # All patches in gray
    ax.scatter(coords[:, 0], coords[:, 1], c='lightgray', s=50, alpha=0.5, label='Other')
    
    # Tumor patches in red
    ax.scatter(tumor_coords[:, 0], tumor_coords[:, 1], c='red', s=100, 
               alpha=0.8, edgecolors='darkred', linewidth=1, label='Tumor')
    
    ax.invert_yaxis()
    ax.set_xlabel('X coordinate', fontsize=12)
    ax.set_ylabel('Y coordinate', fontsize=12)
    ax.set_title('Tumor Region Localization', fontsize=14, pad=15)
    ax.legend(fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_dir / "tumor_localization.png", dpi=150, bbox_inches='tight')
    print(f"✓ Saved: tumor_localization.png")

def main():
    # Configuration
    wsi_filename = "CMU-1-Small-Region"
    
    if len(sys.argv) > 1:
        wsi_filename = sys.argv[1]
    
    predictions_file = f"/results/{wsi_filename}/predictions/predictions.json"
    output_dir = f"/results/{wsi_filename}"
    
    print("=" * 60)
    print(f"Graph Feature Analysis: {wsi_filename}")
    print("=" * 60)
    
    # Load data
    data = load_predictions(predictions_file)
    coordinates = data['coordinates']
    predictions = data['predictions']
    probabilities = data.get('probabilities', None)
    
    print(f"\nLoaded {len(predictions)} patches")
    
    # Analysis 1: Class distribution
    analyze_class_distribution(predictions, output_dir)
    
    # Analysis 2: Spatial tissue map
    visualize_spatial_map(coordinates, predictions, output_dir)
    
    # Analysis 3: Uncertainty analysis
    if probabilities is not None:
        analyze_uncertainty(probabilities, coordinates, predictions, output_dir)
    
    # Analysis 4: Tumor localization
    find_tumor_regions(coordinates, predictions, output_dir)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()