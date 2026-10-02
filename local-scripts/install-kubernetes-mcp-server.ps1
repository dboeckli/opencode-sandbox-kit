#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the Kubernetes MCP server (containers/kubernetes-mcp-server) as a native
    Windows binary on the host (no credentials inside the sandbox).

.DESCRIPTION
    Downloads the official Windows release (amd64/arm64) from GitHub into a local bin
    directory. Idempotent: if the target version is already installed, nothing happens
    (unless -Force is given).

    Runs on the Windows host only - not inside the sandbox.
    Configuration/start: see docs/kubernetes-mcp-server.md (Issue #40).

.PARAMETER Version
    Release tag (e.g. "v0.0.67") or "latest" (default) for the current release version.

.PARAMETER InstallDir
    Target directory. Default: %USERPROFILE%\.local\bin

.PARAMETER AddToPath
    Add the directory to the user PATH (new shells). Default: true.
    Disable with -AddToPath:$false.

.PARAMETER Force
    Reinstall even if the target version is already present.

.EXAMPLE
    .\install-kubernetes-mcp-server.ps1

.EXAMPLE
    .\install-kubernetes-mcp-server.ps1 -Version v0.0.67

.EXAMPLE
    .\install-kubernetes-mcp-server.ps1 -AddToPath:$false
#>
[CmdletBinding()]
param(
    [string]$Version = "latest",
    [string]$InstallDir = (Join-Path $env:USERPROFILE ".local\bin"),
    [bool]$AddToPath = $true,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$repo = "containers/kubernetes-mcp-server"
$exeName = "kubernetes-mcp-server.exe"

function Get-ReleaseArch {
    switch ($env:PROCESSOR_ARCHITECTURE) {
        "AMD64" { "amd64" }
        "ARM64" { "arm64" }
        default { throw "Unsupported architecture: $env:PROCESSOR_ARCHITECTURE" }
    }
}

function Resolve-LatestTag {
    param([string]$Repo)
    try {
        $release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" `
            -Headers @{ "User-Agent" = "local-scripts/install-kubernetes-mcp-server" }
        return $release.tag_name
    }
    catch {
        $msg = "Could not resolve the latest release version ({0}). " -f $_.Exception.Message
        throw ($msg + "Please pass -Version vX.Y.Z explicitly.")
    }
}

function Add-InstallDirToPath {
    param([string]$InstallDir)
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$InstallDir;$userPath", "User")
        Write-Host "[install] Added '$InstallDir' to the user PATH (new shells)."
    }
    else {
        Write-Host "[install] '$InstallDir' is already in the user PATH."
    }
}

function Show-Summary {
    param(
        [string]$Version,
        [string]$ExePath,
        [string]$InstallDir,
        [bool]$AddToPath
    )
    $onPath = if ($AddToPath) { "yes (new shells)" } else { "no (-AddToPath:`$false)" }
    Write-Host ""
    Write-Host "kubernetes-mcp-server installed:" -ForegroundColor Green
    Write-Host ("  Version:      {0}" -f $Version)
    Write-Host ("  Binary:       {0}" -f $ExePath)
    Write-Host ("  Install dir:  {0}" -f $InstallDir)
    Write-Host ("  On PATH:      {0}" -f $onPath)
}

# --- Resolve target version ---
$target = if ($Version -eq "latest") { Resolve-LatestTag -Repo $repo } else { $Version }
$target = $target -replace '^v', ''
if ($target -notmatch '^\d+\.\d+\.\d+') {
    throw "Invalid -Version '$Version' (expected e.g. v0.0.67 or latest)."
}
$target = "v$target"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$exePath = Join-Path $InstallDir $exeName

# --- Idempotency: check already installed version ---
if ((Test-Path $exePath) -and -not $Force) {
    $installed = (& $exePath --version 2>$null | Select-Object -First 1)
    if ($installed -eq $target) {
        if ($AddToPath) { Add-InstallDirToPath -InstallDir $InstallDir }
        Show-Summary -Version $installed -ExePath $exePath -InstallDir $InstallDir -AddToPath $AddToPath
        return
    }
    Write-Host "[install] installed: $installed -> updating to $target"
}

# --- Fail if the server is running: Windows locks the .exe, replacement would fail ---
$running = Get-Process -Name "kubernetes-mcp-server" -ErrorAction SilentlyContinue
if ($running) {
    $pids = ($running | ForEach-Object { $_.Id }) -join ", "
    $msg = "kubernetes-mcp-server is running (PID $pids) - the binary cannot be replaced while in use.`n" +
        "Stop it first:`n" +
        "  Get-Process kubernetes-mcp-server | Stop-Process`n" +
        "Then re-run this script."
    throw $msg
}

# --- Download + install ---
$arch = Get-ReleaseArch
$asset = "kubernetes-mcp-server-windows-$arch.exe"
$url = "https://github.com/$repo/releases/download/$target/$asset"
$tmp = "$exePath.download"

Write-Host "[install] Downloading $url"
try {
    Invoke-WebRequest -Uri $url -OutFile $tmp
    Move-Item -Force $tmp $exePath
}
finally {
    if (Test-Path $tmp) { Remove-Item -Force $tmp -ErrorAction SilentlyContinue }
}
Unblock-File $exePath

# --- Verify ---
$newVersion = (& $exePath --version 2>$null | Select-Object -First 1)
if ($newVersion -ne $target) {
    throw "Version check failed: expected $target, got '$newVersion'."
}
# --- PATH + summary ---
if ($AddToPath) { Add-InstallDirToPath -InstallDir $InstallDir }
Show-Summary -Version $newVersion -ExePath $exePath -InstallDir $InstallDir -AddToPath $AddToPath
