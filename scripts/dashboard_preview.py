"""Isolated synthetic preview for the analysis dashboard browser test.

Run: .venv/bin/python scripts/dashboard_preview.py
Then, from frontend/: npx playwright test e2e/analysis.spec.ts
No provider credentials are loaded and no provider requests are made.
"""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import Settings
from app.db import Base
from app.main import create_app
from app.seed import seed
import uvicorn


def main():
    runtime=ROOT/'.runtime'
    runtime.mkdir(mode=0o700,exist_ok=True)
    app=create_app(Settings(mode='demo',database_url='sqlite:///'+str(runtime/'dashboard-preview.db'),
        auto_sync=False,secure_cookies=False,origin='http://127.0.0.1:8003'))
    Base.metadata.create_all(app.state.engine)
    seed(app.state.sessions)
    root=ROOT/'frontend/dist'
    if not (root/'index.html').is_file():raise SystemExit('Build the frontend first: npm --prefix frontend run build')
    app.mount('/assets',StaticFiles(directory=root/'assets'))
    @app.get('/{path:path}')
    def frontend(path:str):return FileResponse(root/'index.html')
    uvicorn.run(app,host='127.0.0.1',port=8003,access_log=False)


if __name__=='__main__':main()
