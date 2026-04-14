@echo off
setlocal

cd /d %~dp0

echo [1/6] Checking Poetry...
set POETRY=C:\Users\User\AppData\Roaming\Python\Python314\Scripts\poetry.exe
if not exist "%POETRY%" (
  echo Poetry not found at %POETRY%
  echo Edit this BAT file and set the correct path to poetry.exe
  pause
  exit /b 1
)

echo [2/6] Installing dependencies...
"%POETRY%" install -E win --no-cache
if errorlevel 1 goto :fail

echo [3/6] Generating .mo files...
"%POETRY%" run python -m sportorg.language
if errorlevel 1 goto :fail

echo [4/6] Cleaning old build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [5/6] Building EXE via cx_Freeze...
"%POETRY%" run python builder.py build
if errorlevel 1 goto :fail

echo [6/6] Build complete.
echo Output folder should be inside .\build\exe.win-amd64-3.8\
dir build
pause
exit /b 0

:fail
echo.
echo Build failed.
pause
exit /b 1
