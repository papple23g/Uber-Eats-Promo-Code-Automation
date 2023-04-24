@echo off

:: 刷新 PATH 環境變數
setx PATH "%PATH%"

:: 確保 Python 已安裝
where python >nul 2>nul
if errorlevel 1 (
    echo Python 未安裝, 正在自動下載並安裝...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del %TEMP%\python-installer.exe
    echo Python 安裝完成
    setx PATH "%PATH%"
)

:: 確保 pip 已安裝
where pip >nul 2>nul
if errorlevel 1 (
    echo pip 未安裝, 正在安裝...
    python -m ensurepip --default-pip
    echo pip 安裝完成
)

:: 確保 必要套件 已安裝
if not exist installed.txt (
    pip install -r requirements.txt
    playwright install
    echo > installed.txt
)

:: 執行程式
python main.py
pause