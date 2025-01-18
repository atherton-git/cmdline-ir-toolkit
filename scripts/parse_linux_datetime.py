"""
Note: EXPERIMENTAL: Parses linux logs for timestamps and prints the matching lines to csv output.
"""

import os
import re
import pandas as pd
from datetime import datetime
from common_paths import get_toolkit_dirs

def process_log_entry(timestamp_string, line, line_number, current_year, relative_path, channel):
    if line.strip() not in processed_payloads:
        timestamp = None
        formats_to_try = [
            ('%Y %b %d %H:%M:%S', f"{current_year} {timestamp_string}"),
            ('%Y %b %d %H:%M:%S.%f', f"{current_year} {timestamp_string}"),
            ('%Y-%m-%d %H:%M:%S', timestamp_string),
            ('%d/%b/%Y:%H:%M:%S', timestamp_string)
        ]

        for format_str, formatted_ts_str in formats_to_try:
            try:
                timestamp = datetime.strptime(formatted_ts_str, format_str)
                break
            except ValueError:
                pass

        if timestamp:
            timestamps.append({
                'Time Generated': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Filename': relative_path,
                'Line': line_number,
                'Channel': channel,
                'Payload': line.strip()
            })
            processed_payloads.add(line.strip())
            print(f"Processed timestamp {timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
                  f"in file {relative_path} (Line {line_number})")

if __name__ == "__main__":
    # Common_paths
    dirs = get_toolkit_dirs()
    default_input_directory = dirs['input_dir']
    default_output_directory = dirs['output_dir']

    # Output_file variable
    output_filename = datetime.now().strftime("%Y%m%d%H%M%S_linux-log-datetime.csv")
    output_file = os.path.join(default_output_directory, output_filename)

    current_year = datetime.now().year
    timestamps = []
    processed_payloads = set()

    patterns = [
        r'(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})',
        r'(\w{3} \d{1,2} \d{2}:\d{2}:\d{2}\.\d{6})',
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'
    ]

    print(f"Searching for log files in {default_input_directory} (and subdirectories)...")

    for root, _, files in os.walk(default_input_directory):
        for file in files:
            current_file = os.path.join(root, file)
            relative_path = os.path.relpath(current_file, default_input_directory)
            channel = os.path.splitext(file)[0].split('.')[0]

            try:
                with open(current_file, 'r', encoding='unicode_escape') as reader:
                    line_number = 1
                    for line in reader:
                        for pattern in patterns:
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                timestamp_string = match.group(1)
                                process_log_entry(
                                    timestamp_string, line, line_number,
                                    current_year, relative_path, channel
                                )
                        line_number += 1
            except Exception as e:
                print(f"Error processing file {relative_path}: {str(e)}")

    df = pd.DataFrame(timestamps)
    df.to_csv(output_file, index=False)
    print(f"Processing completed. Total timestamps processed: {len(timestamps)}")
