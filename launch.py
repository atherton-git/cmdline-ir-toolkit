#!/usr/bin/env python3
import os
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))

########################################
# HELPER: run_command()
########################################

def run_command(command, success_message):
    """
    Wrapper around subprocess.run() to execute a given command list.
    If check=True raises CalledProcessError, we print an error. 
    Otherwise, print success_message on success.
    """
    try:
        subprocess.run(command, check=True)
        print(success_message)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}: {e.stderr}")
    except Exception as ex:
        print(f"An error occurred: {str(ex)}")

########################################
# MENU SCRIPTS
########################################

def parse_kstrike():
    """
    Calls parse_kstrike.py in scripts/ to parse .mdb files from _input -> _output.
    """
    script_path = os.path.join('scripts', 'parse_kstrike.py')
    subprocess.run(["python", script_path])
    print("KStrike parsing completed. Check _output for results.")

def decode_base64_files():
    """
    Calls decode_base64.py in scripts/ to decode .b64 files.
    """
    script_path = os.path.join('scripts', 'decode_base64.py')
    subprocess.run(["python", script_path])

def encode_base64_files():
    """
    Calls encode_base64_file.py in scripts/ to encode files to Base64.
    """
    script_path = os.path.join('scripts', 'encode_base64_file.py')
    subprocess.run(["python", script_path])

def decode_qr_codes():
    """
    Calls decode_qrcodes.py in scripts/ to detect QR codes in images.
    """
    script_path = os.path.join('scripts', 'decode_qrcodes.py')
    subprocess.run(["python", script_path])

def extract_text_files():
    """
    Calls extract_txt.py in scripts/ to extract text from docs/pdfs/etc. using Apache Tika.
    """
    script_path = os.path.join('scripts', 'extract_txt.py')
    subprocess.run(["python", script_path])

def parse_linux_datatimes():
    """
    Calls parse_linux_datatime.py in scripts/ to parse Linux logs for timestamps.
    """
    script_path = os.path.join('scripts', 'parse_linux_datatime.py')
    subprocess.run(["python", script_path])

def search_freesearch():
    """
    Calls search_freesearch.py in scripts/ for free-text searching in cleartext files.
    """
    script_path = os.path.join('scripts', 'search_freesearch.py')
    subprocess.run(["python", script_path])

def search_ipv4():
    """
    Calls search_ipv4.py in scripts/ to search cleartext files for IPv4 addresses.
    """
    script_path = os.path.join('scripts', 'search_ipv4.py')
    subprocess.run(["python", script_path])

def search_regex():
    """
    Calls search_regex.py in scripts/ to search cleartext files 
    using patterns from input_regex.txt.
    """
    script_path = os.path.join('scripts', 'search_regex.py')
    subprocess.run(["python", script_path])

def search_wordlist():
    """
    Calls search_wordlist.py in scripts/ to search cleartext files 
    using terms from input_wordlist.txt.
    """
    script_path = os.path.join('scripts', 'search_wordlist.py')
    subprocess.run(["python", script_path])

def triage_hayabusa_timeline():
    """
    Calls triage_hayabusa_timeline.py in scripts/ to run 'hayabusa csv-timeline'.
    """
    script_path = os.path.join('scripts', 'triage_hayabusa_timeline.py')
    subprocess.run(["python", script_path])

def triage_hayabusa_winlogon():
    """
    Calls triage_hayabusa_winlogon.py in scripts/ to run 'hayabusa logon-summary'.
    """
    script_path = os.path.join('scripts', 'triage_hayabusa_winlogon.py')
    subprocess.run(["python", script_path])

########################################
# EVTX FUNCTION: parse_evtx_files()
########################################

