import os
import csv
import re
from datetime import datetime
from ipaddress import ip_address

from common_paths import get_toolkit_dirs

def ipv4_search(file_path, output_csv=None, include_private=True):
    """
    Searches for IPv4 addresses within a file. Optionally writes matches to a CSV file if output_csv is specified.
    """
    try:
        if output_csv:
            mode = 'a' if os.path.exists(output_csv) else 'w'
            with open(output_csv, mode, newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                if mode == 'w':
                    csv_writer.writerow(['source_file', 'source_row_number', 'matched_ipv4', 'source_data'])

        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                # Regex for IPv4
                ipv4_addresses = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
                for ipv4_address in ipv4_addresses:
                    ip = ip_address(ipv4_address)
                    # Process if private addresses are included
                    if include_private or not ip.is_private:
                        # Write match to CSV if enabled
                        if output_csv:
                            with open(output_csv, 'a', newline='', encoding='utf-8') as csv_file:
                                csv_writer = csv.writer(csv_file)
                                csv_writer.writerow([file_path, line_number, ipv4_address, line.strip()])
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

if __name__ == "__main__":
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']

    # Prompt user for RFC1918 inclusion
    while True:
        include_private_input = input("Include private IPv4 addresses (RFC1918)? (Y/N): ").strip().lower()
        if include_private_input in {'y', 'n'}:
            include_private = include_private_input == 'y'
            break
        else:
            print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

    # Default CSV filename
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    default_output_csv = os.path.join(default_output_directory, f"{current_datetime}_ipv4_addresses.csv")

    path = default_input_directory
    output_csv = default_output_csv

    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file_name in files:
                file_to_search = os.path.join(root, file_name)
                print(f"Processing file: {file_to_search}")
                ipv4_search(file_to_search, output_csv, include_private)
    elif os.path.isfile(path):
        print(f"Processing file: {path}")
        ipv4_search(path, output_csv, include_private)
    else:
        print("Invalid path provided.")
