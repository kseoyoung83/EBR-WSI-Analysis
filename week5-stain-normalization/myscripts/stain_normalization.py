#!/usr/bin/env python3
"""
Week 5: Stain Normalization
Compare different normalization methods on WSI thumbnails
"""

import sys
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from tiatoolbox.wsicore.wsireader import WSIReader
from tiatoolbox.tools import stainnorm

def load_wsi_thumbnail(wsi_path, resolution=4.0, units="mpp"):
    """Load WSI thumbnail"""
    reader = WSIReader.open(wsi_path)
    thumbnail = reader.slide_thumbnail(resolution=resolution, units=units)
    return thumbnail

def compare_normalization_methods(target_img, source_img, output_dir):
    """
    Compare different stain normalization methods
    
    Args:
        target_img: Target image (reference)
        source_img: Source image (to be normalized)
        output_dir: Output directory
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Normalization methods
    methods = {
        'Macenko': stainnorm.MacenkoNormalizer(),
        'Vahadane': stainnorm.VahadaneNormalizer(),
        'Reinhard': stainnorm.ReinhardNormalizer()
    }
    
    # Fit normalizers with target image
    print("Fitting normalizers with target image...")
    for name, normalizer in methods.items():
        normalizer.fit(target_img)
        print(f"  - {name}: fitted")
    
    # Transform source image
    print("\nNormalizing source image...")
    normalized_images = {}
    for name, normalizer in methods.items():
        normalized = normalizer.transform(source_img)
        normalized_images[name] = normalized
        print(f"  - {name}: transformed")
    
    # Visualize: 2x3 grid (6칸)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Row 1: Source, Target, Macenko
    axes[0, 0].imshow(source_img)
    axes[0, 0].set_title("Source Image", fontsize=14, pad=10)
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(target_img)
    axes[0, 1].set_title("Target Image (Reference)", fontsize=14, pad=10)
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(normalized_images['Macenko'])
    axes[0, 2].set_title("Macenko Normalized", fontsize=14, pad=10)
    axes[0, 2].axis('off')
    
    # Row 2: Vahadane, Reinhard, 빈칸
    axes[1, 0].imshow(normalized_images['Vahadane'])
    axes[1, 0].set_title("Vahadane Normalized", fontsize=14, pad=10)
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(normalized_images['Reinhard'])
    axes[1, 1].set_title("Reinhard Normalized", fontsize=14, pad=10)
    axes[1, 1].axis('off')
    
    # 빈칸 숨기기
    axes[1, 2].axis('off')
    
    plt.tight_layout(pad=2.0)
    plt.savefig(output_dir / "normalization_comparison.png", dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: normalization_comparison.png")
        
    # Save individual normalized images
    for name, img in normalized_images.items():
        Image.fromarray(img).save(output_dir / f"normalized_{name.lower()}.png")
        print(f"✓ Saved: normalized_{name.lower()}.png")
    
    return normalized_images

def main():
    # WSI files
    target_wsi = "/data/CMU-1-Small-Region.svs"
    source_wsi = "/data/TEST_sample1.svs"
    output_dir = "/results"
    
    # Allow command-line override
    if len(sys.argv) > 1:
        source_wsi = f"/data/{sys.argv[1]}.svs"
    
    print("=" * 60)
    print("Stain Normalization Comparison")
    print("=" * 60)
    print(f"\nTarget (reference): {target_wsi}")
    print(f"Source (to normalize): {source_wsi}")
    
    # Load thumbnails
    print("\nLoading WSI thumbnails...")
    target_thumbnail = load_wsi_thumbnail(target_wsi)
    source_thumbnail = load_wsi_thumbnail(source_wsi)
    print(f"Target shape: {target_thumbnail.shape}")
    print(f"Source shape: {source_thumbnail.shape}")
    
    # Compare normalization methods
    normalized = compare_normalization_methods(
        target_thumbnail,
        source_thumbnail,
        output_dir
    )
    
    print("\n" + "=" * 60)
    print("Stain normalization complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()