import streamlit as st
import asyncio
import urllib.parse
import time
import random
from typing import List, Dict
from services.data_service import DataService
from services.ai_service import AIService
from services.price_analysis_service import PriceAnalysisService
from ui.car_display import CarDataDisplay

# Configuration
DEFAULT_FINN_URL = "https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"


def is_valid_finn_url(url: str) -> bool:
    """Validate that URL is from finn.no and properly formatted."""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        
        # Check if it's a finn.no domain
        if not parsed.netloc.lower() in ['finn.no', 'www.finn.no']:
            return False
        
        # Check if it's using HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check if it's a car search URL
        if not parsed.path.startswith('/mobility/'):
            return False
            
        return True
    except Exception:
        return False


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'raw_car_data_text' not in st.session_state:
        st.session_state.raw_car_data_text = None
    if 'parsed_cars_list' not in st.session_state:
        st.session_state.parsed_cars_list = []
    if 'current_finn_url' not in st.session_state:
        st.session_state.current_finn_url = DEFAULT_FINN_URL
    if 'finn_urls' not in st.session_state:
        # Start with default URL, but allow user to delete it completely
        st.session_state.finn_urls = [DEFAULT_FINN_URL]
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


def render_sidebar():
    """Render the sidebar with URL input and fetch controls."""
    st.sidebar.title("🚗 FinnBil Analyzer")
    st.sidebar.markdown("---")
    
    # URL management section
    st.sidebar.subheader("📋 URL-er")
    
    # Check if there are any URLs to display
    if not st.session_state.finn_urls:
        st.sidebar.info("Ingen URL-er lagt til ennå")
        # Add button to restore default URL
        if st.sidebar.button("➕ Legg til standard søke-URL", help="Legger til standard Finn.no søk"):
            st.session_state.finn_urls.append(DEFAULT_FINN_URL)
            st.sidebar.success("✅ Standard URL lagt til")
            st.rerun()
    else:
        # Display existing URLs with delete buttons
        for i, url in enumerate(st.session_state.finn_urls):
            col1, col2 = st.sidebar.columns([4, 1])
            
            with col1:
                if url.strip():
                    # Truncate URL for display
                    display_url = url[:50] + "..." if len(url) > 50 else url
                    st.text(f"{i+1}. {display_url}")
                else:
                    st.text(f"{i+1}. (tom URL)")
            
            with col2:
                if st.button("🗑️", key=f"delete_{i}", help="Slett denne URL-en"):
                    st.session_state.finn_urls.pop(i)
                    # Don't add empty placeholder - let the list be empty if needed
                    st.rerun()
    
    # Add new URL section
    st.sidebar.markdown("---")
    
    # Input for new URL
    new_url = st.sidebar.text_area(
        "Legg til ny URL:",
        height=100,
        help="Lim inn URL fra Finn.no bilsøk (kun finn.no URLer tillatt)",
        placeholder="https://www.finn.no/mobility/search/car?...",
        max_chars=1000  # Limit URL length for security
    )
    
    # Add URL button with plus icon
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        if st.button("➕ Legg til URL", disabled=not new_url.strip()):
            if not new_url.strip():
                st.sidebar.error("URL kan ikke være tom")
            elif not is_valid_finn_url(new_url.strip()):
                st.sidebar.error("❌ Kun gyldige Finn.no bil-søk URLer er tillatt")
            elif new_url.strip() in st.session_state.finn_urls:
                st.sidebar.warning("URL finnes allerede")
            else:
                st.session_state.finn_urls.append(new_url.strip())
                st.sidebar.success("✅ URL lagt til")
                st.rerun()
    
    st.sidebar.markdown("---")
    
    # Fetch button
    if st.sidebar.button("🔄 Hent og analyser alle URL-er", type="primary"):
        fetch_new_data()
    
    # Show current data status
    if st.session_state.parsed_cars_list:
        valid_url_count = len([url for url in st.session_state.finn_urls if url.strip()])
        st.sidebar.text("")
        st.sidebar.success(f"✅ {len(st.session_state.parsed_cars_list)} biler lastet fra {valid_url_count} URL-er")
    
    # Cache status and management
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗄️ Cache Status")
    
    try:
        from services.price_analysis_service import PriceAnalysisService
        
        # Check if cache exists
        if hasattr(PriceAnalysisService, '_instance') and PriceAnalysisService._instance is not None:
            instance = PriceAnalysisService.get_instance()
            record_count = len(instance.rav4_data) if instance.rav4_data is not None else 0
            st.sidebar.info(f"📊 {record_count} RAV4 priser cached")
            
            # Cache reset button
            if st.sidebar.button("🔄 Reset price cache", help="Laster RAV4 prisdata på nytt"):
                PriceAnalysisService.reset_cache()
                st.sidebar.success("✅ Cache tilbakestilt")
                st.rerun()
        else:
            st.sidebar.info("📊 Ingen prisdata cached ennå")
            
    except Exception as e:
        st.sidebar.warning(f"⚠️ Cache status ikke tilgjengelig: {str(e)[:50]}...")
    
    # Cache status and management section
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗄️ Cache Status")
    
    # Get cache status from PriceAnalysisService
    price_service = PriceAnalysisService.get_instance() # type: ignore
    
    if price_service.rav4_data is not None and len(price_service.rav4_data) > 0:
        st.sidebar.success(f"✅ RAV4 data: {len(price_service.rav4_data)} records cached")
    else:
        st.sidebar.warning("⚠️ RAV4 price data not loaded")
    
    # Reset cache button
    if st.sidebar.button("🗑️ Reset Cache", help="Tilbakestill alle cachede data og last dem på nytt"):
        try:
            # Clear Streamlit cache
            st.cache_data.clear()
            
            # Reset PriceAnalysisService singleton
            PriceAnalysisService.reset_cache() # type: ignore
            
            # Reinitialize AI service with fresh cache
            st.session_state.ai_service = AIService()
            
            st.sidebar.success("✅ Cache tilbakestilt!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Feil ved tilbakestilling: {e}")


