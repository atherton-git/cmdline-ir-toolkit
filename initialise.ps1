###############################################################################
# install-toolkit.ps1
###############################################################################

# Set execution policy to bypass for this process
Set-ExecutionPolicy Bypass -Scope Process -Force

###############################################################################
# Check for Admin Privileges
###############################################################################

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-Not $isAdmin) {
    Write-Log "Installing for all users requires administrative privileges." -Level "Error"
    exit 1
}

# Define Hash Mismatch Policy
$HashMismatchPolicy = "Warn"  # Options: "Strict", "Warn", or "Ask"

# List of tools to install - comment out tools you do not want to install
$ToolInstallList = @(
	"AmCacheParser"
	"ShimCacheParser"
	"EvtxECmd"
	"PECmd"
	"JLECmd"
	"LECmd"
	"RECmd"
	"SrumECmd"
	"SBECmd"
	"SqlEcmd"
	"RLA"
	"Hayabusa"
	"DotNetRuntime"
	"Java"
	"Python"
)

# Define relative paths based on the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$toolpath = Join-Path $scriptDir "bin"
$tmp_dir  = Join-Path $scriptDir "tmp"
$output_dir  = Join-Path $scriptDir "_output"

# Define files to remove after installation
$filesToRemove = @(
	"risk_assessment.docx",
	"README.md",
	"initialise.sh",
	".gitkeep"
)

###############################################################################
# Function: Write-Log
###############################################################################

function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "Info"
    )
    switch ($Level) {
        "Info"    { Write-Host    "[INFO] $Message" -ForegroundColor Cyan }
        "Warning" { Write-Warning "[WARNING] $Message" }
        "Error"   { Write-Error   "[ERROR] $Message" }
    }
}

###############################################################################
# Function: Handle-HashMismatch
###############################################################################

function Handle-HashMismatch {
    param (
        [string]$ExpectedHash,
        [string]$ActualHash,
        [string]$FilePath
    )

    $message = "Hash mismatch for '$FilePath'! Expected: $ExpectedHash, Got: $ActualHash"

    switch ($HashMismatchPolicy) {
        "Strict" {
            Write-Log $message -Level "Error"
            throw "Hash mismatch detected. Aborting due to strict policy."
        }
        "Warn" {
            Write-Log $message -Level "Warning"
        }
        "Ask" {
            Write-Log $message -Level "Warning"
            while ($true) {
                $userChoice = Read-Host "Hash mismatch detected. Choose an action: [A]bort, [C]ontinue, [R]etry"
                switch ($userChoice.ToUpper()) {
                    "A" {
                        Write-Log "Aborting due to user choice." -Level "Error"
                        throw "Hash mismatch detected. Aborted by user."
                    }
                    "C" {
                        Write-Log "Continuing despite hash mismatch."
                        return
                    }
                    "R" {
                        Write-Log "Retrying download..."
                        return "Retry"
                    }
                    Default {
                        Write-Host "Invalid choice. Please enter 'A' to Abort, 'C' to Continue, or 'R' to Retry."
                    }
                }
            }
        }
    }
}

###############################################################################
# Function: Download-File
###############################################################################

function Download-File {
    param (
        [string]$url,
        [string]$outpath,
        [string]$expectedHash = $null
    )

    do {
        try {
            Write-Log "Downloading from $url..."
            Invoke-WebRequest -Uri $url -OutFile $outpath -ErrorAction Stop
            Write-Log "Download completed."

            if (-not (Test-Path -Path $outpath)) {
                throw "Downloaded file not found at $outpath"
            }

            if ($expectedHash) {
                Write-Log "Verifying file hash..."
                $fileHash = Get-FileHash -Path $outpath -Algorithm SHA256

                if ($fileHash.Hash -eq $expectedHash) {
                    Write-Log "File hash verified successfully."
                } else {
                    $result = Handle-HashMismatch -ExpectedHash $expectedHash -ActualHash $fileHash.Hash -FilePath $outpath
                    if ($result -eq "Retry") {
                        continue
                    }
                }
            }

            return $true  # Indicate successful download and hash verification
        } catch {
            Write-Log "An error occurred during download or verification: $_" -Level "Error"
            return $false  # Indicate failure
        }
    } while ($true)
}

