@echo off
cd /d "%~dp0"
call venv\Scripts\activate
pip install pyinstaller --force-reinstall
pyinstaller --onefile --noconsole ^
--add-data "templates;templates" ^
--add-data "static;static" ^
--add-data "instance;instance" ^
--add-data "routes;routes" ^
--add-data "migrations;migrations" ^
--add-data "models.py;." ^
--add-data "app.py;." ^
--hidden-import=flask_migrate ^
--hidden-import=flask_login ^
--hidden-import=alembic ^
--hidden-import=fpdf2 ^
--hidden-import=xlsxwriter ^
--hidden-import=pandas ^
--name="AcademyDesktop" run_desktop.py
echo Built! Check dist\AcademyDesktop.exe
pause
