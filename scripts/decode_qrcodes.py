import os
import re
import numpy as np
import pyboof as pb
from common_paths import get_toolkit_dirs

# Function to replace 't' with 'x' only in the matched part of the URL
def sanitize_url(match):
    return match.group().replace('t', 'x')

# Function to process a single image and detect QR codes
def process_image(image_path):
    detector = pb.FactoryFiducial(np.uint8).qrcode()
    image = pb.load_single_band(image_path, np.uint8)
    detector.detect(image)

    print(f"Detected a total of {len(detector.detections)} QR Codes in {image_path}:")

    url_pattern = re.compile(r'https?://[^\s]+')

    for qr in detector.detections:
        sanitized_message = url_pattern.sub(sanitize_url, qr.message)
        print(sanitized_message)
        # If you'd like bounding coordinates, uncomment:
        # print("     at: " + str(qr.bounds))

if __name__ == "__main__":
    # Use common_paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']

    # List of allowed file extensions
    allowed_extensions = [".png", ".jpg", ".jpeg"]  # Add more if needed

    print(f"Searching for QR code images in '{default_input_directory}'...")

    # Iterate through the input directory
    for root, _, files in os.walk(default_input_directory):
        for filename in files:
            if any(filename.lower().endswith(ext) for ext in allowed_extensions):
                image_path = os.path.join(root, filename)
                process_image(image_path)
