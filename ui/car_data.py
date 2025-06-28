"""
Car data display component for FinnBil webapp.
"""
import streamlit as st
from typing import Optional

from utils.logging import logger


class CarDataComponent:
    """Handles car data table and statistics display."""
    
    def __init__(self):
        self.logger = logger
    
    def render(self) -> None:
        """Render the complete car data section."""
        if not st.session_state.parsed_cars_list:
            st.info("👈 Bruk sidepanelet for å hente bildata fra Finn.no")
            return
        
        st.header("📊 Bildata 🚗")
        
        try:
            # Display car table
            df = st.session_state.car_display.prepare_dataframe(st.session_state.parsed_cars_list)
            
            if not df.empty:
                self._render_car_table(df)
                st.markdown("---")
                self._render_statistics()
            else:
                st.warning("Ingen bildata å vise")
                
        except Exception as e:
            error_msg = f"Feil ved visning av bildata: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
    
    def _render_car_table(self, df) -> None:
        """Render the car data table."""
        try:
            # Get display columns in correct order
            display_columns = st.session_state.car_display.get_display_columns(df)
            
            # Display data table
            st.data_editor(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config=st.session_state.car_display.get_column_config(),
                disabled=True,
                height=400
            )
            
            self.logger.debug(f"Displayed car table with {len(df)} cars and columns: {display_columns}")
            
        except Exception as e:
            error_msg = f"Feil ved visning av biltabell: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
    
    def _render_statistics(self) -> None:
        """Render car statistics."""
        try:
            # Calculate and display statistics
            stats = st.session_state.data_service.calculate_statistics(st.session_state.parsed_cars_list)
            st.session_state.car_display.display_statistics(stats)
            
            self.logger.debug(f"Displayed statistics for {stats.get('total_cars', 0)} cars")
            
        except Exception as e:
            error_msg = f"Feil ved beregning av statistikk: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
