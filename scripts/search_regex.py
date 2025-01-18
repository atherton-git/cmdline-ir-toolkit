import os
import csv
from datetime import datetime
import re

from common_paths import get_toolkit_dirs

def freetext(file_path, regex_patterns, output_csv=None):
    """
    Performs a regex-based search on the given file path (which can be a file or directory).
    Logs matching lines to a CSV file (if specified), and prints which file is being processed.
    """
    try:
        if output_csv:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([
                    'regex_pattern', 'pattern_description',
                    'source_file', 'source_row_number', 'source_data'
                ])

        if os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file_name in files:
                    file_to_search = os.path.join(root, file_name)
                    print(f"Processing file: {file_to_search}")
                    for pattern, description in regex_patterns.items():
                        search_in_single_file(
                            file_to_search, pattern, description, output_csv
                        )
        elif os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            for pattern, description in regex_patterns.items():
                search_in_single_file(file_path, pattern, description, output_csv)
        else:
            print("Invalid path provided.")
    except Exception as e:
        print(f"An error occurred: {e}")

def search_in_single_file(file_path, regex_pattern, pattern_description, output_csv=None):
    """
    Searches for a given regex_pattern in a single file. Appends the match info to a CSV if specified.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                if re.search(regex_pattern, line):
                    if output_csv:
                        with open(output_csv, 'a', newline='', encoding='utf-8') as csv_file:
                            csv_writer = csv.writer(csv_file)
                            csv_writer.writerow([
                                regex_pattern, pattern_description,
                                file_path, line_number, line.strip()
                            ])
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    # Predefined paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']
    base_dir = dirs['base_dir']

    input_regex_file = os.path.join(base_dir, "input_regex.txt")
    default_output_csv_path = os.path.join(
        default_output_directory, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_regex.csv"
    )

    # Load regex patterns from input_regex.txt
    try:
        with open(input_regex_file, 'r', encoding='utf-8') as f:
            regex_patterns = {
                line.split('#', 1)[0].strip(): line.split('#', 1)[1].strip()
                for line in f if line.strip() and not line.startswith('#')
            }
    except FileNotFoundError:
        print(f"Regex file not found: {input_regex_file}")
        exit(1)

    # Predefined paths
    output_csv = default_output_csv_path
    freetext(default_input_directory, regex_patterns, output_csv)
