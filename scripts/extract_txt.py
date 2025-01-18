import os
from tika import parser
from common_paths import get_toolkit_dirs

def extract_text_with_tika(input_file, output_directory):
    # Parse file using Tika
    try:
        parsed = parser.from_file(input_file)
        content = parsed.get("content", "")
    except Exception as e:
        print("Error:", e)
        return False

    # Generate output filename
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    file_extension = os.path.splitext(input_file)[1][1:]  # Get file extension
    output_filename = f"{base_filename}_{file_extension}.txt"
    output_path = os.path.join(output_directory, output_filename)

    # Write to output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print("Error:", e)
        return False

    print("Text extracted successfully and saved to", output_path)
    
    # Remove original file
    os.remove(input_file)
    print("Original file removed:", input_file)
    
    return True

def process_files(input_directory, output_directory):
    # Create output directory
    os.makedirs(output_directory, exist_ok=True)

    # Iterate over files in input
    for filename in os.listdir(input_directory):
        input_file = os.path.join(input_directory, filename)
        if filename.endswith((".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".eml", ".msg")):
            extract_text_with_tika(input_file, output_directory)
        else:
            print("Skipping file:", input_file)

if __name__ == '__main__':
    # Common_paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']
    
    process_files(default_input_directory, default_output_directory)
