"""
MommyShops - Streamlit App for Streamlit Cloud Deployment
This is the main entry point for Streamlit Community Cloud
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import the frontend
from frontend import *

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="MommyShops - Analiza tus Productos",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Run the main frontend
    main()