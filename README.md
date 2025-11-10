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

#### Prerequisites

Before deploying, ensure you have:
- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed (for local builds)
- Access to your GCP project

#### 1.Prerequisites Setup

```bash
# Install and authenticate gcloud CLI
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable storage.googleapis.com
```

**Note:** Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

#### 2. Secret Manager Setup

```bash
# Create secrets for API keys
echo -n "YOUR_GROQ_API_KEY" | gcloud secrets create GROQ_API_KEY \
    --data-file=- \
    --project=YOUR_PROJECT_ID

echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
    --data-file=- \
    --project=YOUR_PROJECT_ID
```

**Notes:**
- Replace `YOUR_GROQ_API_KEY` and `YOUR_GEMINI_API_KEY` with your actual API keys
- Replace `YOUR_PROJECT_ID` with your actual GCP project ID
- This step creates secrets in Secret Manager. IAM role grants will be done in Step 6.

#### 3. Artifact Registry Setup

```bash
# Create Artifact Registry repository for Docker images
gcloud artifacts repositories create REPOSITORY_NAME \
    --repository-format=docker \
    --location=YOUR_REGION \
    --description="Docker repository for Healthcare API" \
    --project=YOUR_PROJECT_ID

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker YOUR_REGION-docker.pkg.dev
```

This step creates a Docker repository in Artifact Registry where your Docker images will be stored and configures Docker authentication.

#### 4.Cloud SQL Setup

```bash
# Create Cloud SQL instance
gcloud sql instances create INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=YOUR_REGION \
    --root-password=YOUR_DATABASE_PASSWORD \
    --project=YOUR_PROJECT_ID

# Create database
gcloud sql databases create DATABASE_NAME \
    --instance=INSTANCE_NAME \
    --project=YOUR_PROJECT_ID

# Get instance connection name (needed for Cloud Run)
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe INSTANCE_NAME \
    --format="value(connectionName)" \
    --project=YOUR_PROJECT_ID)

echo "Instance connection name: ${INSTANCE_CONNECTION_NAME}"
```

This step creates a Cloud SQL PostgreSQL instance and database, and retrieves the instance connection name needed for Cloud Run to connect to the database.

#### 5. Create DATABASE_URL Secret

Create the DATABASE_URL secret with the connection string to your Cloud SQL database.

```bash
# Create DATABASE_URL secret
echo -n "postgresql://postgres:YOUR_DATABASE_PASSWORD@localhost/DATABASE_NAME?host=/cloudsql/INSTANCE_CONNECTION_NAME" | \
    gcloud secrets create DATABASE_URL \
    --data-file=- \
    --project=YOUR_PROJECT_ID
```

**Notes:**
- Replace `YOUR_DATABASE_PASSWORD` with your Cloud SQL database password
- Replace `DATABASE_NAME` with your database name
- Replace `INSTANCE_CONNECTION_NAME` with the connection name from Step 4 (format: `PROJECT_ID:REGION:INSTANCE_NAME`)
- Replace `YOUR_PROJECT_ID` with your actual GCP project ID

#### 6. IAM Roles Setup

Grant all necessary IAM roles to the Cloud Run service account.

```bash
# Get Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Secret Manager access for all secrets
gcloud secrets add-iam-policy-binding GROQ_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID

gcloud secrets add-iam-policy-binding DATABASE_URL \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project=YOUR_PROJECT_ID

# Grant Cloud Storage access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectViewer"
```

**Notes:**
- Replace `YOUR_PROJECT_ID` with your actual GCP project ID
- This step grants all necessary permissions to the Cloud Run service account
- Cloud SQL permissions are automatically configured via `--add-cloudsql-instances` flag in deployment commands

#### 7. Backend Deployment

**Note:** Ensure you have the project code locally. If not, clone the repository first.
- Replace 'SERVICE_NAME' with your actual Cloud Run service name

