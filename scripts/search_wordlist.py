import os
import csv
from datetime import datetime

from common_paths import get_toolkit_dirs

def freetext(file_path, search_queries, output_csv=None):
    """
    Performs a wordlist-based search on the given file_path (file or directory).
    Logs matches to a CSV file if specified.
    """
    try:
        if output_csv:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['search_query', 'source_file', 'source_row_number', 'source_data'])

        # Search all files
        if os.path.isdir(file_path):
            for root, _, files in os.walk(file_path):
                for file_name in files:
                    file_to_search = os.path.join(root, file_name)
                    print(f"Processing file: {file_to_search}")
                    for search_query in search_queries:
                        search_in_single_file(file_to_search, search_query, output_csv)
        elif os.path.isfile(file_path):
            print(f"Processing file: {file_path}")
            for search_query in search_queries:
                search_in_single_file(file_path, search_query, output_csv)
        else:
            print("Invalid path provided.")
    except Exception as e:
        print(f"An error occurred: {e}")

def search_in_single_file(file_path, search_query, output_csv=None):
    """
    Searches for `search_query` in a single file.  
    Appends matches to CSV if specified.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                if search_query.lower() in line.lower():
                    if output_csv:
                        with open(output_csv, 'a', newline='', encoding='utf-8') as csv_file:
                            csv_writer = csv.writer(csv_file)
                            csv_writer.writerow([search_query, file_path, line_number, line.strip()])
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    # Default paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']
    base_dir = dirs['base_dir']

    # Wordlist path
    input_wordlist_file = os.path.join(base_dir, "input_wordlist.txt")

    # Load wordlist
    try:
        with open(input_wordlist_file, 'r', encoding='utf-8') as f:
            search_queries = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Wordlist file not found: {input_wordlist_file}")
        exit(1)

    # Build CSV
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    default_output_csv = os.path.join(default_output_directory, f"{current_datetime}_wordlist.csv")

    # Run search
    freetext(default_input_directory, search_queries, default_output_csv)