###############################################################################
# Function: Download-And-Run
###############################################################################

function Download-And-Run {
    param (
        [string]$url,
        [string]$outpath,
        [string]$expectedHash = $null,
        [array]$arguments = $null,
        [switch]$wait
    )

    if (Download-File -url $url -outpath $outpath -expectedHash $expectedHash) {
        try {
            Write-Log "Running $outpath..."
            # Conditionally pass the -ArgumentList parameter only if $arguments is not null or empty
            if ($arguments) {
                Start-Process -FilePath $outpath -ArgumentList $arguments -Wait:$wait
            } else {
                Start-Process -FilePath $outpath -Wait:$wait
            }

            Write-Log "Execution completed."
        } catch {
            Write-Log "An error occurred during execution: $_" -Level "Error"
        } finally {
            if (Test-Path -Path $outpath) {
                Remove-Item -Path $outpath -Force
                Write-Log "Cleaned up temporary file $outpath."
            }
        }
    }
}

###############################################################################
# Function: Download-And-Extract
###############################################################################

function Download-And-Extract {
    param (
        [string]$url,
        [string]$outpath,
        [string]$destination,
        [string]$expectedHash = $null
    )

    if (Download-File -url $url -outpath $outpath -expectedHash $expectedHash) {
        try {
            Write-Log "Extracting to $destination..."
            Expand-Archive -LiteralPath $outpath -DestinationPath $destination -Force
            Write-Log "Extraction completed."
        } catch {
            Write-Log "An error occurred during extraction: $_" -Level "Error"
        } finally {
            if (Test-Path -Path $outpath) {
                Remove-Item -Path $outpath -Force
                Write-Log "Cleaned up temporary file $outpath."
            }
        }
    }
}

###############################################################################
# Function: Check-Hash
###############################################################################

function Check-Hash {
    param (
        [string]$FilePath,
        [string]$ExpectedHash
    )

    if (-Not (Test-Path -Path $FilePath)) {
        Write-Log "WARNING: File not found: $FilePath" -Level "Warning"
        return $false
    }

    # Calculate the file hash
    $actualHash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToUpper()
    $expectedHash = $ExpectedHash.ToUpper()

    if ($actualHash -ne $expectedHash) {
        Write-Log "WARNING: File hash mismatch for $FilePath" -Level "Warning"
        Write-Log "Expected hash: $ExpectedHash" -Level "Warning"
        Write-Log "Actual hash  : $actualHash" -Level "Warning"
        $result = Handle-HashMismatch -ExpectedHash $ExpectedHash -ActualHash $actualHash -FilePath $FilePath
        if ($result -eq "Retry") {
            return $false
        } elseif ($result -eq $null) {
            return $true
        }
    } else {
        Write-Log "File hash check passed for $FilePath" -Level "Info"
        return $true
    }
}

###############################################################################
# Ensure the bin and tmp directories exist
###############################################################################

