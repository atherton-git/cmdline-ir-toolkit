import os
import base64
from common_paths import get_toolkit_dirs

def encode_file_to_base64(file_path, output_directory):
    """Encodes a file to Base64 and saves the output."""
    try:
        # Open file and read
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Encode to b64
        base64_encoded = base64.b64encode(file_data).decode('utf-8')

        # Create the output file
        file_name = os.path.basename(file_path)
        output_file_path = os.path.join(output_directory, f"{file_name}.b64")

        # Save to the output file
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(base64_encoded)

        print(f"Encoded file saved as: {output_file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    # Default paths
    dirs = get_toolkit_dirs()
    input_path = dirs.get('input_dir', '_input')
    output_path = dirs.get('output_dir', '_output')

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Process files
    if os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file_name in files:
                file_to_encode = os.path.join(root, file_name)
                encode_file_to_base64(file_to_encode, output_path)
    elif os.path.isfile(input_path):
        encode_file_to_base64(input_path, output_path)
    else:
        print("Invalid path provided.")
