"""Old entry point, kept so existing deployments that run
``streamlit run streamlit_main.py`` (e.g. Streamlit Community Cloud) keep working.
The app now lives in main.py."""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("main.py")), run_name="__main__")
