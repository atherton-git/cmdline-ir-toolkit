#!/usr/bin/env bash

# Exit immediately if a pipeline returns a non-zero status (set -e).
# 'u' treats unset variables as an error. 'o pipefail' ensures pipeline errors propagate.
set -Eeuo pipefail

###############################################################################
# Variables
###############################################################################

toolkit_dir="$(pwd)"
tmp_dir="${toolkit_dir}/tmp"

###############################################################################
# Pre-flight checks
###############################################################################

# Check if required commands are available
required_cmds=("curl" "sha256sum" "unzip" "pigz" "tar" "pip")
for cmd in "${required_cmds[@]}"; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: Required command '$cmd' not found in PATH. Aborting."
    exit 1
  fi
done

# Ensure tmp_dir exists
mkdir -p "$tmp_dir"

# Ensure our bin directories exist
mkdir -p "${toolkit_dir}/bin/hayabusa"
mkdir -p "${toolkit_dir}/bin/evtx_explorer"
mkdir -p "${toolkit_dir}/bin/dotnet-runtime-600"

###############################################################################
# Function to calculate hash and compare with expected
###############################################################################

check_hash() {
    local file_path="$1"
    local expected_hash="$2"

    if [[ ! -f "$file_path" ]]; then
        echo "WARNING: File not found: $file_path"
        return
    fi

    # Calculate the file's actual hash
    local actual_hash
    actual_hash=$(sha256sum "$file_path" | awk '{print $1}')

    # Compare
    if [[ "$actual_hash" != "$expected_hash" ]]; then
        echo "WARNING: File hash mismatch for $file_path"
        echo "Expected file hash: $expected_hash"
        echo "Actual file hash  : $actual_hash"
        read -rp "Do you want to proceed at your own risk? (y/n): " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            echo "Aborting setup."
            exit 1
        else
            echo "Proceeding despite hash mismatch..."
        fi
    else
        echo "File hash check passed for $file_path"
    fi
}

###############################################################################
# Prompt for Hayabusa installation
###############################################################################

read -rp "Do you want to include Hayabusa in the installation? This will take a few minutes. (y/n): " include_hayabusa
if [[ "$include_hayabusa" =~ ^[Yy]$ ]]; then
  echo "Installing Hayabusa..."

  # Download and extract Hayabusa binaries
  curl -fSL -o "${tmp_dir}/hayabusa.zip" \
    "https://github.com/Yamato-Security/hayabusa/releases/download/v2.16.0/hayabusa-2.16.0-all-platforms.zip"

  hayabusa_expected_hash="1b103677e90c3a049c31f8acb34cc097190e6dcaeb2eb26dbc557fa6ec455193"
  check_hash "${tmp_dir}/hayabusa.zip" "$hayabusa_expected_hash"

  unzip -q "${tmp_dir}/hayabusa.zip" -x "rules/*" -d "${tmp_dir}/hayabusa/"
  mv "${tmp_dir}/hayabusa/"* "${toolkit_dir}/bin/hayabusa/"
  mv "${toolkit_dir}/bin/hayabusa/hayabusa-2.16.0-lin-x64-gnu" "${toolkit_dir}/bin/hayabusa/hayabusa"
  mv "${toolkit_dir}/bin/hayabusa/hayabusa-2.16.0-win-x64.exe" "${toolkit_dir}/bin/hayabusa/hayabusa.exe"
  mkdir -p "${toolkit_dir}/bin/hayabusa/rules"
  rm -r "${tmp_dir}/hayabusa/"

  echo "Downloading and extracting Hayabusa rules. This will take a few minutes..."
  curl -fSL -o "${tmp_dir}/hayabusa-rules.tar.gz" \
    "https://github.com/Yamato-Security/hayabusa-rules/archive/refs/tags/v2.15.0.tar.gz"

  hayabusa_rules_expected_hash="c58d8a557931c9a8136ca581f54263ef4d3969b68816804dc3a1c0c53dc92cde"
  check_hash "${tmp_dir}/hayabusa-rules.tar.gz" "$hayabusa_rules_expected_hash"

  echo "Extracting Hayabusa rules. This will take a few minutes."
  pigz -dc "${tmp_dir}/hayabusa-rules.tar.gz" | \
      tar -C "${toolkit_dir}/bin/hayabusa/rules/" --strip-components=1 -xf -

  rm "${tmp_dir}/hayabusa-rules.tar.gz"
else
  echo "Skipping Hayabusa installation."
fi

###############################################################################
# EvtxECmd Installation
###############################################################################

echo "Installing EvtxECmd..."
curl -fSL -o "${tmp_dir}/EvtxECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/EvtxECmd.zip"

evtxecmd_expected_hash="452e7b5363c56fbe25a7656bfa8d81be136e0452b44a8b6e20be19c2e361c35b"
check_hash "${tmp_dir}/EvtxECmd.zip" "$evtxecmd_expected_hash"

unzip -q "${tmp_dir}/EvtxECmd.zip" -d "${tmp_dir}/EvtxECmd/"
mv "${tmp_dir}/EvtxECmd/EvtxECmd/"* "${toolkit_dir}/bin/evtx_explorer/"
rm -r "${tmp_dir}/EvtxECmd/"

###############################################################################
# SrumECmd Installation
###############################################################################

echo "Installing SrumECmd..."
curl -fSL -o "${tmp_dir}/SrumECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/SrumECmd.zip"

srumecmd_expected_hash="09762bdbd45ebaa4bd6e2cfa6dc8cdaea2092ee6b657420787098d8a6397e9c4"
check_hash "${tmp_dir}/SrumECmd.zip" "$srumecmd_expected_hash"

unzip -q "${tmp_dir}/SrumECmd.zip" -d "${tmp_dir}/SrumECmd/"
mv "${tmp_dir}/SrumECmd/"* "${toolkit_dir}/bin/srum_explorer/"
rm -r "${tmp_dir}/SrumECmd/"

###############################################################################
# .NET 6 runtime
###############################################################################

echo "Installing .NET 6 runtime..."
curl -fSL -o "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" \
  "https://download.visualstudio.microsoft.com/download/pr/0ce1c34f-0d9e-4d9b-964e-da676c8e605a/7a6c353b36477fa84f85b2821f2350c2/dotnet-runtime-6.0.0-linux-x64.tar.gz"

dotnet_expected_hash="1a4076139944f3b16d9a0fc4841190cf060a9d93ebc13330821a2e97f6d4db91"
check_hash "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" "$dotnet_expected_hash"

tar -xzf "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" -C "${toolkit_dir}/bin/dotnet-runtime-600/"

###############################################################################
# Python module installations from requirements.txt
###############################################################################

echo "Installing Python requirements..."
pip install --break-system-packages -r "${toolkit_dir}/requirements.txt"

###############################################################################
# Cleanup and exit
###############################################################################

echo "Removing unwanted files..."
files_to_remove=(
  ".gitkeep"
  "risk_assessment.docx"
  "README.md"
  "initialise.ps1"
)

for pattern in "${files_to_remove[@]}"; do
  find "${toolkit_dir}" -maxdepth 2 -type f -name "${pattern}" -exec rm -f {} +
done
echo "Setup has completed."
