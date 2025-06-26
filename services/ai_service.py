import os
import asyncio
import json
import re
from typing import List, Dict, Optional
from openai import OpenAI
# from services.car_tools import CarTools
from dotenv import load_dotenv

load_dotenv()

class AIService:
    """Simplified AI Service without MCP overhead."""
    
    def __init__(self):
        self.model = os.getenv("AI_MODEL", "deepseek/deepseek-chat-v3-0324:free")
        self.base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        # self.car_tools = CarTools()
        self.system_message = {
            "role": "system",
            "content": (
                "Du er en ekspert bilanalytiker. Analyser bildata og gi anbefalinger på norsk. "
                "Presenter informasjon med tydelig, velstrukturert markdown. "
                "Når du anbefaler biler, nevn deres URL så kan jeg hente detaljert info. "
                "Svar direkte med analysen uten innledende fraser eller gjentagelser av data."
            )
        }
    
    def create_initial_analysis_prompt(self, parsed_cars_list: List[Dict]) -> str:
        """Create the initial analysis prompt."""
        return f"""Analyser de oppgitte bildataene og presenter dine funn.

        Strukturerte bildata:
        {json.dumps(parsed_cars_list, ensure_ascii=False, indent=2)}

        Gi følgende innsikter i et klart, strukturert format:
        1. Gjennomsnittspris på biler (ekskludert 'Solgt')
        2. Gjennomsnittlig kilometerstand
        3. Gjennomsnittlig alder på biler
        4. Gjennomsnittlig km per år
        5. Antall biler merket som 'Solgt'

        Etter å ha presentert disse innsiktene, identifiser 3-5 biler som ser lovende ut for kjøp basert på:
        - God verdi (vurdering av pris vs. alder/kilometerstand)
        - Lav km/år (biler med mindre enn 15 000 km/år regnes som lav kjørelengde)
        - Generell appell basert på kunnskap om bilmodeller

        For hver lovende bil du identifiserer, nevn URL-en så jeg kan hente detaljert informasjon.

        Begrunn valgene dine, og gi anbefalinger basert på bilens tilstand, utstyr og pris, samt eventuelle heftelser.
        Gi også anbefalinger for hvilke biler som kan være gode kjøp basert på deres spesifikasjoner og tilstand.
        Skriv på norsk, bruk klare overskrifter og punktlister der det er relevant.

        VIKTIG: Bruk dine bilkunnskaper for å vurdere hvilke biler som er best egnet for kjøp.
        VIKTIG: Svaret ditt skal kun bestå av de forespurte innsiktene og anbefalingene."""
    
    async def get_ai_response_with_tools(self, messages: List[Dict]) -> str:
        """Get AI response and automatically enhance with detailed car info."""
        try:
            # Get initial AI response
            # Convert messages to the format expected by OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    }
                    for msg in messages if msg.get("role") in ["system", "user", "assistant"]
                ],
                temperature=0.1,
                max_tokens=4000,
                timeout=60
            )
            
            ai_response = response.choices[0].message.content
            
            if ai_response is None:
                return "Ingen respons fra AI"
            return ai_response
            # Check if AI mentioned car URLs and enhance response
            # enhanced_response = await self._enhance_response_with_car_details(ai_response)
            
            # return enhanced_response
            
        except Exception as e:
            return f"Feil ved AI-analyse: {str(e)}"
    
    # async def _enhance_response_with_car_details(self, ai_response: str) -> str:
    #     """Automatically fetch detailed info for cars mentioned in AI response."""
    #     # Extract Finn.no URLs from AI response
    #     url_pattern = r'https://www\.finn\.no/mobility/item/\d+'
    #     urls = re.findall(url_pattern, ai_response)
    #     print(f"Fant {len(urls)} bil-URLer i AI-svaret.")
    #     print(f"URLer: {urls}")
        
    #     if not urls:
    #         return ai_response
        
    #     # Fetch detailed info for each URL (limit to 3 to avoid delays)
    #     enhanced_sections = []
    #     for i, url in enumerate(urls[:3]):
    #         print(f"Henter detaljert info for bil {i+1}/{min(len(urls), 3)}...")
    #         car_details = await self.car_tools.fetch_detailed_car_info(url)
            
    #         if "error" not in car_details:
    #             # Format the detailed info nicely
    #             detail_text = self._format_car_details(car_details)
    #             enhanced_sections.append(f"\n### 🚗 Detaljert info for {url}\n{detail_text}")
    #         else:
    #             enhanced_sections.append(f"\n### ❌ Kunne ikke hente info for {url}\n{car_details.get('error', 'Ukjent feil')}")
        
    #     if enhanced_sections:
    #         return ai_response + "\n\n---\n## 📋 DETALJERT BILINFO\n" + "\n".join(enhanced_sections)
        
    #     return ai_response
    
    # def _format_car_details(self, car_details: Dict) -> str:
    #     """Format car details into readable markdown."""
    #     formatted = []
        
    #     # Title
    #     if car_details.get("title"):
    #         formatted.append(f"**Tittel:** {car_details['title']}")
        
    #     # Description - mer meningsfull utdrag
    #     if car_details.get("description"):
    #         desc = car_details['description']
    #         # Fjern omregistrering tekst hvis det starter med det
    #         if desc.lower().startswith('omregistrering'):
    #             # Finn første setning etter omregistrering info
    #             sentences = desc.split('.')
    #             meaningful_desc = ""
    #             for sentence in sentences[1:]:
    #                 if len(sentence.strip()) > 20:
    #                     meaningful_desc = sentence.strip()
    #                     break
    #             if meaningful_desc:
    #                 formatted.append(f"**Beskrivelse:** {meaningful_desc[:150]}...")
    #         else:
    #             formatted.append(f"**Beskrivelse:** {desc[:150]}...")
        
    #     # Specifications - vis de viktigste
    #     if car_details.get("specifications"):
    #         specs = car_details["specifications"]
    #         important_specs = []
            
    #         # Prioriter viktige spesifikasjoner
    #         priority_keys = [
    #             'årsmodell', 'kilometer', 'drivstoff', 'motor', 'effekt', 
    #             'girkasse', 'hjuldrift', 'registreringsnummer'
    #         ]
            
    #         for key in priority_keys:
    #             for spec_key, spec_value in specs.items():
    #                 if key.lower() in spec_key.lower():
    #                     important_specs.append(f"{spec_key}: {spec_value}")
    #                     break
            
    #         # Legg til andre specs hvis vi ikke har nok
    #         if len(important_specs) < 3:
    #             for spec_key, spec_value in specs.items():
    #                 if f"{spec_key}: {spec_value}" not in important_specs:
    #                     important_specs.append(f"{spec_key}: {spec_value}")
    #                 if len(important_specs) >= 5:
    #                     break
            
    #         if important_specs:
    #             formatted.append(f"**Spesifikasjoner:**\n" + "\n".join(f"  • {spec}" for spec in important_specs[:5]))
        
    #     # Equipment - vis de viktigste
    #     if car_details.get("equipment") and len(car_details["equipment"]) > 0:
    #         equipment = car_details["equipment"]
    #         if len(equipment) <= 5:
    #             formatted.append(f"**Utstyr:** {', '.join(equipment)}")
    #         else:
    #             # Vis de 5 første og antall resterende
    #             equipment_preview = ', '.join(equipment[:5])
    #             formatted.append(f"**Utstyr:** {equipment_preview} (+{len(equipment) - 5} flere)")
        
    #     # Heftelser info - meget viktig for kjøpere
    #     if car_details.get("heftelser_info"):
    #         heftelser = car_details["heftelser_info"]
    #         if heftelser.get("status") == "ingen_heftelser":
    #             formatted.append(f"**🟢 Heftelser:** Ingen registrerte heftelser")
    #         elif heftelser.get("has_heftelser") == False:
    #             formatted.append(f"**🟢 Heftelser:** Ingen heftelser funnet")
    #         elif heftelser.get("has_heftelser") == True:
    #             heftelser_text = "**🔴 Heftelser:** Ja"
    #             if heftelser.get("belop"):
    #                 heftelser_text += f" - Beløp: {heftelser['belop']}"
    #             if heftelser.get("pantsettere"):
    #                 heftelser_text += f" - Pantsettere: {', '.join(heftelser['pantsettere'])}"
    #             formatted.append(heftelser_text)
    #         elif heftelser.get("error"):
    #             formatted.append(f"**⚠️ Heftelser:** Kunne ikke sjekke - {heftelser['error']}")
        
    #     # Success status
    #     if not car_details.get("success", True):
    #         formatted.append(f"**⚠️ Status:** Noe data mangler")
        
    #     return "\n".join(formatted) if formatted else "Ingen detaljert informasjon tilgjengelig."
    