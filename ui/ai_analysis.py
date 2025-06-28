"""
AI analysis component for FinnBil webapp.
"""
import streamlit as st
import asyncio
from typing import List, Dict

from utils.logging import logger


class AIAnalysisComponent:
    """Handles AI analysis section rendering and chat interface."""
    
    def __init__(self):
        self.logger = logger
    
    def render(self) -> None:
        """Render the complete AI analysis section."""
        if not st.session_state.parsed_cars_list:
            return
        
        st.header("🤖 AI Analyse")
        
        # Start analysis button
        if not st.session_state.initial_analysis_done:
            if st.button("🚀 Start AI Analyse", type="primary"):
                self._start_ai_analysis()
        
        # Show chat interface if analysis has started
        if st.session_state.messages:
            self._render_chat_interface()
    
    def _start_ai_analysis(self) -> None:
        """Start the initial AI analysis."""
        if not (st.session_state.parsed_cars_list and st.session_state.raw_car_data_text):
            st.warning("Kan ikke starte AI analyse. Sørg for at data er hentet og parset.")
            return

        # Reset chat state
        st.session_state.messages = [st.session_state.ai_service.system_message]
        st.session_state.initial_analysis_done = False

        # Create and add initial prompt
        try:
            initial_prompt = st.session_state.ai_service.create_initial_analysis_prompt(
                st.session_state.parsed_cars_list
            )
            st.session_state.messages.append({
                "role": "user",
                "content": initial_prompt,
                "is_hidden_prompt": "True"
            })

            with st.spinner("🔍 AI utfører dybdeanalyse med ekstra bildata... Dette kan ta litt tid..."):
                self._get_ai_response()
                
        except Exception as e:
            error_msg = f"Feil under AI analyse: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
    
    def _get_ai_response(self) -> None:
        """Get AI response for current messages."""
        try:
            # Prepare messages for AI (exclude hidden prompts for conversation flow)
            ai_messages = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
            
            # Get AI response with automatic tool enhancement
            ai_response = asyncio.run(
                st.session_state.ai_service.get_ai_response_with_tools(ai_messages)
            )
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.session_state.initial_analysis_done = True
            self.logger.info("AI analysis completed successfully")
            st.rerun()
            
        except Exception as e:
            error_msg = f"Feil under AI kommunikasjon: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            st.error(error_msg)
    
    def _render_chat_interface(self) -> None:
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
            self._handle_user_message(prompt)
    
    def _handle_user_message(self, prompt: str) -> None:
        """Handle user message input."""
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("AI svarer..."):
                try:
                    # Prepare messages for AI (exclude hidden prompts)
                    ai_messages = [
                        {"role": m["role"], "content": m["content"]} 
                        for m in st.session_state.messages 
                        if not m.get("is_hidden_prompt")
                    ]
                    
                    ai_response = asyncio.run(
                        st.session_state.ai_service.get_ai_response_with_tools(ai_messages)
                    )
                    
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    self.logger.debug(f"AI responded to user query: {prompt[:50]}...")
                    
                except Exception as e:
                    error_msg = f"Beklager, jeg kunne ikke behandle forespørselen din: {str(e)}"
                    self.logger.error(f"AI response error: {str(e)}", exc_info=True)
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