def fetch_new_data():
    """Fetch new data from all Finn.no URLs and reset analysis state."""
    # Filter out empty URLs and validate them
    valid_urls = []
    for url in st.session_state.finn_urls:
        if url.strip():
            if is_valid_finn_url(url.strip()):
                valid_urls.append(url.strip())
            else:
                st.sidebar.error(f"❌ Ugyldig URL: {url[:50]}...")

    if not valid_urls:
        st.sidebar.error("❌ Ingen gyldige URL-er å hente fra")
        return
    
    # Reset all state
    st.session_state.raw_car_data_text = None
    st.session_state.parsed_cars_list = []
    st.session_state.messages = []
    st.session_state.initial_analysis_done = False
    
    with st.sidebar.status("Henter bildata...", expanded=True) as status:
        st.write(f"Kobler til Finn.no... ({len(valid_urls)} URL-er)")
        
        all_parsed_cars = []
        all_raw_data = []
        total_urls = len(valid_urls)
        
        try:
            for i, url in enumerate(valid_urls, 1):
                st.write(f"Henter fra URL {i}/{total_urls}...")
                
                # Additional rate limiting between URL requests
                if i > 1:
                    delay = random.uniform(3, 6)  # 3-6 seconds between different URLs
                    time.sleep(delay)  # Use time.sleep instead of await in sync function
                
                # Fetch data from current URL
                success, error_msg, parsed_cars, raw_json = asyncio.run(
                    st.session_state.data_service.fetch_and_parse_cars(url)
                )
                
                if success:
                    all_parsed_cars.extend(parsed_cars)
                    all_raw_data.append(raw_json)
                    st.write(f"✅ URL {i}: {len(parsed_cars)} biler")
                else:
                    st.write(f"❌ URL {i}: {error_msg}")
            
            if all_parsed_cars:
                st.session_state.parsed_cars_list = all_parsed_cars
                st.session_state.raw_car_data_text = "\n\n".join(all_raw_data)
                
                # Save to file
                st.session_state.data_service.save_data_to_file(all_parsed_cars)
                
                st.write(f"✅ Totalt hentet {len(all_parsed_cars)} biler")
                status.update(label="Data hentet!", state="complete", expanded=False)
                st.sidebar.success(f"✅ {len(all_parsed_cars)} biler hentet fra {total_urls} URL-er")
                st.rerun()
            else:
                status.update(label="Ingen data hentet", state="error", expanded=False)
                st.sidebar.error("❌ Ingen bildata ble hentet fra noen av URL-ene")
                
        except Exception as e:
            status.update(label="Feil oppstod", state="error", expanded=False)
            st.sidebar.error(f"❌ Feil: {str(e)}")


