<#
    Script description.

    Some notes.
#>
param(
# script name without extension
    [Parameter(Mandatory = $true)]
    [String]$script,

# optional parameter 1
    [Parameter(Mandatory = $false)]
    [String]$param1,

# optional parameter 2
    [Parameter(Mandatory = $false)]
    [String]$param2
)

$venv = "$PSScriptRoot\\venv"
if (Test-Path -Path $venv)
{
}
else
{
    "VENV doesn't exist. Create venv from python3 >= 3.8 and <= 3.10"
    exit
}

PowerShell $PSScriptRoot\\venv\\scripts\\Activate.ps1

PowerShell $PSScriptRoot\\venv\\scripts\\python.exe $PSScriptRoot\\src\\$script.py $param1 $param2
