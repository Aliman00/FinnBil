import asyncio
import json
import os
from typing import List, Dict, Optional

from openai import OpenAI
from dotenv import load_dotenv

from config.settings import settings
from services.simple_car_analyzer import car_analyzer
from utils.exceptions import AIServiceError, ConfigurationError
from utils.logging import logger

load_dotenv()


class AIService:
    """AI Service for car analysis and recommendations."""
    
    def __init__(self):
        """Initialize AI service with configuration."""
        try:
            # Validate configuration
            if not settings.ai.api_key:
                raise ConfigurationError("OpenRouter API key is not configured")
            
            self.client = OpenAI(
                base_url=settings.ai.base_url,
                api_key=settings.ai.api_key
            )
            self.model = settings.ai.model
            self.timeout = settings.ai.timeout
            self.car_analyzer = car_analyzer
            
            # Initialize system message
            self.system_message = self._create_system_message()
            
            logger.info(f"AI Service initialized with model: {self.model}")
            
        except Exception as e:
            error_msg = f"Failed to initialize AI service: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(error_msg)
    
    def _create_system_message(self) -> Dict[str, str]:
        """Create the system message for AI interactions."""
        return {
            "role": "system",
            "content": (
                "Du er en senior bilanalytiker og kjøpsrådgiver med 15+ års erfaring fra norsk bilbransje. "
                "Du har tilgang til avansert verdifall-analyse basert på SmartePenger.no industristandarder og historiske RAV4 nybilpriser (2019-2024). "
                "\nVIKTIG - BRUKTBILMARKED ANALYSE:"
                "• Alle biler på Finn.no var opprinnelig kjøpt nye (bruk SmartePenger 'ny bil' verdifall)"
                "• HØYERE verdifall enn forventet = BEDRE KJØP (bilen har tapt MER verdi = BILLIGERE for deg)"
                "• LAVERE verdifall enn forventet = DÅRLIGERE KJØP (bilen har tapt MINDRE verdi = DYRERE for deg)"
                "• KRITISK: Hvis forskjellen er NEGATIV (-18.6%) = bilen har tapt MINDRE verdi = OVERPRISET"
                "• KRITISK: Hvis forskjellen er POSITIV (+15.0%) = bilen har tapt MER verdi = UNDERPRISET"
                "• Eksempel: 50% faktisk vs 40% forventet = +10% forskjell = bilen er BILLIGERE enn forventet = BRA KJØP"
                "• Eksempel: 30% faktisk vs 40% forventet = -10% forskjell = bilen er DYRERE enn forventet = DÅRLIG KJØP"
                "• LAVERE kilometerstand = BEDRE KJØP (mindre slitasje)"
                "• HØYERE kilometerstand = DÅRLIGERE KJØP (mer slitasje)"
                "• Forventet verdifall: 20% år 1, 14% år 2, 13% år 3, osv."
                "• VIKTIG: Totalkarakter kombinerer pris (50%), kjørelengde (40%) og trim-nivå (10%)"
                "• Trim-nivåer: Executive > Style > Active > Life (høyere nivå gir fordel ved like biler)"
                "• Executive gir fordel ved tilsvarende pris/km, men dårlig pris/høy km veier tyngre"
                "• Biler med F i kjørelengde (>25k km/år) kan MAKS få C totalkarakter"
                "• Biler med D i kjørelengde (20-25k km/år) kan MAKS få B totalkarakter"
                "• Kun biler med A-C kjørelengde kan få A totalkarakter"
                "\nDin specialitet:"
                "• Analysere bruktbilmarkedet med SmartePenger 'ny bil' verdifallsmodell (alle biler startet som nye)"
                "• Finne underprisede biler: Biler hvor faktisk verdifall er HØYERE enn SmartePenger-forventet"
                "• EKSEMPEL UNDERPRISET: 55% faktisk vs 47% forventet = +8% forskjell = BILLIGERE = ANBEFAL"
                "• EKSEMPEL OVERPRISET: 35% faktisk vs 47% forventet = -12% forskjell = DYRERE = UNNGÅ"
                "• Prioritere lav kilometerstand: Under 11k km/år = Utmerket, 11-15k = Bra, 15-20k = Greit, over 20k = Dårlig"
                "• A-karakter kun for biler med både god pris OG akseptabel kjørelengde"
                "• Ekstrem kjørelengde (>25k km/år) begrenser totalkarakter til maks C"
                "• Identifisere overprisede biler (lavere verdifall enn forventet) vs underprisede (høyere verdifall)"
                "• Gi spesifikke kjøps/unngå-anbefalinger der A/B = kjøp, D/F = unngå"
                "• Verdi-score analyse (0-100) hvor høy score = god kjøpsmulighet"
                "\nSkrivestil:"
                "• Forklar tydelig at høyere verdifall = bedre pris for kjøper"
                "• Ranger anbefalinger basert på verdiscore der høy score = god deal"
                "• Gi KONKRETE grunner med 'høyere/lavere verdifall enn forventet = billigere/dyrere'"
                "• Inkluder alltid Finn.no URL for anbefalte biler"
                "\nSvar KUN på norsk og følg promptstrukturen nøyaktig."
            )
        }
    
    def create_initial_analysis_prompt(self, parsed_cars_list: List[Dict]) -> str:
        """Create the initial analysis prompt with simple car analysis."""
        
        # Get simple analysis for all cars
        analysis_summary = self.car_analyzer.analyze_multiple_cars(parsed_cars_list)
        
        # Prepare enhanced data with simple analysis
        enhanced_analysis = ""
        if analysis_summary and analysis_summary.get('all_analyses'):
            enhanced_analysis = "\n\n📊 BILANALYSE (SmartePenger.no standarder):\n"
            
            for analysis in analysis_summary['all_analyses'][:10]:  # Top 10 for brevity
                car = analysis['car_info']
                price = analysis['price_analysis']
                mileage = analysis['mileage_analysis']
                
                enhanced_analysis += f"""
                🚗 {car['name']} ({car['year']}) - Totalkarakter: {analysis['grade']} (Pris: {price['grade']}, Km: {mileage['grade']}, Utstyr: {analysis['equipment_analysis']['grade']})
                • Markedspris: {car['current_price']:,} kr
                • Nybilpris: {price['original_price']:,} kr
                • Faktisk verdifall: {price['actual_depreciation_percent']:.1f}%
                • Forventet verdifall: {price['expected_depreciation_percent']:.1f}%
                • Verdifallssammenligning: {price['depreciation_difference']:+.1f}% ({'BILLIGERE enn forventet (bra for kjøper)' if price['depreciation_difference'] > 0 else 'DYRERE enn forventet (dårlig for kjøper)'})
                • Kjørelengde: {car['km_per_year']:,} km/år ({mileage['assessment']})
                • Utstyrsnivå: {analysis['equipment_analysis']['level']} ({analysis['equipment_analysis']['assessment']})
                • Anbefaling: {analysis['recommendation']}
                """

        base_prompt = f"""Du er en senior bilanalytiker med 15+ års erfaring fra bilbransjen. Analyser disse RAV4-ene som en profesjonell kjøpsrådgiver.

            STRUKTURERTE BILDATA:
            {json.dumps(parsed_cars_list, ensure_ascii=False, indent=2)}

            {enhanced_analysis}

            📈 ANALYSESAMMENDRAG (SmartePenger.no standarder):
            • Analysert: {analysis_summary.get('total_cars', 0)} biler
            • Karakterfordeling: A:{analysis_summary.get('grade_distribution', {}).get('A', 0)} B:{analysis_summary.get('grade_distribution', {}).get('B', 0)} C:{analysis_summary.get('grade_distribution', {}).get('C', 0)} D:{analysis_summary.get('grade_distribution', {}).get('D', 0)} F:{analysis_summary.get('grade_distribution', {}).get('F', 0)}
            • Anbefalte biler (A-B): {analysis_summary.get('good_deals', 0)}/{analysis_summary.get('total_cars', 0)}

            ## 🎯 TOPP 5 KJØPSANBEFALINGER

            Ranger de 5 BESTE bilene basert på SmartePenger verdifallsanalyse. HUSK: Høyere faktisk verdifall enn forventet = billigere bil = bedre kjøp!
            
            **PRIORITERING (viktigst først):**
            1. **Kjørelengde** (40%) - Lav km/år er viktigst for langsiktig verdi
            2. **Pris/verdifall** (50%) - Sammenlign med forventet markedsverdi  
            3. **Trim-nivå** (10%) - Executive > Style > Active > Life som faktisk nevnes i annonsen
            
            **VED TETT KONKURRANSE:** Hvis to biler har lik pris og kilometerstand, velg Executive over Active over Life basert på det som faktisk står i annonsen.
            
            Du skal gi KONKRETE grunner til hvorfor hver bil er et godt kjøp, basert på verdifall og kilometerstand og du skal se dette som en mulighet til å gi kjøpsråd til potensielle kjøpere.
            DU SKAL gi det absolutte beste rådet for hver bil, om du er usikker på hva som er best, så skal du gi det beste rådet du kan basert på de dataene du har og gjerne tenke deg om 2-3 ganger før du gir rådet.

            **[RANG #X] - [Bilnavn og år] - Karakter: [A-F] - Pris: [] - Kilometerstand: [] - ID: []**
            - 💰 **Pris vs. industri**: [Sammenlign med SmartePenger forventet verdifall]
            - 📉 **Kjøpsanalyse**: [VIKTIG: Hvis faktisk verdifall > forventet = billigere = bra. Hvis faktisk < forventet = dyrere = dårlig]
            - 🚗 **Kilometerstand**: [Under 11k km/år = Utmerket, 11-15k = Bra, 15-20k = Greit, over 20k = Dårlig]
            - 🎛️ **Trim-nivå**: [Executive/Style/Active/Life - hvor Executive er toppmodell og Life grunnmodell]
            - ⚡ **Kjøpsargument**: [Ved like pris/km - fremhev trim-nivå som avgjørende faktor, Executive > Style > Active > Life]
            - ⚠️ **Risikofaktorer**: [Potensielle problemer/bekymringer. Utdyp hva er det som en potensiell kjøper bør være oppmerksom på]
            - 🔗 **URL**: [Finn.no lenke]
            - 🏆 **Kjøpsanbefaling**: [Basert på SmartePenger-analyse fra kjøpers perspektiv]

            EKSEMPEL PÅ RIKTIG TOLKNING:
            - 50% faktisk vs 40% forventet = +10% høyere verdifall = billigere bil = BRA for kjøper
            - 30% faktisk vs 40% forventet = -10% lavere verdifall = dyrere bil = DÅRLIG for kjøper

            ## 📊 MARKEDSANALYSE

            ### Prissegmenter:
            - **Budget (under 300k)**: [Antall biler og verdifallsanalyse]
            - **Mellomklasse (300-450k)**: [Antall biler og vurdering]  
            - **Premium (over 450k)**: [Antall biler og vurdering]

            ### Avvik fra forventet verdifall:
            - **Overprised** (høyere enn forventet): [Liste med begrunnelse]
            - **Underpriced** (lavere enn forventet): [Liste med begrunnelse]

            ### Solgte biler-analyse:
            [Analyser soldier biler: pris, km-stand, årsaker til salg]

            ## ⚠️ BILER Å UNNGÅ

            List 2-3 biler du IKKE ville anbefalt med konkrete grunner:
            - **[Bilnavn]**: [Spesifikk grunn - høy pris, høy km-stand, dårlig verdifall etc.]

            ## 📊 MARKED-INSIGHTS

            ### Generelle trender:
            - Hvilke årsmodeller gir best value?
            - Optimal km-stand for beste pris/verdi-forhold?
            - Sesongeffekter eller markedstrender?

            ### Forhandlingstips:
            - Hvilke biler har vært lenge til salgs? (potensial for prutearr)
            - Prisargumenter basert på verdifall-data

            ## 🎯 KONKLUSJON

            **TL;DR for travle kjøpere:**
            1. **Best buy**: [Bil + pris + hovedgrunn]
            2. **Best value**: [Bil + pris + hovedgrunn]  
            3. **Avoid**: [Bil + hovedgrunn]

            **Generell markedsvurdering**: [Er det kjøpers eller selgers marked?]

            KRITISK: Vær spesifikk, bruk tallene fra verdifall-analysen, og gi KONKRETE kjøpsråd med URL-er. Ingen generelle fraser - kun actionable insights!"""
        
        return base_prompt
    
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
    