# priceIQ agent
> Intelligent product price discovery & market analysis powered by autonomous web navigation. Built on open-source browser automation, the agent traverses digital marketplaces, captures visual data, and synthesizes real-time price intelligence.

## Core Features
- 🤖 **Autonomous Navigation**: Self-guided web traversal and data extraction
- 🔄 **Agentic Loop**: Continuous market monitoring with intelligent state management
- 📊 **Multi-Source Analysis**: Cross-marketplace price comparison and trend detection
- 📸 **Visual Processing**: Screenshot capture and analysis for data verification
- 🔌 **Modular Architecture**: Extensible design - easily adapt the agentic loop for different research tasks

## Use Cases
- Real-time price monitoring across multiple marketplaces
- Competitive analysis and market positioning
- Product availability tracking
- Historical price trend analysis

## Technical Foundation
Built on open-source browser automation technology, priceIQ agent combines:
- Autonomous web navigation
- Computer vision processing
- Natural language understanding
- Real-time data synthesis

The modular architecture allows for easy adaptation of the agentic loop to research different domains - from product prices to any other web-based data collection and analysis task.

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