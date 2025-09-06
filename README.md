# Bodø/Glimt Ticket Monitor

A Python application that monitors the Bodø/Glimt website for ticket availability for the Tottenham match and sends email notifications when tickets become available for ordinary people (non-members/non-season ticket holders).

## Features

- Automatically checks the Bodø/Glimt website every hour
- Uses Claude AI to analyze website content for ticket availability  
- Sends email notifications when tickets are available
- Designed for deployment on Railway

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Required environment variables:
- `ANTHROPIC_API_KEY`: Your Claude API key from Anthropic
- `FROM_EMAIL`: Your Gmail address
- `EMAIL_PASSWORD`: Your Gmail app password (not regular password)
- `TO_EMAIL`: Email address to receive notifications

### 3. Gmail Setup

For Gmail:
1. Enable 2-factor authentication
2. Generate an "App Password" for this application
3. Use the app password in `EMAIL_PASSWORD`

### 4. Run Locally

```bash
python main.py
```

## Railway Deployment

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Set environment variables in Railway dashboard
5. Deploy: `railway up`

## How It Works

1. Fetches content from Bodø/Glimt homepage
2. Uses Claude to analyze content for Tottenham ticket availability
3. Looks specifically for tickets available to ordinary people
4. Sends email alerts when tickets are found
5. Runs continuously every hour
