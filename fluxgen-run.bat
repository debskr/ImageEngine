@echo OFF
ECHO Starting Flux Image Generator Application...

REM Get the directory where this batch script is located
SET "BATCH_DIR=%~dp0"

REM --- Customize these paths if necessary ---
REM Path to your virtual environment's activate script
SET "VENV_ACTIVATE_SCRIPT=%BATCH_DIR%fluxgen\Scripts\activate.bat"

REM Name of your Python application script
SET "PYTHON_SCRIPT_NAME=fluxgen.py"
REM Full path to your Python script
SET "PYTHON_SCRIPT_PATH=%BATCH_DIR%%PYTHON_SCRIPT_NAME%"
REM --- End of customization section ---

REM Check if the virtual environment activate script exists
IF NOT EXIST "%VENV_ACTIVATE_SCRIPT%" (
    ECHO ERROR: Virtual environment activate script not found at:
    ECHO %VENV_ACTIVATE_SCRIPT%
    ECHO Please ensure the virtual environment 'flux_env' exists in the same directory as this batch file,
    ECHO or update the VENV_ACTIVATE_SCRIPT path in this batch file.
    PAUSE
    EXIT /B 1
)

REM Check if the Python script exists
IF NOT EXIST "%PYTHON_SCRIPT_PATH%" (
    ECHO ERROR: Python script not found at:
    ECHO %PYTHON_SCRIPT_PATH%
    ECHO Please ensure the script '%PYTHON_SCRIPT_NAME%' exists in the same directory as this batch file,
    ECHO or update the PYTHON_SCRIPT_PATH in this batch file.
    PAUSE
    EXIT /B 1
)

ECHO Activating virtual environment...
CALL "%VENV_ACTIVATE_SCRIPT%"

IF ERRORLEVEL 1 (
    ECHO ERROR: Failed to activate virtual environment.
    PAUSE
    EXIT /B 1
)

ECHO Virtual environment activated.
ECHO Running Python application: %PYTHON_SCRIPT_NAME%
ECHO.

REM Run the Python script
REM Using "python" command assumes it's correctly pathed after venv activation
python "%PYTHON_SCRIPT_PATH%"

REM Optional: Deactivate the virtual environment after the script finishes
REM This might close the command window immediately if the Python script exits quickly.
REM If you want to see output/errors from the Python script, you might comment this out or add a PAUSE before it.
REM CALL deactivate

ECHO.
ECHO Application finished or closed.
EXIT
@echo ON