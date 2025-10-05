#!/usr/bin/env python3
"""
Generate thumbnails at multiple resolutions and create comparison image
"""

import os
from PIL import Image
from tiatoolbox.wsicore.wsireader import WSIReader
import matplotlib.pyplot as plt

def generate_multi_resolution(input_path, output_dir):
    """Generate thumbnails at different resolutions and compare"""
    
    print(f"Opening WSI: {input_path}")
    reader = WSIReader.open(input_path)
    
    resolutions = [0.5, 1.25, 2.5, 5.0]
    thumbnails = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Generate individual thumbnails
    for res in resolutions:
        thumbnail = reader.slide_thumbnail(resolution=res, units="power")
        
        filename = f"thumbnail_res_{res}x.png"
        output_path = os.path.join(output_dir, filename)
        Image.fromarray(thumbnail).save(output_path)
        
        thumbnails.append((res, thumbnail))
        print(f"Resolution {res}x: {thumbnail.shape} -> {output_path}")
    
    # Step 2: Create comparison image
    print("\nCreating comparison image...")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, (res, thumb) in enumerate(thumbnails):
        axes[idx].imshow(thumb)
        axes[idx].set_title(f"Resolution: {res}x\nSize: {thumb.shape[:2]}", 
                           fontsize=12, pad=10)
        axes[idx].axis('off')
    
    plt.tight_layout(pad=2.0)
    
    comparison_path = os.path.join(output_dir, "resolution_comparison.png")
    plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
    
    print(f"Comparison saved to: {comparison_path}")

if __name__ == "__main__":
    generate_multi_resolution("/data/CMU-1-Small-Region.svs", "/results")