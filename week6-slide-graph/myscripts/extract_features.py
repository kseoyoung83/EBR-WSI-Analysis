#!/usr/bin/env python3
"""
Week 6: Feature Extraction from WSI patches
Extract deep features using pretrained ResNet50
"""

import sys
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from tiatoolbox.models.architecture import get_pretrained_model
from tiatoolbox.models.engine.patch_predictor import (
    PatchPredictor,
    IOPatchPredictorConfig
)

def extract_patch_features(wsi_path, output_dir, resolution=0.5, patch_size=224):
    """
    Extract features from WSI patches using pretrained ResNet50
    
    Args:
        wsi_path: Path to WSI file
        output_dir: Output directory
        resolution: Resolution for patch extraction (mpp)
        patch_size: Patch size in pixels
    
    Returns:
        Dictionary with features and coordinates
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Feature Extraction from WSI")
    print("=" * 60)
    print(f"\nWSI: {wsi_path}")
    print(f"Resolution: {resolution} mpp")
    print(f"Patch size: {patch_size}x{patch_size}")
    
    # Load pretrained model
    print("\nLoading pretrained ResNet50...")
    try:
        # Use resnet50 for feature extraction
        predictor = PatchPredictor(
            pretrained_model="resnet50-kather100k",
            batch_size=16
        )
        print("✓ Model loaded: ResNet50-kather100k")
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
    
    # Configure patch extraction
    ioconfig = IOPatchPredictorConfig(
        input_resolutions=[{"units": "mpp", "resolution": resolution}],
        patch_input_shape=[patch_size, patch_size],
        stride_shape=[patch_size, patch_size],  # No overlap
    )
    
    # Extract features
    print("\nExtracting features from patches...")
    print("This may take several minutes...")
    
    try:
        output = predictor.predict(
            imgs=[Path(wsi_path)],
            mode="wsi",
            ioconfig=ioconfig,
            save_dir=output_dir / "predictions",
            return_probabilities=True,  # Return features, not predictions
            device="cpu"
        )
        
        print(f"\n✓ Features extracted")

        import json
        predictions_dir = output_dir / "predictions"
        predictions_dir.mkdir(parents=True, exist_ok=True)

        if output and len(output) > 0:
            output_file = predictions_dir / "predictions.json"
            with open(output_file, 'w') as f:
            # output[0]를 직렬화 가능한 형태로 변환
                save_data = {
                    'predictions': output[0].get('predictions', []).tolist() if hasattr(output[0].get('predictions', []), 'tolist') else output[0].get('predictions', []),
                    'coordinates': output[0].get('coordinates', []).tolist() if hasattr(output[0].get('coordinates', []), 'tolist') else output[0].get('coordinates', []),
                    'probabilities': output[0].get('probabilities', []).tolist() if hasattr(output[0].get('probabilities', []), 'tolist') else output[0].get('probabilities', []),
                }
                json.dump(save_data, f)
            print(f"✓ Saved to: {output_file}")
        else:
            print("Warning: No output generated")

        return output

  
    except Exception as e:
        print(f"\nError during feature extraction: {e}")
        return None

def analyze_features(features_dir):
    """
    Analyze extracted features
    
    Args:
        features_dir: Directory containing features
    """
    print("\n" + "=" * 60)
    print("Feature Analysis")
    print("=" * 60)
    
    features_dir = Path(features_dir)  / "predictions"
    
    # Look for output files
    json_files = list(features_dir.glob("*.json"))
    
    if not json_files:
        print("No feature files found")
        return
    
    # Load first JSON file
    with open(json_files[0], 'r') as f:
        data = json.load(f)
    
    if 'predictions' in data:
        features = np.array(data['predictions'])
        coords = np.array(data.get('coordinates', []))
        
        print(f"\nNumber of patches: {len(features)}")
        if len(features) > 0:
            print(f"Feature dimension: {features[0] if isinstance(features[0], (int, float)) else 'N/A'}")
        print(f"Coordinate shape: {coords.shape if len(coords) > 0 else 'N/A'}")

def visualize_patch_distribution(output_dir, wsi_path):
    """
    Visualize spatial distribution of extracted patches
    
    Args:
        output_dir: Directory with results
        wsi_path: Original WSI path
    """
    output_dir = Path(output_dir)
    
    print("\n" + "=" * 60)
    print("Patch Distribution Visualization")
    print("=" * 60)
    
    # Load coordinates from JSON
    json_files = list((output_dir/"predictions").glob("*.json"))
    if not json_files:
        print("No results found for visualization")
        return
    
    with open(json_files[0], 'r') as f:
        data = json.load(f)
    
    if 'coordinates' not in data:
        print("No coordinate information found")
        return
    
    coords = np.array(data['coordinates'])
    
    # Plot patch locations
    fig, ax = plt.subplots(figsize=(10, 8))
    
    ax.scatter(coords[:, 0], coords[:, 1], alpha=0.5, s=10)
    ax.set_xlabel('X coordinate', fontsize=12)
    ax.set_ylabel('Y coordinate', fontsize=12)
    ax.set_title(f'Patch Distribution ({len(coords)} patches)', fontsize=14)
    ax.invert_yaxis()  # Image coordinates
    
    plt.tight_layout()
    plt.savefig(output_dir / "patch_distribution.png", dpi=150, bbox_inches='tight')
    print(f"✓ Saved: patch_distribution.png")

def main():
    # Default configuration
    wsi_filename = "CMU-1-Small-Region"
    
    # Allow command-line override
    if len(sys.argv) > 1:
        wsi_filename = sys.argv[1]
    
    wsi_path = f"/data/{wsi_filename}.svs"
    output_dir = f"/results/{wsi_filename}"
    
    # Extract features
    features = extract_patch_features(
        wsi_path,
        output_dir,
        resolution=0.5,
        patch_size=224
    )
    
    if features is not None:
        # Analyze features
        analyze_features(output_dir)
        
        # Visualize patch distribution
        visualize_patch_distribution(output_dir, wsi_path)
    
    print("\n" + "=" * 60)
    print("Feature extraction complete!")
    print(f"Results: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()