def render_car_data():
    """Render the car data table and statistics."""
    if not st.session_state.parsed_cars_list:
        st.info("👈 Bruk sidepanelet for å hente bildata fra Finn.no")
        return
    
    st.header("📊 Bildata 🚗")
    
    # Display car table
    df = st.session_state.car_display.prepare_dataframe(st.session_state.parsed_cars_list)
    
    if not df.empty:        
        # Show data table with custom column order
        # st.subheader("🚗 Biltabell")
        
        # ✅ NOW USING get_display_columns!
        display_columns = st.session_state.car_display.get_display_columns(df)
        
        st.data_editor(
            df[display_columns],  # ← This will show columns in correct order
            use_container_width=True,
            hide_index=True,
            column_config=st.session_state.car_display.get_column_config(),
            disabled=True,
            height=400
        )
        
        st.markdown("---")
        # Debug info (optional - remove later)
        # st.write(f"**Debug:** Viser kolonner: {', '.join(display_columns)}")

        # Show statistics
        stats = st.session_state.data_service.calculate_statistics(st.session_state.parsed_cars_list)
        
        # Display improved statistics
        st.session_state.car_display.display_statistics(stats)
        st.markdown("---")
        
    else:
        st.warning("Ingen bildata å vise")


def render_ai_analysis():
    """Render the AI analysis section."""
    if not st.session_state.parsed_cars_list:
        return
    
    st.header("🤖 AI Analyse")
    
    # Start analysis button
    if not st.session_state.initial_analysis_done:
        if st.button("🚀 Start AI Analyse", type="primary"):
            start_ai_analysis()
    
    # Show chat interface if analysis has started
    if st.session_state.messages:
        render_chat_interface()


def start_ai_analysis():
    """Start the initial AI analysis."""
    if not (st.session_state.parsed_cars_list and st.session_state.raw_car_data_text):
        st.warning("Kan ikke starte AI analyse. Sørg for at data er hentet og parset.")
        return

    # Reset chat state
    st.session_state.messages = [st.session_state.ai_service.system_message]
    st.session_state.initial_analysis_done = False

    # Create and add initial prompt
    initial_prompt = st.session_state.ai_service.create_initial_analysis_prompt(st.session_state.parsed_cars_list)
    st.session_state.messages.append({
        "role": "user",
        "content": initial_prompt,
        "is_hidden_prompt": "True"
    })

    with st.spinner("🔍 AI utfører dybdeanalyse med ekstra bildata... Dette kan ta litt tid..."):
        try:
            # Get AI response with automatic tool enhancement
            ai_response = asyncio.run(st.session_state.ai_service.get_ai_response_with_tools(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ))
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.session_state.initial_analysis_done = True
            st.rerun()
            
        except Exception as e:
            st.error(f"Feil under AI analyse: {e}")


def render_chat_interface():
    """Render the chat interface for continued AI interaction."""
    st.subheader("💬 Chat med AI")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue  # Skip system message
        
        if message["role"] == "user" and message.get("is_hidden_prompt"):
            continue  # Skip hidden initial prompt
        
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Still et spørsmål om bilene..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("AI svarer..."):
                try:
                    ai_response = asyncio.run(st.session_state.ai_service.get_ai_response_with_tools(
                        [{"role": m["role"], "content": m["content"]} 
                         for m in st.session_state.messages if not m.get("is_hidden_prompt")]
                    ))
                    
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = f"Beklager, jeg kunne ikke behandle forespørselen din: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


def main():
    """Main application function."""
    st.set_page_config(
        page_title="FinnBil Analyzer",
        page_icon="🚗",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Layout: sidebar + main content
    render_sidebar()
    
    # Main content
    render_car_data()
    render_ai_analysis()


if __name__ == "__main__":
    main()