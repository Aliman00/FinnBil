# FinnBil Analyzer

A comprehensive car analysis tool for Finn.no listings with AI-powered insights.

## Features

- **Web Scraping**: Automated data collection from Finn.no car listings
- **AI Analysis**: Advanced car valuation using SmartePenger.no depreciation standards
- **Interactive Dashboard**: Streamlit-based web interface with real-time data visualization
- **Smart Recommendations**: AI-powered buying recommendations based on value analysis
- **Statistics**: Comprehensive car market statistics and trends

## Project Structure

```
FinnBil/
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Centralized settings with environment variables
├── services/               # Business logic services
│   ├── __init__.py
│   ├── ai_service.py       # AI/LLM integration
│   ├── data_service.py     # Data fetching and processing
│   └── simple_car_analyzer.py  # Car valuation logic
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── ai_analysis.py      # AI analysis interface
│   ├── car_data.py         # Car data display
│   ├── car_display.py      # Car data formatting
│   └── sidebar.py          # Sidebar controls
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── common.py           # Common utility functions
│   ├── exceptions.py       # Custom exception classes
│   └── logging.py          # Logging configuration
├── data/                   # Data storage
├── logs/                   # Application logs
├── webapp.py               # Main Streamlit application
├── webscraper.py           # Web scraping functionality
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FinnBil
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   # Required
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   # Optional (with defaults)
   AI_MODEL=deepseek/deepseek-chat-v3-0324:free
   AI_BASE_URL=https://openrouter.ai/api/v1
   AI_TIMEOUT=60
   
   # Scraping configuration
   MAX_PAGES=2
   RATE_LIMIT_MIN=2.0
   RATE_LIMIT_MAX=4.0
   REQUEST_TIMEOUT=10
   ```

## Usage

1. **Start the application**:
   ```bash
   streamlit run webapp.py
   ```

2. **Add Finn.no URLs**:
   - Use the sidebar to add car search URLs from Finn.no
   - Multiple URLs can be added for comprehensive analysis

3. **Fetch and analyze data**:
   - Click "Hent og analyser alle URL-er" to fetch car data
   - View the data table with statistics

4. **AI Analysis**:
   - Click "Start AI Analyse" for detailed AI-powered recommendations
   - Use the chat interface for specific questions

## Configuration

The application uses a centralized configuration system with environment variable support:

- **AI Configuration**: Model, API keys, timeouts
- **Scraping Configuration**: Rate limits, request timeouts, user agents
- **Application Configuration**: UI settings, file paths, default URLs

## Key Features Explained

### Smart Car Analysis
- Uses SmartePenger.no depreciation standards
- Calculates expected vs actual depreciation
- Provides A-F grading system for cars
- Considers both price and mileage factors

### Rate Limiting
- Respectful scraping with configurable delays
- Random delays between requests to avoid detection
- Timeout protection for network requests

### Error Handling
- Comprehensive exception hierarchy
- Detailed logging with configurable levels
- Graceful error recovery and user feedback

### Data Management
- Automatic data persistence to JSON files
- Docker-compatible data directory structure
- Statistics calculation with error handling

## Docker Support

The application includes Docker configuration files:
- `Dockerfile`: Container definition
- `docker-compose.yaml`: Local development
- `docker-compose.prod.yaml`: Production deployment

## Development

### Code Quality
- Type hints throughout the codebase
- Modular component architecture
- Separation of concerns between services, UI, and utilities
- Comprehensive error handling and logging

### Testing
- Test files included for various components
- Debug utilities for price analysis and caching

### Logging
- Configurable logging levels
- File and console output options
- Structured logging with timestamps and levels

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) | - |
| `AI_MODEL` | AI model to use | `deepseek/deepseek-chat-v3-0324:free` |
| `AI_BASE_URL` | AI service base URL | `https://openrouter.ai/api/v1` |
| `AI_TIMEOUT` | AI request timeout (seconds) | `60` |
| `MAX_PAGES` | Maximum pages to scrape | `2` |
| `RATE_LIMIT_MIN` | Minimum delay between requests | `2.0` |
| `RATE_LIMIT_MAX` | Maximum delay between requests | `4.0` |
| `REQUEST_TIMEOUT` | HTTP request timeout | `10` |

## Contributing

1. Follow the existing code structure and patterns
2. Add type hints to all functions
3. Include appropriate error handling
4. Update tests for new functionality
5. Use the logging system for debugging information

## License

[Add your license information here]

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.
