<div style="margin: 25px; padding: 0;">
    <p align="center" style="margin: 0; padding: 0;">
      <img src="static/images/site/logo.png" alt="WarfPlanner logo"/>
    </p>
    <h1 align="center" style="margin: 0; padding: 0; color: #D83A32;">WarfPlanner</h1>
</div>

## FOR NOW IT IS ONLY A PoC (Proof of Concept) AND IT IS NOT USABLE YET

STATUS: **WIP** \
It is not usable yet, but I hope it will be one day.

## About

WarfPlanner is a tool for Arknights mobile game. It allows you to plan your characters upgrades, and see how much
resources you have and need. \
It uses AI to recognize materials from screenshots or open client of depot screen, and OCR to recognize amounts and type
of materials.

### TODO
- Add tooltips to icons
- Add screencapture from game
- Add AI for materials from screenshots/screencapture
- Add OCR for materials amounts
- Make it usable
- Make it executable/installable
- Add hide and show for characters in character list

### TODO (in future if all above is done)
- Add rooster mechanism for characters like:
  - https://www.krooster.com/
- Add AI for characters recognition from screenshots/screencapture

## Development
### Dependencies
#### 1. Python `3.8 - 3.11` (Because of `ultralytics` and `easyocr` uses `torch` dependency)


### Setup
#### 1. Copy .env.example to .env and fill it with your data
```shell
cp .env.example .env
```

#### 2. Creating virtual environment
```shell
python -m venv venv
```

#### 3. Activating virtual environment
| Platform | Shell      | Command to activate virtual environment |
|----------|------------|-----------------------------------------|
| POSIX    | bash/zsh   | source venv/bin/activate                |
|          | fish       | source venv/bin/activate.fish           |
|          | csh/tcsh   | source venv/bin/activate.csh            |
|          | PowerShell | venv/bin/Activate.ps1                   |
| Windows  | cmd.exe    | venv\Scripts\activate.bat               |
|          | PowerShell | venv\Scripts\Activate.ps1               |

#### 4. Upgrading pip
```shell
python.exe -m pip install --upgrade pip
```

#### 5. Installing dependencies
Why there is no `requirements.txt`? \
Because there are some dependencies that collide with each other, and some of them need to be installed in specific order.

##### Development dependencies
```shell
pip install black --no-cache-dir --force-reinstall --upgrade
pip install mypy --no-cache-dir --force-reinstall --upgrade
pip install types_requests --no-cache-dir --force-reinstall --upgrade
pip install types-PyYAML --no-cache-dir --force-reinstall --upgrade
pip install codespell --no-cache-dir --force-reinstall --upgrade
```

##### Main
```shell
pip install requests --no-cache-dir --force-reinstall --upgrade
pip install pyyaml --no-cache-dir --force-reinstall --upgrade
pip install python-dotenv --no-cache-dir --force-reinstall --upgrade
pip install requests --no-cache-dir --force-reinstall --upgrade
pip install marshmallow-dataclass --no-cache-dir --force-reinstall --upgrade
pip install pywebview --no-cache-dir --force-reinstall --upgrade
pip install flask --no-cache-dir --force-reinstall --upgrade
pip install waitress --no-cache-dir --force-reinstall --upgrade
pip install opencv-python --no-cache-dir --force-reinstall --upgrade
pip install scikit-learn --no-cache-dir --force-reinstall --upgrade
pip install scipy --no-cache-dir --force-reinstall --upgrade
pip install matplotlib --no-cache-dir --force-reinstall --upgrade
pip install autodistill-yolov8 --no-cache-dir --force-reinstall --upgrade
pip install roboflow --no-cache-dir --force-reinstall --upgrade
pip install hub_sdk --no-cache-dir --force-reinstall --upgrade
pip install ultralytics --no-cache-dir --force-reinstall --upgrade
pip install easyocr --no-cache-dir --force-reinstall --upgrade
#pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir --force-reinstall --upgrade
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir --force-reinstall --upgrade
```

### Running scripts
All scripts should be ran from root directory of the project and before running them, you should activate virtual environment.
#### Scripts
- `stubgen src -o .` - generates stubs for type hinting / mypy
- `black src` - formats code
- `codespell src -w` - checks spelling
- `mypy src` - checks types

- `python src\App.py` - runs the program
- `python src\ArknightsData` - downloads Arknights data/images and generates data for program

- `python src\AIAutoAnnotate.py` - runs automatic annotation of images
- `python src\AICreateImages.py` - runs generation of images for AI training / annotation
- `python src\AIDeployModel.py` - runs deployment of model to Roboflow
- `python src\AIDownloadLabels.py` - runs downloading of labels from Roboflow
- `python src\AITestModels.py` - runs testing of models
- `python src\AITrainModels.py` - runs training of models
- `python src\AIUploadModel.py` - runs uploading of model to Roboflow

## Acknowledgements / links:
- AI:
    - model and training:
        - [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)
    - labeling:
        - [roboflow](https://app.roboflow.com)
        - [autodistill/autodistill](https://github.com/autodistill/autodistill)
        - Labels for AI training are published via [Roboflow Universe](https://universe.roboflow.com)
          on [this link](https://universe.roboflow.com/moques/arknightsmaterials).
- OCR:
    - [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
- Arknights:
    - data:
        - [Kengxxiao/ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)
        - [Kengxxiao/ArknightsGameData_YoStar](https://github.com/Kengxxiao/ArknightsGameData_YoStar)
    - images:
        - [yuanyan3060/ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)
        - [Aceship/Arknight-Images](https://github.com/Aceship/Arknight-Images)
- Random images:
  - [https://picsum.photos](https://picsum.photos)
  - [https://source.unsplash.com](https://source.unsplash.com)
  - [https://loremflickr.com](https://loremflickr.com)
