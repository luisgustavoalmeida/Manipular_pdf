@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo === Manipulador PDF — build PyInstaller ===
echo.

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"
if not defined PY (
    echo [ERRO] Ambiente virtual nao encontrado. Crie com: python -m venv .venv
    exit /b 1
)

echo Usando: %PY%
"%PY%" -m pip install -q -r requirements.txt pyinstaller

echo.
echo Compilando executavel (pode demorar alguns minutos)...
"%PY%" -m PyInstaller --noconfirm --clean manipular_pdf.spec
if errorlevel 1 (
    echo.
    echo [ERRO] Falha na compilacao.
    exit /b 1
)

echo.
echo === Concluido ===
echo Executavel: dist\ManipuladorPDF.exe
echo.
echo Copie dist\ManipuladorPDF.exe para onde quiser usar.
echo O config_usuario.json sera salvo em %%LOCALAPPDATA%%\ManipuladorPDF (nao ao lado do .exe).
echo.
echo Nota: conversao de Word/Excel/PowerPoint ainda exige LibreOffice instalado.
echo       Traducao exige conexao com a internet.
echo.
pause
