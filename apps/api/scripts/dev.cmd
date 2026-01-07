@echo off
cd %~dp0..
call .venv\Scripts\activate.bat
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8002