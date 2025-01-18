import os
import csv
import subprocess
from datetime import datetime

from common_paths import get_toolkit_dirs

current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")

def run_command(command, success_message):
    """
    Runs the provided command list with subprocess.run().
    Prints success_message if it completes, or an error if it fails.
    """
    try:
        subprocess.run(command, check=True)
        print(success_message)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}: {e.stderr}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def hayabusa_logons():
    """
    Calls the 'hayabusa' executable to produce a CSV and HTML timeline in _output,
    using _input as the source directory.
    """
    dirs = get_toolkit_dirs()
    hayabusa_executable = os.path.join(dirs['base_dir'], "bin", "hayabusa", "hayabusa")
    
    input_dir = dirs['input_dir']
    output_csv = os.path.join(dirs['output_dir'], f"{current_datetime}_hayabusa_timeline.csv")
    output_html = os.path.join(dirs['output_dir'], f"{current_datetime}_hayabusa_timeline.html")

    command = [
        hayabusa_executable,
        "csv-timeline",
        "-d", input_dir,
        "-o", output_csv,
        "-H", output_html
    ]

    run_command(command, "Command executed successfully.")

if __name__ == "__main__":
    hayabusa_logons()