foreach ($dir in @($toolpath, $tmp_dir)) {
    if (-not (Test-Path -Path $dir)) {
        Write-Log "Creating directory at $dir"
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

###############################################################################
# Exit on errors
###############################################################################

$ErrorActionPreference = "Stop"

###############################################################################
# Function: Install-Hayabusa
###############################################################################

function Install-Hayabusa {
    Write-Log "Installing Hayabusa..." -Level "Info"
	$hayabusa_version       = "3.0.1"
	Add-MpPreference -ExclusionPath "$tmp_dir\hayabusa-$hayabusa_version-win-x64.zip"
    Add-MpPreference -ExclusionPath "$toolpath\hayabusa\rules\sigma\builtin\powershell\powershell_classic\*.yml"
    Add-MpPreference -ExclusionPath "$toolpath\hayabusa\rules\sigma\builtin\powershell\powershell_script\*.yml"
	Add-MpPreference -ExclusionPath "$output_dir\*.csv"
    $hayabusa_url           = "https://github.com/Yamato-Security/hayabusa/releases/download/v$hayabusa_version/hayabusa-$hayabusa_version-win-x64.zip"
    $hayabusa_path          = Join-Path $tmp_dir "hayabusa-$hayabusa_version-win-x64.zip"
    $hayabusa_expected_hash = "E3D732DC0DEB9C0AD623364B6FDEA3DCD744123821BF1843EC2943F084A7FD19"

    Download-And-Extract -url $hayabusa_url `
                         -outpath $hayabusa_path `
                         -destination "$toolpath\hayabusa" `
                         -expectedHash $hayabusa_expected_hash

    Rename-Item -Path "$toolpath\hayabusa\hayabusa-$hayabusa_version-win-x64.exe" -NewName "hayabusa.exe" -Force
    Write-Log "Hayabusa installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-AmCacheParser
###############################################################################

function Install-AmCacheParser {
    Write-Log "Installing AmCacheParser..." -Level "Info"

    $amcachep_url           = "https://download.ericzimmermanstools.com/net6/AmCacheParser.zip"
    $amcachep_path          = Join-Path $tmp_dir "AmCacheParser.zip"
    $amcachep_expected_hash = "0E0214D3B8D17500946E445F3DEC92F9485D00F788316EAA5CA78EBB31C92D78"

    Download-And-Extract -url $amcachep_url `
                         -outpath $amcachep_path `
                         -destination "$tmp_dir\AmCacheParser" `
                         -expectedHash $amcachep_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "AmCacheParser\*") -Destination $toolpath\amcache_explorer
	Write-Log "AmCacheParser installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-ShimCacheParser
###############################################################################

function Install-ShimCacheParser {
    Write-Log "Installing ShimCacheParser..." -Level "Info"

    $shimcachep_url           = "https://download.ericzimmermanstools.com/net6/AppCompatCacheParser.zip"
    $shimcachep_path          = Join-Path $tmp_dir "ShimCacheParser.zip"
    $shimcachep_expected_hash = "08BE9F08CD2A4F0080FFB6AC336BDAA3FFD357EFAC632C2F6A1F5415A8C06A57"

    Download-And-Extract -url $shimcachep_url `
                         -outpath $shimcachep_path `
                         -destination "$tmp_dir\ShimCacheParser" `
                         -expectedHash $shimcachep_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "ShimCacheParser\*") -Destination $toolpath\shimcache_parser
	Write-Log "ShimCacheParser installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-EvtxECmd
###############################################################################

function Install-EvtxECmd {
    Write-Log "Installing EvtxECmd..." -Level "Info"

    $evtxecmd_url           = "https://download.ericzimmermanstools.com/net6/EvtxECmd.zip"
    $evtxecmd_path          = Join-Path $tmp_dir "EvtxECmd.zip"
    $evtxecmd_expected_hash = "A35A9080F52C144182A69F380F2A5194F80C32563ABB485D8B083CD8B8E52651"

    Download-And-Extract -url $evtxecmd_url `
                         -outpath $evtxecmd_path `
                         -destination "$tmp_dir" `
                         -expectedHash $evtxecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "EvtxECmd\*") -Destination $toolpath\evtx_explorer
	Write-Log "EvtxECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-SqlECmd
###############################################################################

function Install-SqlECmd {
    Write-Log "Installing SqlECmd..." -Level "Info"

    $sqlecmd_url           = "https://download.ericzimmermanstools.com/net6/SqlECmd.zip"
    $sqlecmd_path          = Join-Path $tmp_dir "SqlECmd.zip"
    $sqlecmd_expected_hash = "F01A20187EAD06D4B187D79710341164F25FD8C171BCA6EF3045A60166B25313"

    Download-And-Extract -url $sqlecmd_url `
                         -outpath $sqlecmd_path `
                         -destination "$tmp_dir" `
                         -expectedHash $sqlecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "SqlECmd\*") -Destination $toolpath\sql_explorer
	Write-Log "SqlECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-RECmd
###############################################################################

function Install-RECmd {
    Write-Log "Installing EvtxECmd..." -Level "Info"

    $recmd_url           = "https://download.ericzimmermanstools.com/net6/RECmd.zip"
    $recmd_path          = Join-Path $tmp_dir "RECmd.zip"
    $recmd_expected_hash = "318EE17EDE7D5FFBCB59382C318C4CB09E1AB3341B4C5683779237EA56DAC27F"

    Download-And-Extract -url $recmd_url `
                         -outpath $recmd_path `
                         -destination "$tmp_dir" `
                         -expectedHash $recmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "RECmd\*") -Destination $toolpath\registry_explorer
	Write-Log "RECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-SrumECmd
###############################################################################

function Install-SrumECmd {
    Write-Log "Installing SrumECmd..." -Level "Info"

    $srumecmd_url           = "https://download.ericzimmermanstools.com/net6/SrumECmd.zip"
    $srumecmd_path          = Join-Path $tmp_dir "SrumECmd.zip"
    $srumecmd_expected_hash = "09762BDBD45EBAA4BD6E2CFA6DC8CDAEA2092EE6B657420787098D8A6397E9C4"

    Download-And-Extract -url $srumecmd_url `
                         -outpath $srumecmd_path `
                         -destination "$tmp_dir\SrumECmd" `
                         -expectedHash $srumecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "SrumECmd\*") -Destination $toolpath\srum_explorer
	Write-Log "SrumECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-PECmd
###############################################################################

function Install-PECmd {
    Write-Log "Installing PECmd..." -Level "Info"

    $pecmd_url           = "https://download.ericzimmermanstools.com/net6/PECmd.zip"
    $pecmd_path          = Join-Path $tmp_dir "PECmd.zip"
    $pecmd_expected_hash = "42007057C50C07FA955BE8BF738901B2B2DAD0A94EDE8E03087C4D40B0F8B4B5"

    Download-And-Extract -url $pecmd_url `
                         -outpath $pecmd_path `
                         -destination "$tmp_dir\PECmd" `
                         -expectedHash $pecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "PECmd\*") -Destination $toolpath\prefetch_explorer
	Write-Log "PECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-LECmd
###############################################################################

function Install-LECmd {
    Write-Log "Installing LECmd..." -Level "Info"

    $lecmd_url           = "https://download.ericzimmermanstools.com/net6/LECmd.zip"
    $lecmd_path          = Join-Path $tmp_dir "LECmd.zip"
    $lecmd_expected_hash = "9A7A145C172EB4F5FCF95F4377780003B3EE3CED5F851DE4BEFBEE6501D5EF08"

    Download-And-Extract -url $lecmd_url `
                         -outpath $lecmd_path `
                         -destination "$tmp_dir\LECmd" `
                         -expectedHash $lecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "LECmd\*") -Destination $toolpath\lnk_explorer
	Write-Log "LECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-JLECmd
###############################################################################

function Install-JLECmd {
    Write-Log "Installing JLECmd..." -Level "Info"

    $jlecmd_url           = "https://download.ericzimmermanstools.com/net6/JLECmd.zip"
    $jlecmd_path          = Join-Path $tmp_dir "JLECmd.zip"
    $jlecmd_expected_hash = "5897B96A8A34719304D7C8B287CEB15A6CA50AB565D7E1028F61AE3095E8BFEB"

    Download-And-Extract -url $jlecmd_url `
                         -outpath $jlecmd_path `
                         -destination "$tmp_dir\JLECmd" `
                         -expectedHash $lecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "JLECmd\*") -Destination $toolpath\jumplist_explorer
	Write-Log "JLECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-SBECmd
###############################################################################

function Install-SBECmd {
    Write-Log "Installing SBECmd..." -Level "Info"

    $sbecmd_url           = "https://download.ericzimmermanstools.com/net6/SBECmd.zip"
    $sbecmd_path          = Join-Path $tmp_dir "SBECmd.zip"
    $sbecmd_expected_hash = "769C0C3548EFA70F81748918A7CEF017F106438E9FA516E1415450CE6310F451"

    Download-And-Extract -url $sbecmd_url `
                         -outpath $sbecmd_path `
                         -destination "$tmp_dir\SBECmd" `
                         -expectedHash $sbecmd_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "SBECmd\*") -Destination $toolpath\shellbags_explorer
	Write-Log "SBECmd installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-RLA
###############################################################################

function Install-RLA {
    Write-Log "Installing RLA..." -Level "Info"

    $rla_url           = "https://download.ericzimmermanstools.com/net6/rla.zip"
    $rla_path          = Join-Path $tmp_dir "rla.zip"
    $rla_expected_hash = "77F4C50706EBF3778420FDA70A0B3DBEBCCD2CFBD302286F3B4407866A4DCBAF"

    Download-And-Extract -url $rla_url `
                         -outpath $rla_path `
                         -destination "$tmp_dir\rla" `
                         -expectedHash $rla_expected_hash

    Move-Item -Path (Join-Path $tmp_dir "rla\*") -Destination $toolpath\registry_log_analysis
	Write-Log "RLA installation complete!" -Level "Info"
}

###############################################################################
# Function: Install-Python
###############################################################################

function Install-Python {
    Write-Host "Checking Python installation..." -Level "Info"
    $pythonVersionRequired = "3.12.4"
    $versionCheck = ""
    try {
        # Attempt to get Python version
        $versionCheck = & python --version 2>&1
    } catch {
        # Assume Python is not installed if the command fails
    }

    if ($versionCheck -match "Python $pythonVersionRequired") {
        Write-Host "Python $pythonVersionRequired is already installed."
    }
    else {
        Write-Host "Python $pythonVersionRequired is not installed. Proceeding with installation..." -Level "Info"

        # Define Python installer details
        $pythonUrl       = "https://www.python.org/ftp/python/$pythonVersionRequired/python-$pythonVersionRequired-amd64.exe"
        $pythonHash      = "DA5809DF5CB05200B3A528A186F39B7D6186376CE051B0A393F1DDF67C995258"
        $pythonInstaller = Join-Path $tmp_dir "python-$pythonVersionRequired-amd64.exe"

        # Use Download-And-Run to handle download, hash verification, and execution
        Download-And-Run -url $pythonUrl `
                        -outpath $pythonInstaller `
                        -expectedHash $pythonHash `
                        -arguments @("/passive", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1") `
                        -wait

        Write-Host "Python installation initiated." -Level "Info"

        # Specify python.exe path if not in PATH
        $pythonExe = Join-Path $env:ProgramW6432 "\Python312\python.exe"

        if (-not (Test-Path $pythonExe)) {
            Write-Host "Could not find Python at $pythonExe. Please verify installation." -Level "Error"
            return
        }

        # Upgrade pip
        try {
            Write-Host "Upgrading pip..." -Level "Info"
            & $pythonExe -m pip install --upgrade pip
        } catch {
            Write-Host "Could not upgrade pip. Continuing..." -Level "Warning"
        }

        # Install dependencies from requirements.txt
        $requirementsFile = Join-Path $scriptDir "requirements.txt"
        if (Test-Path $requirementsFile) {
            Write-Host "Installing Python dependencies from requirements.txt..." -Level "Info"
            try {
                & $pythonExe -m pip install --break-system-packages -r $requirementsFile
            } catch {
                Write-Host "Failed to install some Python dependencies." -Level "Error"
            }
        }
        else {
            Write-Host "requirements.txt not found in $scriptDir. Skipping Python module installation." -Level "Warning"
        }
    }
}

###############################################################################
# Function: Install-Java
###############################################################################

function Install-Java {
    Write-Host "Checking Java installation..." -Level "Info"
    $javaVersionRequired = "21.0.3+9"
    $javaExePath = "C:\Program Files\Eclipse Adoptium\jre-21.0.3.9-hotspot\bin\java.exe"  # Adjust this path based on the installer

    # Check if Java is already installed by verifying the presence of java.exe
    if (Test-Path -Path $javaExePath) {
        try {
            $installedVersion = & "$javaExePath" -version 2>&1 | Select-String -Pattern 'version "(\d+\.\d+\.\d+)\+(\d+)"' | ForEach-Object {
                $_.Matches[0].Groups[1].Value + "+" + $_.Matches[0].Groups[2].Value
            }
        } catch {
            $installedVersion = ""
        }

        if ($installedVersion -eq $javaVersionRequired) {
            Write-Host "Java $javaVersionRequired is already installed." -Level "Info"
            return
        }
        else {
            Write-Host "Different Java version detected ($installedVersion). Proceeding with installation of Java $javaVersionRequired..." -Level "Info"
        }
    }
    else {
        Write-Host "Java is not installed. Proceeding with installation..." -Level "Info"
    }

    # Define Java installer details
    $javaUrl        = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.3+9/OpenJDK21U-jre_x64_windows_hotspot_21.0.3_9.msi"
    $javaHash       = "790BD6BD823618CE33E366294159282B92D3FCD41886E375FD4B876843E0D90F"
    $javaInstaller  = Join-Path $tmp_dir "OpenJDK21U-jre_x64_windows_hotspot_21.0.3_9.msi"

    # Use Download-And-Run to handle download, hash verification, and execution
    Download-And-Run -url $javaUrl `
                    -outpath $javaInstaller `
                    -expectedHash $javaHash `
                    -arguments @("INSTALLLEVEL=1", "/passive") `
                    -wait

    Write-Host "Java installation initiated." -Level "Info"

    # Clean up downloaded installer
    if (Test-Path -Path $javaInstaller) {
        Remove-Item -Path $javaInstaller -Force
        Write-Host "Cleaned up temporary installer at $javaInstaller." -Level "Info"
    }
}

###############################################################################
# Function: Install-DotNetRuntime
###############################################################################

function Install-DotNetRuntime {
    Write-Log "Installing .NET 6 runtime..." -Level "Info"

    $dotnet_url           = "https://download.visualstudio.microsoft.com/download/pr/6b96c97d-9b8c-4141-a32a-5848d3369dbf/9972321cb7af5938fecdee2d8ebd72bb/dotnet-runtime-6.0.0-win-x64.zip"
    $dotnet_path          = Join-Path $tmp_dir "dotnet-runtime-6.0.0-win-x64.zip"
    $dotnet_expected_hash = "095C8284ACECB07532390FF8ABDEDCF4E2F39005A4C58BD51CB5661A8379A6F6"

    Download-And-Extract -url $dotnet_url `
                         -outpath $dotnet_path `
                         -destination "$toolpath\dotnet-runtime-600" `
                         -expectedHash $dotnet_expected_hash

    Write-Log ".NET 6 runtime installation complete!" -Level "Info"
}

###############################################################################
# Main Script Execution
###############################################################################

Write-Log "`nStarting toolkit setup..." -Level "Info"

# Install tools based on $ToolInstallList
foreach ($tool in $ToolInstallList) {
    switch ($tool) {
        "AmCacheParser" {
            Install-AmCacheParser
        }
        "ShimCacheParser" {
            Install-ShimCacheParser
        }
        "EvtxECmd" {
            Install-EvtxECmd
        }
        "SrumECmd" {
            Install-SrumECmd
        }
        "SqlECmd" {
            Install-SqlECmd
        }
        "PECmd" {
            Install-PECmd
        }
        "JLECmd" {
            Install-JLECmd
        }
        "SBECmd" {
            Install-SBECmd
        }
        "LECmd" {
            Install-LECmd
        }
        "RECmd" {
            Install-RECmd
        }
        "RLA" {
            Install-RLA
        }
        "Hayabusa" {
            Install-Hayabusa
        }
        "DotNetRuntime" {
            Install-DotNetRuntime
        }
        "Java" {
            Install-Java
        }
        "Python" {
            Install-Python
        }
        default {
            Write-Log "No installation routine defined for tool: $tool" -Level "Warning"
        }
    }
}

###############################################################################
# Cleanup and exit
###############################################################################

Write-Host "Removing unneeded files..."
Get-ChildItem -Path $scriptDir -Filter ".gitkeep" -Recurse -Depth 1 -File |
    Remove-Item -Force

$filesToRemove = @(
    "risk_assessment.docx",
    "README.md",
    "initialise.sh"
)

foreach ($file in $filesToRemove) {
    Write-Host "Removing any $file..."
    Get-ChildItem -Path $scriptDir -Filter $file -File |
        Remove-Item -Force
}

Write-Log "`nToolkit setup complete. The script will exit in 10 seconds..." -Level "Info"
Start-Sleep -Seconds 10
exit
