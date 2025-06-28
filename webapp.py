"""
FinnBil Analyzer - Main Streamlit application.

A comprehensive car analysis tool for Finn.no listings with AI-powered insights.
"""
import streamlit as st
from typing import Dict, Any

from config.settings import settings
from services.data_service import DataService
from services.ai_service import AIService
from ui.car_display import CarDataDisplay
from ui.sidebar import SidebarComponent
from ui.car_data import CarDataComponent
from ui.ai_analysis import AIAnalysisComponent
from utils.logging import logger


class FinnBilApp:
    """Main application class for FinnBil Analyzer."""
    
    def __init__(self):
        self.logger = logger
        self._configure_page()
        self._initialize_components()
        self._initialize_session_state()
    
    def _configure_page(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=settings.app.page_title,
            page_icon=settings.app.page_icon,
            layout="wide"  # Type-safe literal
        )
    
    def _initialize_components(self) -> None:
        """Initialize UI components."""
        self.sidebar = SidebarComponent()
        self.car_data = CarDataComponent()
        self.ai_analysis = AIAnalysisComponent()
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        # Data state
        if 'raw_car_data_text' not in st.session_state:
            st.session_state.raw_car_data_text = None
        if 'parsed_cars_list' not in st.session_state:
            st.session_state.parsed_cars_list = []
        
        # URL management state
        if 'current_finn_url' not in st.session_state:
            st.session_state.current_finn_url = settings.app.default_finn_url
        if 'finn_urls' not in st.session_state:
            # Start with default URL, but allow user to delete it completely
            st.session_state.finn_urls = [settings.app.default_finn_url]
        
        # AI chat state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'initial_analysis_done' not in st.session_state:
            st.session_state.initial_analysis_done = False
        
        # Initialize services once and cache in session state
        if 'data_service' not in st.session_state:
            st.session_state.data_service = DataService()
        if 'ai_service' not in st.session_state:
            st.session_state.ai_service = AIService()
        if 'car_display' not in st.session_state:
            st.session_state.car_display = CarDataDisplay()
        
        self.logger.debug("Session state initialized")
    
    def run(self) -> None:
        """Run the main application."""
        try:
            # Validate configuration
            settings.validate()
            
            # Render UI components
            self.sidebar.render()
            self.car_data.render()
            self.ai_analysis.render()
            
        except Exception as e:
            error_msg = f"Kritisk feil i applikasjonen: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            st.stop()


def main():
    """Application entry point."""
    try:
        app = FinnBilApp()
        app.run()
    except Exception as e:
        # Fallback error handling
        st.error(f"Kunne ikke starte applikasjonen: {str(e)}")
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()