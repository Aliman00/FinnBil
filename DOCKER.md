# FinnBil Docker Setup

Dette er Docker-konfigurasjonen for FinnBil Analyzer applikasjonen.

## 🚀 Hvordan kjøre applikasjonen

### Forutsetninger
- Docker og Docker Compose installert
- `.env` fil med `OPENROUTER_API_KEY` (få din egen på openrouter.ai)

### Bygg og kjør med Docker Compose
```bash
# Bygg og start containeren
docker-compose up --build

# Kjør i bakgrunnen
docker-compose up -d --build

# Stopp containeren
docker-compose down

# Se logger
docker-compose logs -f
```

### Manuell Docker bygging
```bash
# Bygg image
docker build -t finnbil-analyzer .

# Kjør container
docker run -p 8501:8501 --env-file .env finnbil-analyzer
```

## 📁 Persistent data

Data lagres i `./data` mappen som blir mountet inn i containeren, så `finn_data.json` vil bli bevart mellom container-restart.

## 🌐 Tilgang

Applikasjonen vil være tilgjengelig på: http://localhost:8501

## 🔧 Konfigurasjon

- Port: 8501 (kan endres i docker-compose.yaml)
- Environment variables: Definert i .env filen
- Health check: Innebygd helse-sjekk hver 30. sekund

## 📊 Monitoring

```bash
# Sjekk container status
docker-compose ps

# Se ressursbruk
docker stats finnbil-analyzer

# Sjekk logs
docker-compose logs finnbil-app
```
