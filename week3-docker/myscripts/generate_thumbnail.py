#!/usr/bin/env python3
"""
Generate thumbnail image from WSI file using TIAToolbox
"""

import os
from PIL import Image
from tiatoolbox.wsicore.wsireader import WSIReader

def generate_thumbnail(input_path, output_dir, resolution=1.25, units="power"):
    """
    Generate thumbnail from WSI file and save to output directory
    
    Args:
        input_path (str): Path to input WSI file
        output_dir (str): Directory to save thumbnail
        resolution (float): Resolution for thumbnail (default: 1.25)
        units (str): Units for resolution (default: "power")
    """
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist!")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Open WSI file
        print(f"Opening WSI file: {input_path}")
        reader = WSIReader.open(input_path)
        
        # Generate thumbnail
        thumbnail = reader.slide_thumbnail(resolution=resolution, units=units)
        
        # Save thumbnail
        filename = os.path.basename(input_path).replace('.svs', '_thumbnail.png')
        output_path = os.path.join(output_dir, filename)
        Image.fromarray(thumbnail).save(output_path)
        
        print(f"Success! Thumbnail saved to: {output_path}")
        print(f"Thumbnail size: {thumbnail.shape}")
        
        return True
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    input_path = "/data/CMU-1-Small-Region.svs"
    output_dir = "/results"
    
    generate_thumbnail(input_path, output_dir)