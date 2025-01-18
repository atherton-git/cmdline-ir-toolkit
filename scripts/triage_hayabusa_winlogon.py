import os
import csv
import subprocess
from datetime import datetime

from common_paths import get_toolkit_dirs

current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")

def run_command(command, success_message):
    try:
        subprocess.run(command, check=True)
        print(success_message)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}: {e.stderr}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def hayabusa_logons():
    """
    Calls the 'hayabusa' binary to produce a WinLogon summary CSV.
    Uses _input for input data, writes CSV to _output.
    """
    dirs = get_toolkit_dirs()
    hayabusa_executable = os.path.join(dirs['base_dir'], "bin", "hayabusa", "hayabusa")

    input_dir = dirs['input_dir']
    output_csv = os.path.join(dirs['output_dir'], f"{current_datetime}_hayabusa_winlogon.csv")

    command = [
        hayabusa_executable,
        "logon-summary",
        "-d", input_dir,
        "-o", output_csv
    ]

    run_command(command, "Command executed successfully.")

if __name__ == "__main__":
    hayabusa_logons()
