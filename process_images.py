import os
import subprocess

assets_dir = "public/assets"
for filename in os.listdir(assets_dir):
    if filename.endswith(".png") and not filename.endswith("-nobg.png"):
        filepath = os.path.join(assets_dir, filename)
        outpath = os.path.join(assets_dir, filename.replace(".png", "-nobg.png"))
        print(f"Processing {filepath} -> {outpath}")
        try:
            subprocess.run(["rembg", "i", filepath, outpath], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing {filepath}: {e}")

