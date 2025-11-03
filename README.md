# 🏥 Healthcare API - Production

A production-ready FastAPI healthcare API with AI-powered clinical assistant, deployed on Google Cloud Platform.

## 🌐 Production URLs

- **API Documentation**: `https://your-api-url.run.app/docs`
- **Health Check**: `https://your-api-url.run.app/api/v2/health`
- **Streamlit Frontend**: `https://your-frontend-url.run.app`

## 🚀 Quick Start

This application is deployed on **Google Cloud Run** and automatically scales based on demand.

### Architecture

- **Backend**: FastAPI v2 (Cloud Run)
- **Frontend**: Streamlit (Cloud Run)  
- **Database**: Cloud SQL (PostgreSQL)
- **AI Agent**: LangChain with multi-LLM support (Groq, OpenAI, Gemini)

## 📋 API Endpoints

### Core Resources
- `/api/v2/patients` - Patient management
- `/api/v2/encounters` - Medical encounters
- `/api/v2/conditions` - Medical conditions
- `/api/v2/observations` - Clinical observations
- `/api/v2/practitioners` - Healthcare providers
- `/api/v2/organizations` - Healthcare facilities

### Health Check
- `GET /api/v2/health` - Service health status

## 🔐 Environment Variables

All secrets are managed through **Google Cloud Secret Manager**:

- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key for Llama models
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `GEMINI_API_KEY` - Google Gemini API key

## 🔄 Deployment

### Automatic Deployment
- Pushing to `production` branch triggers CI/CD pipeline
- Docker images are built and deployed to Cloud Run automatically

### Manual Deployment
```bash
# Build and push Docker image
docker build -t gcr.io/PROJECT_ID/healthcare-api:latest -f infra/docker/Dockerfile .
docker push gcr.io/PROJECT_ID/healthcare-api:latest

# Deploy to Cloud Run
gcloud run deploy healthcare-api-backend \
  --image gcr.io/PROJECT_ID/healthcare-api:latest \
  --region us-central1
```

## 📊 Monitoring

- **Cloud Logging**: View logs in Google Cloud Console
- **Cloud Monitoring**: Track performance and errors
- **Health Checks**: Automatic health monitoring at `/api/v2/health`

## 🔧 Troubleshooting

1. **Check Cloud Run logs** for errors
2. **Verify secrets** in Secret Manager
3. **Test database connection** via Cloud SQL console
4. **Review API documentation** at `/docs` endpoint

## 📝 Tech Stack

- **Framework**: FastAPI 2.x
- **Database**: PostgreSQL 15 (Cloud SQL)
- **ORM**: SQLAlchemy
- **AI/ML**: LangChain, LangGraph
- **Frontend**: Streamlit
- **Deployment**: Google Cloud Run
- **Container**: Docker

## 📞 Support

For deployment issues, check:
- Cloud Run service logs
- Cloud SQL connection status
- Secret Manager configuration

---

**Version**: 2.0.0  
**Last Updated**: 2025  
**Platform**: Google Cloud Run
