import os
import csv
from datetime import datetime

# Import from common_paths.py
from common_paths import get_toolkit_dirs

def freetext(file_path, search_query, output_csv=None):
    """
    Performs a free-text search on the given file path (which can be a file or directory).
    Optionally writes matching lines to a CSV file.
    """
    try:
        # Create CSV with header
        if output_csv:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['source_file', 'source_row_number', 'source_data'])

        # Recursively search in files
        if os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file_name in files:
                    file_to_search = os.path.join(root, file_name)
                    print(f"Processing file: {file_to_search}")
                    search_in_single_file(file_to_search, search_query, output_csv)
        elif os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            search_in_single_file(file_path, search_query, output_csv)
        else:
            print("Invalid path provided.")
    except Exception as e:
        print(f"An error occurred: {e}")

def search_in_single_file(file_path, search_query, output_csv=None):
    """
    Searches for the given query string in a single file.
    If output_csv is specified, appends matching lines to that CSV file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                if search_query.lower() in line.lower():
                    if output_csv:
                        with open(output_csv, 'a', newline='', encoding='utf-8') as csv_file:
                            csv_writer = csv.writer(csv_file)
                            csv_writer.writerow([file_path, line_number, line.strip()])
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    # Default paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']

    # Predefined inputs
    _input = default_input_directory

    # Prompt user for search query
    _search_query = input('Please enter the search query: ')

    # Output CSV
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    proposed_csv_name = f"{current_datetime}_freetext.csv"
    proposed_csv_path = os.path.join(default_output_directory, proposed_csv_name)

    _output_csv = proposed_csv_path
    freetext(_input, _search_query, _output_csv if _output_csv else None)
