import streamlit as st
import pandas as pd
from typing import List, Dict


class CarDataDisplay:
    """Handles car data display and formatting."""
    
    @staticmethod
    def prepare_dataframe(cars_list: List[Dict]) -> pd.DataFrame:
        """Prepare and format car data for display."""
        df_cars = pd.DataFrame(cars_list)
        
        # Set index if available
        index_column_to_use = None
        if 'original_chunk_order' in df_cars.columns:
            index_column_to_use = 'original_chunk_order'
        elif 'id' in df_cars.columns:
            index_column_to_use = 'id'

        if index_column_to_use:
            df_cars = df_cars.set_index(index_column_to_use)
            df_cars.index.name = "ID"

        if 'price' in df_cars.columns:
            df_cars['price_display'] = df_cars['price'].astype(str).replace('nan', 'N/A')
        else:
            df_cars['price_display'] = 'N/A'
            
        return df_cars
    
    @staticmethod
    def get_column_config() -> Dict:
        """Get column configuration for data display."""
        return {
            "name": st.column_config.TextColumn("Model", width="large"),
            "image_url": st.column_config.ImageColumn("Bilde", width="small"),
            "link": st.column_config.LinkColumn("Link", display_text="🔗", width="small"),
            "year": st.column_config.NumberColumn("År", format="%d"),
            "mileage": st.column_config.NumberColumn("Km", format="%d"),
            "price_display": st.column_config.TextColumn("Pris", width="small"),
            "age": st.column_config.NumberColumn("Alder", format="%d år"),
            "km_per_year": st.column_config.NumberColumn("Km/år", format="%d"),
        }
    
    @staticmethod
    def get_display_columns(df: pd.DataFrame) -> List[str]:
        """Get columns to display in the data editor."""
        desired_columns = ["name", "year", "mileage", "price_display", "age", "km_per_year", "link", "image_url"]
        return [col for col in desired_columns if col in df.columns]
    
    @staticmethod
    def display_statistics(stats: Dict) -> None:
        """Display car statistics in columns."""
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            if stats['avg_price'] > 0:
                st.metric("Gj.snitt pris", f"{stats['avg_price']:,.0f} kr")
        
        with stats_col2:
            if stats['avg_mileage'] > 0:
                st.metric("Gj.snitt km", f"{stats['avg_mileage']:,.0f}")
        
        with stats_col3:
            st.metric("Solgte", stats['sold_count'])

        with stats_col4:
            st.metric("Antall biler", stats['total_cars'])