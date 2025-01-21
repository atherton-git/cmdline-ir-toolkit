#!/usr/bin/env bash

# Exit immediately if a pipeline returns a non-zero status.
# '-u' treats unset variables as an error.
# 'pipefail' ensures pipeline errors propagate.
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
required_cmds=("curl" "sha256sum" "unzip" "pigz" "tar")
for cmd in "${required_cmds[@]}"; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: Required command '$cmd' not found in PATH. Aborting."
    exit 1
  fi
done

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
    actual_hash="$(sha256sum "$file_path" | awk '{print $1}')"

    # Compare
    if [[ "${actual_hash,,}" != "${expected_hash,,}" ]]; then
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
# Install Hayabusa
###############################################################################

hayabusa_ver="3.0.1"

read -rp "Do you want to include Hayabusa in the installation? This will take a few minutes. (y/n): " include_hayabusa
if [[ "$include_hayabusa" =~ ^[Yy]$ ]]; then
  echo "Installing Hayabusa..."

  # Download and extract Hayabusa binaries
  curl -fSL -o "${tmp_dir}/hayabusa.zip" \
    "https://github.com/Yamato-Security/hayabusa/releases/download/v${hayabusa_ver}/hayabusa-${hayabusa_ver}-all-platforms.zip"

  hayabusa_expected_hash="1b103677e90c3a049c31f8acb34cc097190e6dcaeb2eb26dbc557fa6ec455193"
  check_hash "${tmp_dir}/hayabusa.zip" "$hayabusa_expected_hash"

  unzip -q "${tmp_dir}/hayabusa.zip" -x "rules/*" -d "${tmp_dir}/hayabusa/"
  mv "${tmp_dir}/hayabusa/"* "${toolkit_dir}/bin/hayabusa/"
  mv "${toolkit_dir}/bin/hayabusa/hayabusa-${hayabusa_ver}-lin-x64-gnu" "${toolkit_dir}/bin/hayabusa/hayabusa"
  mv "${toolkit_dir}/bin/hayabusa/hayabusa-${hayabusa_ver}-win-x64.exe" "${toolkit_dir}/bin/hayabusa/hayabusa.exe"
  mkdir -p "${toolkit_dir}/bin/hayabusa/rules"
  rm -r "${tmp_dir}/hayabusa/"

  echo "Downloading and extracting Hayabusa rules. This will take a few minutes..."
  curl -fSL -o "${tmp_dir}/hayabusa-rules.tar.gz" \
    "https://github.com/Yamato-Security/hayabusa-rules/archive/refs/tags/v${hayabusa_ver}.tar.gz"

  hayabusa_rules_expected_hash="c58d8a557931c9a8136ca581f54263ef4d3969b68816804dc3a1c0c53dc92cde"
  check_hash "${tmp_dir}/hayabusa-rules.tar.gz" "$hayabusa_rules_expected_hash"

  echo "Extracting Hayabusa rules. This will take a few minutes."
  pigz -dc "${tmp_dir}/hayabusa-rules.tar.gz" | \
      tar -C "${toolkit_dir}/bin/hayabusa/rules/" --strip-components=1 -xf -

  rm "${tmp_dir}/hayabusa-rules.tar.gz"
  rm "${tmp_dir}/hayabusa.zip"
else
  echo "Skipping Hayabusa installation."
fi

###############################################################################
# Install AmCacheParser
###############################################################################

echo "Installing AmCacheParser..."
curl -fSL -o "${tmp_dir}/AmCacheParser.zip" \
  "https://download.ericzimmermanstools.com/net6/AmCacheParser.zip"

amcachep_expected_hash="0e0214d3b8d17500946e445f3dec92f9485d00f788316eaa5ca78ebb31c92d78"
check_hash "${tmp_dir}/AmCacheParser.zip" "$amcachep_expected_hash"