```bash
# Navigate to project root
cd /path/to/project/root

# Build Docker image
docker build -t SERVICE_NAME:latest -f infra/docker/Dockerfile .

# Tag image for Artifact Registry
docker tag SERVICE_NAME:latest \
    YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY_NAME/SERVICE_NAME:latest

# Push to Artifact Registry
docker push YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY_NAME/SERVICE_NAME:latest

# Deploy backend to Cloud Run
gcloud run deploy SERVICE_NAME \
    --image YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY_NAME/SERVICE_NAME:latest \
    --platform managed \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars DATABASE_URL="postgresql://postgres:YOUR_DATABASE_PASSWORD@localhost/DATABASE_NAME?host=/cloudsql/INSTANCE_CONNECTION_NAME" \
    --set-secrets GROQ_API_KEY=GROQ_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest \
    --add-cloudsql-instances=INSTANCE_CONNECTION_NAME

# Get backend URL
BACKEND_URL=$(gcloud run services describe SERVICE_NAME \
    --platform managed \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --format="value(status.url)")

echo "Backend URL: ${BACKEND_URL}"
```

This step builds your Docker image, pushes it to Artifact Registry, and deploys it to Cloud Run with database connection, secrets, and Cloud SQL instance configuration. The Cloud SQL Proxy creates a secure connection between Cloud Run and Cloud SQL using IAM authentication.

#### 8. Database Schema Creation

Before importing data, create the database tables using a Cloud Run Job.

```bash
# Create a Cloud Run Job to create tables
gcloud run jobs create JOB_NAME \
    --image YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY_NAME/SERVICE_NAME:latest \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --set-env-vars DATABASE_URL="postgresql://postgres:YOUR_DATABASE_PASSWORD@localhost/DATABASE_NAME?host=/cloudsql/INSTANCE_CONNECTION_NAME" \
    --set-cloudsql-instances=INSTANCE_CONNECTION_NAME \
    --args="python,-m,api.v2.create_tables_v2" \
    --task-timeout=300 \
    --memory=2Gi \
    --cpu=1

# Execute the job
gcloud run jobs execute JOB_NAME \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID
```

This step creates all necessary database tables (patients_v2, encounters_v2, conditions_v2, organizations_v2, practitioners_v2, observations_v2) in your Cloud SQL database using the same containerized environment as your production deployment.

#### 9. Cloud Storage Setup

Upload your FHIR bundle JSON files to Cloud Storage for data import.

```bash
# Create a Cloud Storage bucket (if not already created)
gsutil mb -p YOUR_PROJECT_ID -l YOUR_REGION gs://YOUR_BUCKET_NAME

# Upload data bundles to Cloud Storage
gsutil -m cp -r /path/to/local/data/bundles/* gs://YOUR_BUCKET_NAME/bundles/

# Verify upload
gsutil ls gs://YOUR_BUCKET_NAME/bundles/ | head -10
```

This step uploads your FHIR bundle JSON files to Cloud Storage, which will be used by the data import job to populate your Cloud SQL database. The `-m` flag enables parallel (multi-threaded) uploads, significantly speeding up the transfer when uploading many files.

#### 10. Data Import

Import FHIR bundle data into Cloud SQL using a Cloud Run Job. This job will download bundles from Cloud Storage and import them into the database.

```bash
# Create Cloud Run Job for data import
gcloud run jobs create JOB_NAME \
    --image YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPOSITORY_NAME/SERVICE_NAME:latest \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --set-secrets DATABASE_URL=DATABASE_URL:latest \
    --set-env-vars GCS_BUCKET_NAME=YOUR_BUCKET_NAME,GCS_BUNDLES_PREFIX=bundles/ \
    --set-cloudsql-instances=INSTANCE_CONNECTION_NAME \
    --args="python,-m,scripts.import_all_data" \
    --task-timeout=3600 \
    --memory=4Gi \
    --cpu=2 \
    --max-retries=1

# Execute the import job
gcloud run jobs execute JOB_NAME \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID \
    --wait

# Monitor job execution
gcloud run jobs executions list \
    --job=JOB_NAME \
    --region YOUR_REGION \
    --project YOUR_PROJECT_ID
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
