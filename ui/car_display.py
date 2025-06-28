import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional

from utils.common import format_price, format_mileage
from utils.logging import logger


class CarDataDisplay:
    """Handles car data display and formatting."""
    
    def __init__(self):
        self.logger = logger
    
    def prepare_dataframe(self, cars_list: List[Dict]) -> pd.DataFrame:
        """
        Prepare and format car data for display.
        
        Args:
            cars_list: List of car dictionaries
            
        Returns:
            Formatted pandas DataFrame
        """
        try:
            if not cars_list:
                return pd.DataFrame()
            
            df_cars = pd.DataFrame(cars_list)
            
            # Ensure ID column is available for display
            if 'original_chunk_order' in df_cars.columns:
                df_cars['id'] = df_cars['original_chunk_order']
            elif 'id' not in df_cars.columns:
                # Create ID column if it doesn't exist
                df_cars['id'] = range(1, len(df_cars) + 1)

            # Format price for display
            if 'price' in df_cars.columns:
                df_cars['price_display'] = df_cars['price'].apply(format_price)
            else:
                df_cars['price_display'] = 'N/A'
            
            # Format mileage for display
            if 'mileage' in df_cars.columns:
                df_cars['mileage_display'] = df_cars['mileage'].apply(format_mileage)
            else:
                df_cars['mileage_display'] = 'N/A'
            
            self.logger.debug(f"Prepared DataFrame with {len(df_cars)} cars")
            return df_cars
            
        except Exception as e:
            self.logger.error(f"Error preparing DataFrame: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    @staticmethod
    def get_column_config() -> Dict[str, Any]:
        """
        Get column configuration for data display.
        
        Returns:
            Dictionary of column configurations
        """
        return {
            "id": st.column_config.NumberColumn("ID", format="%d", width="small"),
            "name": st.column_config.TextColumn("Model", width="large"),
            "image_url": st.column_config.ImageColumn("Bilde", width="small"),
            "link": st.column_config.LinkColumn("Link", display_text="🔗", width="small"),
            "year": st.column_config.NumberColumn("År", format="%d"),
            "mileage": st.column_config.NumberColumn("Km", format="%d"),
            "mileage_display": st.column_config.TextColumn("Kilometere", width="small"),
            "price_display": st.column_config.TextColumn("Pris", width="small"),
            "age": st.column_config.NumberColumn("Alder", format="%d år"),
            "km_per_year": st.column_config.NumberColumn("Km/år", format="%d"),
        }
    
    @staticmethod
    def get_display_columns(df: pd.DataFrame) -> List[str]:
        """
        Get columns to display in the data editor.
        
        Args:
            df: DataFrame to get columns from
            
        Returns:
            List of column names to display
        """
        desired_columns = [
            "id", "name", "year", "mileage_display", "price_display", 
            "age", "km_per_year", "link", "image_url"
        ]
        return [col for col in desired_columns if col in df.columns]
    
    def display_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Display car statistics in columns.
        
        Args:
            stats: Statistics dictionary
        """
        try:
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                if stats.get('avg_price', 0) > 0:
                    st.metric("Gj.snitt pris", f"{stats['avg_price']:,.0f} kr")
                else:
                    st.metric("Gj.snitt pris", "N/A")
            
            with stats_col2:
                if stats.get('avg_mileage', 0) > 0:
                    st.metric("Gj.snitt km", f"{stats['avg_mileage']:,.0f}")
                else:
                    st.metric("Gj.snitt km", "N/A")
            
            with stats_col3:
                st.metric("Solgte", stats.get('sold_count', 0))

            with stats_col4:
                st.metric("Antall biler", stats.get('total_cars', 0))
            
            # Additional statistics if available
            if stats.get('price_range') and stats['price_range']['max'] > 0:
                price_range_col1, price_range_col2, mileage_range_col1, mileage_range_col2 = st.columns(4)
                
                with price_range_col1:
                    st.metric("Min pris", f"{stats['price_range']['min']:,.0f} kr")
                
                with price_range_col2:
                    st.metric("Max pris", f"{stats['price_range']['max']:,.0f} kr")
                
                if stats.get('mileage_range') and stats['mileage_range']['max'] > 0:
                    with mileage_range_col1:
                        st.metric("Min km", f"{stats['mileage_range']['min']:,.0f}")
                    
                    with mileage_range_col2:
                        st.metric("Max km", f"{stats['mileage_range']['max']:,.0f}")
                        
        except Exception as e:
            self.logger.error(f"Error displaying statistics: {str(e)}", exc_info=True)
            st.error("Feil ved visning av statistikk")