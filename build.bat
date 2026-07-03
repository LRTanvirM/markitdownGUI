@echo off
setlocal
cd /d "%~dp0"

echo === [1/4] Installing dependencies ===
python -m pip install -r requirements.txt || goto :err

echo === [2/4] Generating app icon ===
python make_icon.py || goto :err

echo === [3/4] Building the app (onefile exe + onedir folder) ===
python -m PyInstaller --noconfirm MarkItDownGUI.spec || goto :err

echo === [4/4] Zipping the portable onedir build ===
powershell -NoProfile -Command "Compress-Archive -Path 'dist\MarkItDownGUI\*' -DestinationPath 'dist\MarkItDownGUI-portable.zip' -Force" || goto :err

echo.
echo Build complete:
echo   dist\MarkItDownGUI.exe                (onefile - portable, slower first launch)
echo   dist\MarkItDownGUI\MarkItDownGUI.exe  (onedir  - fast launch)
echo   dist\MarkItDownGUI-portable.zip       (onedir zipped for sharing)

rem Optional: build a distributable Setup.exe if Inno Setup is installed.
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    echo === Building installer with Inno Setup ===
    "%ISCC%" installer.iss || goto :err
    echo Installer complete:  dist\MarkItDown-1.0-Setup.exe
) else (
    echo.
    echo Inno Setup not found - skipped Setup.exe.
    echo   To install now with no extra tools, run:  install.bat
    echo   To build a shareable Setup.exe, install Inno Setup, then re-run build.bat
)
goto :eof

:err
echo.
echo Build FAILED.
exit /b 1
