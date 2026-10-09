import os
import shutil
import subprocess

# Define the mapping from original paths to flattened paths
# Based on what was referenced in page.tsx
mapping = {
    'sensai-mascot.png': 'Landing Page/sensai-mascot.png',
    'hero-composite.png': 'Landing Page/hero-composite.png',
    'icon-child.png': 'Landing Page/icon-child bg.png',
    'icon-hand.png': 'Landing Page/icon-hand bg.png',
    'icon-trend.png': 'Landing Page/icon-trend bg.png',
    'process-flow.png': 'Landing Page/process-flow-bg.png',
    'tech-feature.png': 'Landing Page/technologies/detection.png',  # Guessed mapping
    'votre-mouvement-features.png': 'Landing Page/mouvement-features-setup.png',
    'pour-les-enfants-cards.png': 'Landing Page/kids/pour-les-enfants-cards.png',
    'kids-illustration.png': 'Landing Page/kids-illustrationpic.png',
    'therapist-mockup.png': 'Landing Page/therapist-mockup.png',
    'pour-les-therapeutes-features.png': 'Landing Page/therapist/pour-les-therapeutes-features.png',
    'pourquoi-sensai-cards.png': 'Landing Page/pourquoi/pourquoi-sensai-cards.png',
    'hardware-setup.png': 'Landing Page/hardware-setup.png',
    'vision-photo.png': 'Landing Page/vision-photo.png',
    'wave-divider.png': 'Landing Page/wave-divider.png',
    'logo-white.png': 'Landing Page/logo-white.png',
    'footer-socials.png': 'Landing Page/footer-socials.png'
}

base_src = "public/Assets"
base_dest = "public/assets_flat"

if not os.path.exists(base_dest):
    os.makedirs(base_dest)

for flat_name, orig_subpath in mapping.items():
    orig_path = os.path.join(base_src, orig_subpath)
    if not os.path.exists(orig_path):
        print(f"Missing: {orig_path}")
        continue
    
    dest_path = os.path.join(base_dest, flat_name)
    # Copy original
    shutil.copy(orig_path, dest_path)
    
    # Run rembg to generate -nobg.png
    dest_nobg = os.path.join(base_dest, flat_name.replace('.png', '-nobg.png'))
    print(f"Removing background for {flat_name}...")
    try:
        subprocess.run(["rembg", "i", dest_path, dest_nobg], check=True, capture_output=True)
    except Exception as e:
        print(f"Failed to process {flat_name}: {e}")

