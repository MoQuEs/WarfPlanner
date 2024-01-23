$venv = "$PSScriptRoot\\venv"
if (Test-Path -Path $venv)
{
}
else
{
    "VENV doesn't exist. Create venv from python3 >= 3.8 and <= 3.10"
    exit
}

PowerShell $venv\\scripts\\Activate.ps1

PowerShell $venv\\scripts\\python.exe -m pip install --upgrade pip

PowerShell $venv\\scripts\\pip3.exe install requests --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install pyyaml --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install python-dotenv --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install requests --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install black --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install marshmallow-dataclass --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install pywebview --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install flask --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install waitress --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install opencv-python --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install scikit-learn --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install scipy --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install matplotlib --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install autodistill-grounded-sam --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install autodistill-yolov8 --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install roboflow --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install hub_sdk --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install ultralytics --no-cache-dir --force-reinstall --upgrade
PowerShell $venv\\scripts\\pip3.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir --force-reinstall --upgrade
#PowerShell $venv\\scripts\\pip3.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir --force-reinstall --upgrade




