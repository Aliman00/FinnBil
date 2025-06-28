"""
Sidebar component for FinnBil webapp.
"""
import streamlit as st
import time
import random
import asyncio
from typing import List

from config.settings import settings
from utils.common import is_valid_finn_url, truncate_url_for_display, filter_valid_urls
from utils.logging import logger


class SidebarComponent:
    """Handles sidebar rendering and URL management."""
    
    def __init__(self):
        self.logger = logger
    
    def render(self) -> None:
        """Render the complete sidebar."""
        st.sidebar.title("🚗 FinnBil Analyzer")
        st.sidebar.markdown("---")
        
        self._render_url_management()
        self._render_fetch_section()
        self._render_status_display()
    
    def _render_url_management(self) -> None:
        """Render the URL management section."""
        st.sidebar.subheader("📋 URL-er")
        
        # Check if there are any URLs to display
        if not st.session_state.finn_urls:
            st.sidebar.info("Ingen URL-er lagt til ennå")
            # Add button to restore default URL
            if st.sidebar.button("➕ Legg til standard søke-URL", help="Legger til standard Finn.no søk"):
                st.session_state.finn_urls.append(settings.app.default_finn_url)
                st.sidebar.success("✅ Standard URL lagt til")
                st.rerun()
        else:
            self._render_existing_urls()
        
        st.sidebar.markdown("---")
        self._render_add_url_section()
    
    def _render_existing_urls(self) -> None:
        """Render existing URLs with delete buttons."""
        for i, url in enumerate(st.session_state.finn_urls):
            col1, col2 = st.sidebar.columns([4, 1])
            
            with col1:
                if url.strip():
                    display_url = truncate_url_for_display(
                        url, 
                        settings.app.display_url_truncate_length
                    )
                    st.text(f"{i+1}. {display_url}")
                else:
                    st.text(f"{i+1}. (tom URL)")
            
            with col2:
                if st.button("🗑️", key=f"delete_{i}", help="Slett denne URL-en"):
                    st.session_state.finn_urls.pop(i)
                    self.logger.info(f"Deleted URL at index {i}")
                    st.rerun()
    
    def _render_add_url_section(self) -> None:
        """Render the add new URL section."""
        # Input for new URL
        new_url = st.sidebar.text_area(
            "Legg til ny URL:",
            height=100,
            help="Lim inn URL fra Finn.no bilsøk (kun finn.no URLer tillatt)",
            placeholder="https://www.finn.no/mobility/search/car?...",
            max_chars=settings.app.max_url_length
        )
        
        # Add URL button
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button("➕ Legg til URL", disabled=not new_url.strip()):
                self._handle_add_url(new_url.strip())
    
    def _handle_add_url(self, new_url: str) -> None:
        """Handle adding a new URL."""
        if not new_url:
            st.sidebar.error("URL kan ikke være tom")
            return
        
        if not is_valid_finn_url(new_url):
            st.sidebar.error("❌ Kun gyldige Finn.no bil-søk URLer er tillatt")
            return
        
        if new_url in st.session_state.finn_urls:
            st.sidebar.warning("URL finnes allerede")
            return
        
        st.session_state.finn_urls.append(new_url)
        st.sidebar.success("✅ URL lagt til")
        self.logger.info(f"Added new URL: {new_url[:50]}...")
        st.rerun()
    
    def _render_fetch_section(self) -> None:
        """Render the fetch data section."""
        st.sidebar.markdown("---")
        
        # Fetch button
        if st.sidebar.button("🔄 Hent og analyser alle URL-er", type="primary"):
            self._fetch_new_data()
    
    def _render_status_display(self) -> None:
        """Render the current data status."""
        if st.session_state.parsed_cars_list:
            valid_url_count = len(filter_valid_urls(st.session_state.finn_urls))
            st.sidebar.text("")
            st.sidebar.success(
                f"✅ {len(st.session_state.parsed_cars_list)} biler lastet "
                f"fra {valid_url_count} URL-er"
            )
    
    def _fetch_new_data(self) -> None:
        """Fetch new data from all Finn.no URLs and reset analysis state."""
        valid_urls = filter_valid_urls(st.session_state.finn_urls)
        
        # Display errors for invalid URLs
        for url in st.session_state.finn_urls:
            if url.strip() and not is_valid_finn_url(url.strip()):
                display_url = truncate_url_for_display(url, 50)
                st.sidebar.error(f"❌ Ugyldig URL: {display_url}")
        
        if not valid_urls:
            st.sidebar.error("❌ Ingen gyldige URL-er å hente fra")
            return
        
        # Reset all state
        self._reset_session_state()
        
        with st.sidebar.status("Henter bildata...", expanded=True) as status:
            st.write(f"Kobler til Finn.no... ({len(valid_urls)} URL-er)")
            
            try:
                all_parsed_cars, all_raw_data = self._fetch_from_urls(valid_urls)
                
                if all_parsed_cars:
                    self._save_fetched_data(all_parsed_cars, all_raw_data, status)
                else:
                    status.update(label="Ingen data hentet", state="error", expanded=False)
                    st.sidebar.error("❌ Ingen bildata ble hentet fra noen av URL-ene")
                    
            except Exception as e:
                error_msg = f"Feil oppstod: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                status.update(label="Feil oppstod", state="error", expanded=False)
                st.sidebar.error(f"❌ {error_msg}")
    
    def _reset_session_state(self) -> None:
        """Reset session state for new data fetch."""
        st.session_state.raw_car_data_text = None
        st.session_state.parsed_cars_list = []
        st.session_state.messages = []
        st.session_state.initial_analysis_done = False
        self.logger.info("Reset session state for new data fetch")
    
    def _fetch_from_urls(self, valid_urls: List[str]) -> tuple:
        """Fetch data from all valid URLs."""
        all_parsed_cars = []
        all_raw_data = []
        total_urls = len(valid_urls)
        
        for i, url in enumerate(valid_urls, 1):
            st.write(f"Henter fra URL {i}/{total_urls}...")
            
            # Rate limiting between URL requests
            if i > 1:
                delay = random.uniform(
                    settings.scraping.rate_limit_delay_min,
                    settings.scraping.rate_limit_delay_max
                )
                time.sleep(delay)
            
            # Fetch data from current URL
            try:
                result = asyncio.run(
                    st.session_state.data_service.fetch_and_parse_cars(url)
                )
                
                if result.success:
                    all_parsed_cars.extend(result.cars)
                    if result.raw_data:
                        all_raw_data.append(result.raw_data)
                    st.write(f"✅ URL {i}: {len(result.cars)} biler")
                    self.logger.info(f"Successfully fetched {len(result.cars)} cars from URL {i}")
                else:
                    st.write(f"❌ URL {i}: {result.error_message}")
                    self.logger.warning(f"Failed to fetch from URL {i}: {result.error_message}")
                    
            except Exception as e:
                error_msg = f"Feil ved henting fra URL {i}: {str(e)}"
                st.write(f"❌ {error_msg}")
                self.logger.error(error_msg, exc_info=True)
        
        return all_parsed_cars, all_raw_data
    
    def _save_fetched_data(self, all_parsed_cars: List, all_raw_data: List, status) -> None:
        """Save fetched data and update status."""
        st.session_state.parsed_cars_list = all_parsed_cars
        st.session_state.raw_car_data_text = "\n\n".join(all_raw_data)
        
        # Save to file
        success = st.session_state.data_service.save_data_to_file(all_parsed_cars)
        if not success:
            self.logger.warning("Failed to save data to file")
        
        st.write(f"✅ Totalt hentet {len(all_parsed_cars)} biler")
        status.update(label="Data hentet!", state="complete", expanded=False)
        
        valid_url_count = len(filter_valid_urls(st.session_state.finn_urls))
        st.sidebar.success(f"✅ {len(all_parsed_cars)} biler hentet fra {valid_url_count} URL-er")
        
        self.logger.info(f"Successfully fetched and saved {len(all_parsed_cars)} cars")
        st.rerun()
