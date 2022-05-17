# Trsync manager configure

This graphical application permit to manage [trsync manager](https://github.com/buxx/trsync/tree/main/manager) config file and signal [trsync manager](https://github.com/buxx/trsync/tree/main/manager) config reload.

# Package executable

1. Prepare and activate python virtual environment
2. Install dependencies from `requirements.txt` : `pip install -r requirements.txt`
3. Install pyinstaller : `pip install pyinstaller`
4. Package executable : `pyinstaller --name configure --onefile run.py`

Executable available in `dist` folder.
