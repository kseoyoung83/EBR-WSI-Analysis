import openslide
from pathlib import Path
from PIL import Image
import numpy as np


class WSIPatchExtractor:
    def __init__(self, wsi_path):
        self.wsi_path = wsi_path
        self.slide = openslide.OpenSlide(wsi_path)

    def _calculate_tissue_ratio(self, patch, brightness_threshold=200):
        """Calculate tissue ratio in a patch."""
        gray = patch.convert('L')
        gray_array = np.array(gray)

        tissue_pixels = np.sum(gray_array < brightness_threshold)
        total_pixels = gray_array.size

        tissue_ratio = tissue_pixels / total_pixels
        return tissue_ratio

    def extract_patches_grid(self, patch_size=256, overlap=0, level=0, tissue_threshold=0.3):
        # Create output directories
        all_patches_dir = Path("results/patches/all")
        tissue_patches_dir = Path("results/patches/tissue_only")
        all_patches_dir.mkdir(parents=True, exist_ok=True)
        tissue_patches_dir.mkdir(parents=True, exist_ok=True)

        level_dims = self.slide.level_dimensions[level]
        width, height = level_dims

        step = patch_size - overlap

        all_patches = []
        tissue_patches = []
        skipped_count = 0

        for y in range(0, height - patch_size + 1, step):
            for x in range(0, width - patch_size + 1, step):
                patch = self.slide.read_region(
                    (x, y), level, (patch_size, patch_size)
                )

                patch = patch.convert("RGB")

                # Calculate tissue ratio
                tissue_ratio = self._calculate_tissue_ratio(patch)

                filename = f"patch_x{x}_y{y}.png"

                # Save to all patches folder
                all_filepath = all_patches_dir / filename
                patch.save(all_filepath)

                all_patches.append({
                    'x': x,
                    'y': y,
                    'filename': filename,
                    'filepath': str(all_filepath),
                    'tissue_ratio': tissue_ratio
                })

                # Save to tissue-only folder if threshold is met
                if tissue_ratio >= tissue_threshold:
                    tissue_filepath = tissue_patches_dir / filename
                    patch.save(tissue_filepath)

                    tissue_patches.append({
                        'x': x,
                        'y': y,
                        'filename': filename,
                        'filepath': str(tissue_filepath),
                        'tissue_ratio': tissue_ratio
                    })
                else:
                    skipped_count += 1

        print(f"Total patches extracted: {len(all_patches)}")
        print(f"Tissue patches saved: {len(tissue_patches)}")
        print(f"Background patches skipped: {skipped_count}")
        print(f"All patches saved to: {all_patches_dir}")
        print(f"Tissue-only patches saved to: {tissue_patches_dir}")

        return {
            'all_patches': all_patches,
            'tissue_patches': tissue_patches,
            'skipped_count': skipped_count
        }

    def close(self):
        self.slide.close()


def main():
    wsi_path = "data/CMU-1-Small-Region.svs"

    extractor = WSIPatchExtractor(wsi_path)
    result = extractor.extract_patches_grid(patch_size=256, overlap=0, level=0, tissue_threshold=0.3)
    extractor.close()


if __name__ == "__main__":
    main()
