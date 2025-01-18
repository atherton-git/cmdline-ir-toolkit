import os
import base64
from common_paths import get_toolkit_dirs

def decode_base64_to_file(encoded_file_path, output_directory):
    """Decodes a Base64 encoded file and saves it to the output directory."""
    try:
        # Read b64 file
        with open(encoded_file_path, 'r', encoding='utf-8') as file:
            base64_encoded_data = file.read()

        # Decode b64 data
        file_data = base64.b64decode(base64_encoded_data)

        # Create the output file path
        file_name = os.path.basename(encoded_file_path)
        original_file_name = file_name.rsplit('.', 1)[0]
        output_file_path = os.path.join(output_directory, original_file_name)

        # Write to output file
        with open(output_file_path, 'wb') as output_file:
            output_file.write(file_data)

        print(f"Decoded file saved as: {output_file_path}")
    except Exception as e:
        print(f"An error occurred while processing {encoded_file_path}: {e}")

if __name__ == "__main__":
    # Default paths
    dirs = get_toolkit_dirs()
    input_path = dirs.get('input_dir', '_input')
    output_path = dirs.get('output_dir', '_output')

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    if os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file_name in files:
                if file_name.endswith('.b64'):  # Process only .b64 files
                    encoded_file_path = os.path.join(root, file_name)
                    decode_base64_to_file(encoded_file_path, output_path)
    elif os.path.isfile(input_path):
        if input_path.endswith('.b64'):
            decode_base64_to_file(input_path, output_path)
        else:
            print("The specified file is not a .b64 file.")
    else:
        print("Invalid path provided.")