def parse_evtx_files():
    """
    Runs the EvtxExplorer (EvtxECmd.dll) tool (under bin/dotnet-runtime-600/dotnet, etc.)
    to parse all .evtx logs from _input into CSV in _output.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(script_dir, "bin")
    dotnet_dir = os.path.join(bin_dir, "dotnet-runtime-600", "dotnet")
    evtx_dir = os.path.join(bin_dir, "evtx_explorer", "EvtxECmd.dll")
    input_dir = os.path.join(script_dir, "_input")
    output_dir = os.path.join(script_dir, "_output")
    command = [
        dotnet_dir,
        evtx_dir,
        "-d", input_dir,
        "--csv", output_dir
    ]

    run_command(command, "EVTX files processed successfully, check _output for CSV results.")

########################################
# EVTX FUNCTION: parse_srum_files()
########################################

def parse_srum_files():
    """
    Runs the Srum (SrumECmd.dll) tool (under bin/dotnet-runtime-600/dotnet, etc.)
    to parse SRUB.dat files from _input into CSV in _output.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(script_dir, "bin")
    dotnet_dir = os.path.join(bin_dir, "dotnet-runtime-600", "dotnet")
    srum_dir = os.path.join(bin_dir, "srum_explorer", "SrumECmd.dll")
    input_dir = os.path.join(script_dir, "_input")
    output_dir = os.path.join(script_dir, "_output")
    command = [
        dotnet_dir,
        srum_dir,
        "-d", input_dir,
        "--csv", output_dir
    ]

    run_command(command, "EVTX files processed successfully, check _output for CSV results.")


########################################
# MAIN MENU
########################################

def main():
    print(r"""
                      _____                  _            __              ____   _ __ 
  _________ ___  ____/ / (_)___  ___        (_)____      / /_____  ____  / / /__(_) /_
 / ___/ __ `__ \/ __  / / / __ \/ _ \______/ / ___/_____/ __/ __ \/ __ \/ / //_/ / __/
/ /__/ / / / / / /_/ / / / / / /  __/_____/ / /  /_____/ /_/ /_/ / /_/ / / ,< / / /_  
\___/_/ /_/ /_/\__,_/_/_/_/ /_/\___/     /_/_/         \__/\____/\____/_/_/|_/_/\__/  

Note: Input files (.evtx, .log, .mdb, etc) need to be placed within the _input dir                                                                                      
""")
    while True:
        print("\nMENU OPTIONS:")
        # Quit
        print(" 1) Quit")

        # Convert
        print(" 2) Convert	| Documents to txt (Apache Tika)")

        # Decode
        print(" 3) Decode	| Base64 to files")
        print(" 4) Decode	| QR codes (Linux only)")

        # Encode
        print(" 5) Encode	| Files to Base64")

        # Parse
        print(" 6) Parse	| EVTX files (EvtxECmd)")
        print(" 7) Parse	| User Access Logging (KStrike)")
        print(" 8) Parse	| Linux datetimes in logs")
        print(" 9) Parse	| Srum files (SrumECmd)")

        # Search
        print("10) Search	| Free-text")
        print("11) Search	| IPv4")
        print("12) Search	| Regex (input_regex.txt)")
        print("13) Search	| Wordlist (input_wordlist.txt)")

        # Triage
        print("14) Triage	| EVTX (Hayabusa timeline)")
        print("15) Triage	| EVTX (Hayabusa logon summary)")

        choice = input("\nEnter your choice: ").strip()

        if choice == '1':
            break

        elif choice == '2':
            extract_text_files()

        elif choice == '3':
            decode_base64_files()

        elif choice == '4':
            decode_qr_codes()

        elif choice == '5':
            encode_base64_files()

        elif choice == '6':
            parse_evtx_files()

        elif choice == '7':
            parse_kstrike()

        elif choice == '8':
            parse_linux_datatimes()

        elif choice == '9':
            parse_srum_files()

        elif choice == '10':
            search_freesearch()

        elif choice == '11':
            search_ipv4()

        elif choice == '12':
            search_regex()

        elif choice == '13':
            search_wordlist()

        elif choice == '14':
            triage_hayabusa_timeline()

        elif choice == '15':
            triage_hayabusa_winlogon()

        else:
            print("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    main()
