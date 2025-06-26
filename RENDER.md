# Render.com Deployment Guide for FinnBil

## 🚀 Deploying til Render.com

### Steg 1: Forbered prosjektet
1. Push koden til GitHub/GitLab
2. Sørg for at Dockerfile er i root-mappen

### Steg 2: Opprett Web Service på Render.com
1. Gå til [Render.com](https://render.com) dashboard
2. Klikk "New +" → "Web Service"
3. Koble til ditt GitHub repository
4. Velg repository: `FinnBil`

### Steg 3: Konfigurer deployment
**Build Settings:**
- **Environment**: `Docker`
- **Build Command**: (la stå tom - Render bruker Dockerfile automatisk)
- **Start Command**: (la stå tom - Render bruker CMD fra Dockerfile)

**Service Details:**
- **Name**: `finnbil-analyzer`
- **Region**: `Frankfurt` (nærmest Norge)
- **Branch**: `main` (eller din standard branch)
- **Auto-Deploy**: `Yes`

### Steg 4: Sett Environment Variables
I Render dashboard under "Environment":
```
OPENROUTER_API_KEY = your_openrouter_api_key_here
AI_MODEL = deepseek/deepseek-chat-v3-0324:free
AI_BASE_URL = https://openrouter.ai/api/v1
```

**Hvor få API-nøkkel:**
- Gå til [OpenRouter.ai](https://openrouter.ai/)
- Registrer deg og få din egen API-nøkkel
- Erstatt `your_openrouter_api_key_here` med din faktiske nøkkel

**Alternative modeller du kan prøve:**
- `anthropic/claude-3-sonnet` (bedre kvalitet, dyrere)
- `openai/gpt-4` (OpenAI sin flaggskip)
- `google/gemini-pro` (Google sin modell)
- `meta-llama/llama-3-70b-instruct` (Open source alternativ)

### Steg 5: Deploy
- Klikk "Create Web Service"
- Render vil automatisk bygge og deploye appen
- URL vil være: `https://finnbil-analyzer.onrender.com`

## 🔧 Forskjeller for Render.com

### Ikke nødvendig:
- ❌ `docker-compose.yaml` (Render bruker kun Dockerfile)
- ❌ `.env` fil i produksjon (Render håndterer miljøvariabler)
- ❌ Port mapping (Render håndterer dette automatisk)

### Kun for lokal utvikling:
- ✅ `docker-compose.yaml` for lokal testing
- ✅ `.env` fil lokalt

## 📊 Render.com konfigurasjon

**Plan**: Free tier (512MB RAM, sleeps after 15 min inaktivitet)  
**Port**: 8501 (automatisk detektert fra Dockerfile)  
**Health checks**: Automatisk fra HEALTHCHECK i Dockerfile  
**Logs**: Tilgjengelig i Render dashboard  

## 🔄 Auto-deployment

Hver gang du pusher til main branch, vil Render automatisk:
1. Bygge ny Docker image
2. Deploye oppdatert versjon
3. Kjøre health checks

## 💡 Tips for Render.com

1. **Startup tid**: Første deployment kan ta 5-10 minutter
2. **Sleep mode**: Free tier "sover" etter 15 min - første request tar lengre tid
3. **Persistent storage**: Render har ikke persistent disk på free tier
4. **Logs**: Overvåk deployment i Render dashboard

## 🛠️ Troubleshooting

**Problem**: App starter ikke
- **Løsning**: Sjekk logs i Render dashboard

**Problem**: Environment variables ikke tilgjengelig
- **Løsning**: Verifiser at OPENROUTER_API_KEY er satt i Render dashboard

**Problem**: Slow startup
- **Løsning**: Normal for free tier - vurder paid plan for faster startup