unzip -q ${tmp_dir}/AmCacheParser.zip -d ${tmp_dir}/AmCacheParser/
mv ${tmp_dir}/AmCacheParser/* ${toolkit_dir}/bin/amcache_explorer/
rm -r ${tmp_dir}/AmCacheParser/
rm ${tmp_dir}/AmCacheParser.zip

###############################################################################
# Install ShimCacheParser (AppCompatCacheParser)
###############################################################################

echo "Installing ShimCacheParser..."
curl -fSL -o "${tmp_dir}/ShimCacheParser.zip" \
  "https://download.ericzimmermanstools.com/net6/AppCompatCacheParser.zip"

shimcachep_expected_hash="08be9f08cd2a4f0080ffb6ac336bdaa3ffd357efac632c2f6a1f5415a8c06a57"
check_hash "${tmp_dir}/ShimCacheParser.zip" "$shimcachep_expected_hash"

unzip -q ${tmp_dir}/ShimCacheParser.zip -d ${tmp_dir}/ShimCacheParser/
mv ${tmp_dir}/ShimCacheParser/* ${toolkit_dir}/bin/shimcache_parser/
rm -r ${tmp_dir}/ShimCacheParser/
rm ${tmp_dir}/ShimCacheParser.zip

###############################################################################
# Install EvtxECmd
###############################################################################

echo "Installing EvtxECmd..."
curl -fSL -o "${tmp_dir}/EvtxECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/EvtxECmd.zip"

evtxecmd_expected_hash="a35a9080f52c144182a69f380f2a5194f80c32563abb485d8b083cd8b8e52651"
check_hash "${tmp_dir}/EvtxECmd.zip" "$evtxecmd_expected_hash"

unzip -q ${tmp_dir}/EvtxECmd.zip -d ${tmp_dir}/EvtxECmd/
rm -r "${toolkit_dir}/bin/evtx_explorer/Maps/" || true
mv ${tmp_dir}/EvtxECmd/EvtxECmd/* ${toolkit_dir}/bin/evtx_explorer/
rm -r ${tmp_dir}/EvtxECmd/
rm ${tmp_dir}/EvtxECmd.zip

###############################################################################
# Install PECmd (Prefetch Explorer)
###############################################################################

echo "Installing PECmd..."
curl -fSL -o "${tmp_dir}/PECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/PECmd.zip"

pecmd_expected_hash="42007057c50c07fa955be8bf738901b2b2dad0a94ede8e03087c4d40b0f8b4b5"
check_hash "${tmp_dir}/PECmd.zip" "$pecmd_expected_hash"

unzip -q ${tmp_dir}/PECmd.zip -d ${tmp_dir}/PECmd/
mv ${tmp_dir}/PECmd/* ${toolkit_dir}/bin/prefetch_explorer/
rm -r ${tmp_dir}/PECmd/
rm ${tmp_dir}/PECmd.zip

###############################################################################
# Install JLECmd (Jumplist Explorer)
###############################################################################

echo "Installing JLECmd..."
curl -fSL -o "${tmp_dir}/JLECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/JLECmd.zip"

jlecmd_expected_hash="5897b96a8a34719304d7c8b287ceb15a6ca50ab565d7e1028f61ae3095e8bfeb"
check_hash "${tmp_dir}/JLECmd.zip" "$jlecmd_expected_hash"

unzip -q ${tmp_dir}/JLECmd.zip -d ${tmp_dir}/JLECmd/
mv ${tmp_dir}/JLECmd/* ${toolkit_dir}/bin/jumplist_explorer/
rm -r "${tmp_dir}/JLECmd/"
rm "${tmp_dir}/JLECmd.zip"

###############################################################################
# Install LECmd (LNK Explorer)
###############################################################################

echo "Installing LECmd..."
curl -fSL -o "${tmp_dir}/LECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/LECmd.zip"

lecmd_expected_hash="9a7a145c172eb4f5fcf95f4377780003b3ee3ced5f851de4befbee6501d5ef08"
check_hash "${tmp_dir}/LECmd.zip" "$lecmd_expected_hash"

unzip -q ${tmp_dir}/LECmd.zip -d ${tmp_dir}/LECmd/
mv ${tmp_dir}/LECmd/* ${toolkit_dir}/bin/lnk_explorer/
rm -r ${tmp_dir}/LECmd/
rm ${tmp_dir}/LECmd.zip

###############################################################################
# Install RECmd (Registry Explorer)
###############################################################################

echo "Installing RECmd..."
curl -fSL -o "${tmp_dir}/RECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/RECmd.zip"

recmd_expected_hash="318ee17ede7d5ffbcb59382c318c4cb09e1ab3341b4c5683779237ea56dac27f"
check_hash "${tmp_dir}/RECmd.zip" "$recmd_expected_hash"

unzip -q "${tmp_dir}/RECmd.zip" -d "${tmp_dir}/RECmd/"
mv "${tmp_dir}/RECmd/"* "${toolkit_dir}/bin/registry_explorer/"
rm -r "${tmp_dir}/RECmd/"
rm "${tmp_dir}/RECmd.zip"

###############################################################################
# Install SrumECmd
###############################################################################

echo "Installing SrumECmd..."
curl -fSL -o "${tmp_dir}/SrumECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/SrumECmd.zip"

srumecmd_expected_hash="09762bdbd45ebaa4bd6e2cfa6dc8cdaea2092ee6b657420787098d8a6397e9c4"
check_hash "${tmp_dir}/SrumECmd.zip" "$srumecmd_expected_hash"

unzip -q ${tmp_dir}/SrumECmd.zip -d ${tmp_dir}/SrumECmd/
mv ${tmp_dir}/SrumECmd/* ${toolkit_dir}/bin/srum_explorer/
rm -r ${tmp_dir}/SrumECmd/
rm ${tmp_dir}/SrumECmd.zip

###############################################################################
# Install SBECmd (ShellBags Explorer)
###############################################################################

echo "Installing SBECmd..."
curl -fSL -o "${tmp_dir}/SBECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/SBECmd.zip"

sbecmd_expected_hash="769c0c3548efa70f81748918a7cef017f106438e9fa516e1415450ce6310f451"
check_hash "${tmp_dir}/SBECmd.zip" "$sbecmd_expected_hash"

unzip -q ${tmp_dir}/SBECmd.zip -d ${tmp_dir}/SBECmd/
mv ${tmp_dir}/SBECmd/* ${toolkit_dir}/bin/shellbags_explorer/
rm -r ${tmp_dir}/SBECmd/
rm ${tmp_dir}/SBECmd.zip

###############################################################################
# Install SqlECmd (SQLite Explorer)
###############################################################################

echo "Installing SQLECmd..."
curl -fSL -o "${tmp_dir}/SQLECmd.zip" \
  "https://download.ericzimmermanstools.com/net6/SQLECmd.zip"

sqlecmd_expected_hash="f01a20187ead06d4b187d79710341164f25fd8c171bca6ef3045a60166b25313"
check_hash "${tmp_dir}/SQLECmd.zip" "$sqlecmd_expected_hash"

unzip -q ${tmp_dir}/SQLECmd.zip -d ${tmp_dir}/SQLECmd/
rm -r "${toolkit_dir}/bin/sql_explorer/Maps/" || true
mv ${tmp_dir}/SQLECmd/SQLECmd/* ${toolkit_dir}/bin/sql_explorer/
rm -r ${tmp_dir}/SQLECmd/
rm ${tmp_dir}/SQLECmd.zip

###############################################################################
# Install RLA (Registry Log Analysis)
###############################################################################

echo "Installing RLA..."
curl -fSL -o "${tmp_dir}/rla.zip" \
  "https://download.ericzimmermanstools.com/net6/rla.zip"

rla_expected_hash="77f4c50706ebf3778420fda70a0b3dbebccd2cfbd302286f3b4407866a4dcbaf"
check_hash "${tmp_dir}/rla.zip" "$rla_expected_hash"

unzip -q ${tmp_dir}/rla.zip -d ${tmp_dir}/rla/
mv ${tmp_dir}/rla/* ${toolkit_dir}/bin/registry_log_analysis/
rm -r ${tmp_dir}/rla/
rm ${tmp_dir}/rla.zip

###############################################################################
# .NET 6 runtime (Linux build)
###############################################################################

echo "Installing .NET 6 runtime (Linux x64)..."
curl -fSL -o "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" \
  "https://download.visualstudio.microsoft.com/download/pr/0ce1c34f-0d9e-4d9b-964e-da676c8e605a/7a6c353b36477fa84f85b2821f2350c2/dotnet-runtime-6.0.0-linux-x64.tar.gz"

dotnet_expected_hash="1a4076139944f3b16d9a0fc4841190cf060a9d93ebc13330821a2e97f6d4db91"
check_hash "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" "$dotnet_expected_hash"

tar -xzf "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz" -C "${toolkit_dir}/bin/dotnet-runtime-600/"
rm "${tmp_dir}/dotnet-runtime-6.0.0-linux-x64.tar.gz"

###############################################################################
# .NET 9 runtime (Linux build)
###############################################################################

net9_ver="9.0.0"

echo "Installing .NET 9 runtime (Linux x64)..."
curl -fSL -o "${tmp_dir}/dotnet-runtime-${net9_ver}-linux-x64.tar.gz" \
  "https://download.visualstudio.microsoft.com/download/pr/282bb881-c2ae-4250-b814-b362745073bd/6e15021d23f704c0d457c820a69a3de6/dotnet-runtime-9.0.0-linux-x64.tar.gz"

dotnet_expected_hash="f017c3ae36d0b7bbf31d67fe305abe598a5967eaf7bfe45b8eca77bb611cefcf"
check_hash "${tmp_dir}/dotnet-runtime-${net9_ver}-linux-x64.tar.gz" "$dotnet_expected_hash"

tar -xzf "${tmp_dir}/dotnet-runtime-${net9_ver}-linux-x64.tar.gz" -C "${toolkit_dir}/bin/dotnet-runtime-900/"
rm "${tmp_dir}/dotnet-runtime-${net9_ver}-linux-x64.tar.gz"

###############################################################################
# Python module installations from requirements.txt
###############################################################################

echo "Installing Python requirements..."
pip install --break-system-packages -r "${toolkit_dir}/requirements.txt"

###############################################################################
# Cleanup and exit
###############################################################################

echo "Removing unneeded files..."
files_to_remove=(
  ".gitkeep"
  "risk_assessment.docx"
  "README.md"
  "initialise.ps1"
)

for pattern in "${files_to_remove[@]}"; do
  find "${toolkit_dir}" -maxdepth 2 -type f -name "${pattern}" -exec rm -f {} +
done

echo -e "\nSetup has completed!"
