# 🚀 Deployment Guide for Honeypot API

## ✅ Pre-Deployment Checklist

### Files Required
- [x] `requirements.txt` - All Python dependencies
- [x] `Procfile` - Start command for deployment platforms
- [x] `runtime.txt` - Python version specification
- [x] `.env.example` - Template for environment variables
- [x] `.gitignore` - Excludes .env and virtual environment

### Environment Variables Required
Set these in your hosting provider's dashboard:

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | Your API authentication key | `your-strong-secret-key` |
| `AI_PROVIDER` | AI provider: gemini, groq, or cohere | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `GROQ_API_KEY` | Groq API key (optional) | `gsk_...` |
| `COHERE_API_KEY` | Cohere API key (optional) | `...` |
| `GUVI_CALLBACK_URL` | GUVI callback endpoint | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` |
| `PORT` | Server port (auto-set by most platforms) | `8000` |

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 📦 Deployment Options

### Option 1: Render.com (Recommended - Free Tier)
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set environment variables
5. Deploy!

### Option 2: Railway.app
1. Push code to GitHub
2. Create new project on Railway
3. Add environment variables
4. Deploy from GitHub

### Option 3: Heroku
1. Install Heroku CLI
2. `heroku create your-app-name`
3. `heroku config:set API_KEY=your-key GEMINI_API_KEY=your-key ...`
4. `git push heroku main`

### Option 4: DigitalOcean App Platform
1. Create new app from GitHub
2. Set environment variables
3. Deploy

---

## 🧪 Post-Deployment Testing

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app-url.com/health

# API documentation
https://your-app-url.com/docs

# Test message (replace with your API key)
curl -X POST https://your-app-url.com/api/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"sessionId": "test", "message": {"sender": "scammer", "text": "Test message", "timestamp": "2026-01-01T00:00:00Z"}, "conversationHistory": [], "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}}'
```

---

## 🔒 Security Notes

1. **Never commit `.env` file** - It contains real API keys
2. **Use strong API_KEY** - Generate a random secure key for production
3. **Update API keys** - Rotate keys regularly
4. **HTTPS only** - Most platforms handle this automatically

---

## 📊 Monitoring

Monitor these endpoints for health:
- `/health` - Basic health check
- `/api/stats` - API statistics and metrics
