# Environment Variables Configuration

This file documents all available environment variables for the FinnBil application.

## 🔑 Required Variables

### `OPENROUTER_API_KEY`
- **Description**: API key for OpenRouter service
- **Required**: Yes
- **Example**: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Where to get**: [OpenRouter.ai](https://openrouter.ai/) - Sign up and get your API key
- **Security**: Never commit this to version control!

## 🤖 AI Model Configuration

### `AI_MODEL`
- **Description**: The AI model to use for analysis
- **Required**: No
- **Default**: `deepseek/deepseek-chat-v3-0324:free`
- **Popular options**:
  - `deepseek/deepseek-chat-v3-0324:free` (Free, good quality)
  - `anthropic/claude-3-sonnet` (High quality, paid)
  - `openai/gpt-4` (OpenAI flagship, paid)
  - `google/gemini-pro` (Google's model)
  - `meta-llama/llama-3-70b-instruct` (Open source)

### `AI_BASE_URL`
- **Description**: Base URL for the AI API
- **Required**: No
- **Default**: `https://openrouter.ai/api/v1`
- **Note**: Change only if using a different AI provider

## 📁 Example .env file

```env
# Required - Get your own API key from https://openrouter.ai/
OPENROUTER_API_KEY=your_api_key_here

# Optional AI Configuration
AI_MODEL=deepseek/deepseek-chat-v3-0324:free
AI_BASE_URL=https://openrouter.ai/api/v1
```

## 🚀 For Different Environments

### Local Development
Create a `.env` file with all variables.

### Docker
Variables are passed through docker-compose.yaml or command line.

### Render.com
Set variables in the Render dashboard under "Environment".

## 💰 Cost Considerations

### Free Models
- `deepseek/deepseek-chat-v3-0324:free`
- Most models with `:free` suffix

### Paid Models
- `anthropic/claude-3-sonnet` (~$3-15 per 1M tokens)
- `openai/gpt-4` (~$10-30 per 1M tokens)
- `google/gemini-pro` (~$0.50-7 per 1M tokens)

**Tip**: Start with free models for testing, then upgrade for production if needed.
