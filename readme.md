# priceIQ agent
> Intelligent product price discovery & market analysis

## Setup

### 1. Install Dependencies
```bash
pip -r requirements.txt
```

### 2. API Keys Setup
Create a `.env` file in the root directory with the following keys (check env.example):

```env
OPENAI_API_KEY=your_key_here
BROWSERLESS_API_KEY=your_key_here
SERPAPI_API_KEY=your_key_here
```

#### How to Get API Keys:

**OpenAI API Key**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to Settings → API Keys
4. Create new secret key

**Browserless API Key**
1. Visit [Browserless](https://www.browserless.io/)
2. Sign up for free tier
3. Copy API key from dashboard

**SerpAPI Key**
1. Visit [SerpAPI](https://serpapi.com/)
2. Create free account
3. Find API key in dashboard

### 3. Run Agent
```bash
python agent.py
```

Follow the interactive prompts to:
- Enter products to analyze (separate with ' | ')
- Enter websites to search (separate with ' | ')
- Choose output format (json/excel)
- Set number of analysis turns

Press 'q' + Enter at any time to exit gracefully.

## Output
Results will be saved in the `workspace` directory in your chosen format (JSON or Excel).