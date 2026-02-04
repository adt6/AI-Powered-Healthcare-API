# 🏥 AI-Powered Healthcare API

A comprehensive, production-ready FastAPI project for managing healthcare data using PostgreSQL and Docker, enhanced with an intelligent AI clinical assistant. Built with clean architecture, comprehensive data modeling, RESTful CRUD endpoints following FHIR (Fast Healthcare Interoperability Resources) standards, and powered by advanced AI models for natural language healthcare data interaction.

---

## 📦 Features

- 🚀 **FastAPI v2** with modular structure and versioned APIs
- 🧠 **SQLAlchemy ORM** with PostgreSQL for robust data persistence
- 📄 **Pydantic schemas** for request/response validation
- 🐳 **Docker + docker-compose** for isolated development
- 🔁 **CRUD endpoints** for core FHIR-style entities
- 🔧 **Swagger UI** for interactive API testing
- 📊 **Comprehensive data modeling** with proper relationships
- 🏗️ **Clean architecture** with separation of concerns
- 🤖 **AI-Powered Clinical Assistant** with multi-LLM support
- 💬 **Interactive Chatbot Interface** using Streamlit
- 🛠️ **Specialized Healthcare Tools** for data retrieval and analysis

---

## 🏗️ Project Structure

```text
Building API/
├── backend/src/            # Backend API and AI agent
│   ├── api/v2/             # FastAPI v2 (FHIR-style)
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routes/         # API endpoint handlers
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── database.py     # Database configuration
│   │   └── main.py         # FastAPI application entry point
│   ├── agents/             # AI Clinical Assistant
│   │   ├── prompts/        # Clinical instructions
│   │   ├── tools/          # Patient and observation tools
│   │   ├── agent_config.py # AI model configuration
│   │   └── agent_factory.py
│   ├── scripts/            # Data import utilities
│   └── tests/              # Test suite
├── frontend/               # Streamlit chatbot UI
│   └── streamlit_app.py
├── data/                   # FHIR bundle data files
├── docs/                   # Documentation and diagrams
├── infra/compose/          # Docker Compose
├── start-backend.sh        # Start FastAPI (uv)
├── start-frontend.sh       # Start Streamlit (uv)
├── run_chatbot.py          # AI chatbot launcher
└── pyproject.toml          # Dependencies (uv)
```

---

## 🗃️ Comprehensive Data Modeling (API v2)

### **Database Schema Overview**

The app_v2 implements a comprehensive healthcare data model with 6 core entities and their relationships:

#### **Core Entities:**

1. **🏢 Organizations** (`organizations_v2`)
   - Healthcare facilities, hospitals, clinics
   - Manages practitioners and hosts encounters
   - Contains contact and location information

2. **👥 Patients** (`patients_v2`)
   - Central entity - all healthcare data revolves around patients
   - Comprehensive demographic and contact information
   - Links to managing organization

3. **👨‍⚕️ Practitioners** (`practitioners_v2`)
   - Healthcare providers (doctors, nurses, specialists)
   - Belongs to organizations
   - Conducts encounters and performs observations

4. **🏥 Encounters** (`encounters_v2`)
   - Patient visits, appointments, hospital stays
   - Links patients, practitioners, and organizations
   - Contains visit details, timing, and reasons

5. **🩺 Conditions** (`conditions_v2`)
   - Medical diagnoses, problems, conditions
   - Associated with patients and encounters
   - Includes clinical status and verification

6. **📊 Observations** (`observations_v2`)
   - Clinical measurements, test results, vital signs
   - Links to patients, encounters, and practitioners
   - Supports both numeric and text values

### **Database Relationships & Cardinality**

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ PRACTITIONERS : employs
    ORGANIZATIONS ||--o{ ENCOUNTERS : hosts
    ORGANIZATIONS ||--o{ PATIENTS : manages
    
    PATIENTS ||--o{ ENCOUNTERS : has
    PATIENTS ||--o{ CONDITIONS : has
    PATIENTS ||--o{ OBSERVATIONS : has
    
    PRACTITIONERS ||--o{ ENCOUNTERS : conducts
    PRACTITIONERS ||--o{ OBSERVATIONS : performs
    
    ENCOUNTERS ||--o{ CONDITIONS : diagnoses
    ENCOUNTERS ||--o{ OBSERVATIONS : includes
```

### **Key Design Principles:**

#### **1. Patient-Centric Design**
- **Patients** are the central entity
- All clinical data (encounters, conditions, observations) links back to patients
- Enables comprehensive patient history and care coordination

#### **2. Flexible Relationships**
- **Optional foreign keys** allow for incomplete data scenarios
- **Nullable relationships** support real-world healthcare workflows
- **One-to-many relationships** follow healthcare domain patterns

#### **3. FHIR Compliance**
- **FHIR-style identifiers** for interoperability
- **Standardized coding systems** (LOINC, SNOMED CT)
- **Temporal data** with proper datetime handling

#### **4. Data Integrity**
- **Primary keys** with auto-incrementing IDs
- **Foreign key constraints** for referential integrity
- **Indexes** on frequently queried fields

### **Detailed Entity Specifications**

#### **🏢 Organizations Table**
```sql
CREATE TABLE organizations_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR UNIQUE,           -- FHIR identifier
    name VARCHAR NOT NULL,               -- Organization name
    type_code VARCHAR,                   -- Organization type (hospital, clinic, etc.)
    type_display VARCHAR,                -- Human-readable type
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    address_line VARCHAR,                -- Street address
    city VARCHAR,                        -- City
    state VARCHAR,                       -- State/Province
    postal_code VARCHAR,                 -- ZIP/Postal code
    part_of_identifier VARCHAR           -- Parent organization
);
```

#### **👥 Patients Table**
```sql
CREATE TABLE patients_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR UNIQUE,           -- MRN/UUID from FHIR
    first_name VARCHAR NOT NULL,         -- Patient first name
    last_name VARCHAR NOT NULL,          -- Patient last name
    birth_date DATE NOT NULL,            -- Date of birth
    gender VARCHAR,                      -- Gender (M/F/O)
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    address_line VARCHAR,                -- Street address
    city VARCHAR,                        -- City
    state VARCHAR,                       -- State/Province
    postal_code VARCHAR,                 -- ZIP/Postal code
    marital_status VARCHAR,              -- Marital status
    language VARCHAR,                    -- Preferred language
    race VARCHAR,                        -- Race
    ethnicity VARCHAR,                   -- Ethnicity
    deceased_date VARCHAR,               -- Date of death (ISO string)
    active BOOLEAN DEFAULT TRUE,         -- Active patient flag
    managing_organization_identifier VARCHAR  -- Managing organization
);
```

#### **👨‍⚕️ Practitioners Table**
```sql
CREATE TABLE practitioners_v2 (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR,                  -- FHIR identifier
    name VARCHAR NOT NULL,               -- Practitioner name
    gender VARCHAR,                      -- Gender
    specialty_code VARCHAR,              -- Medical specialty code
    specialty_display VARCHAR,           -- Specialty description
    phone VARCHAR,                       -- Contact phone
    email VARCHAR,                       -- Contact email
    organization_id INTEGER REFERENCES organizations_v2(id)  -- Employing organization
);
```

#### **🏥 Encounters Table**
```sql
CREATE TABLE encounters_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    practitioner_id INTEGER REFERENCES practitioners_v2(id),
    organization_id INTEGER REFERENCES organizations_v2(id),
    
    identifier VARCHAR,                  -- Encounter identifier
    status VARCHAR NOT NULL,             -- Encounter status (planned, active, finished)
    class_code VARCHAR,                  -- Encounter class (ambulatory, emergency, etc.)
    class_display VARCHAR,               -- Human-readable class
    start_time TIMESTAMP,                -- Encounter start time
    end_time TIMESTAMP,                  -- Encounter end time
    reason_code VARCHAR,                 -- Reason for encounter
    reason_display VARCHAR               -- Human-readable reason
);
```

#### **🩺 Conditions Table**
```sql
CREATE TABLE conditions_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    encounter_id INTEGER REFERENCES encounters_v2(id),
    
    code VARCHAR NOT NULL,               -- Condition code (ICD-10, SNOMED)
    system VARCHAR,                      -- Coding system
    display VARCHAR,                     -- Human-readable condition
    category_code VARCHAR,               -- Condition category
    clinical_status VARCHAR,             -- Clinical status (active, inactive, resolved)
    verification_status VARCHAR,         -- Verification status (provisional, confirmed)
    onset_time TIMESTAMP,                -- Condition onset time
    abatement_time TIMESTAMP,            -- Condition resolution time
    recorded_date TIMESTAMP              -- When condition was recorded
);
```

#### **📊 Observations Table**
```sql
CREATE TABLE observations_v2 (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients_v2(id),
    encounter_id INTEGER REFERENCES encounters_v2(id),
    practitioner_id INTEGER REFERENCES practitioners_v2(id),
    
    identifier VARCHAR,                  -- Observation identifier
    status VARCHAR NOT NULL,             -- Observation status
    code VARCHAR NOT NULL,               -- Observation code (LOINC)
    code_system VARCHAR,                 -- Coding system
    code_display VARCHAR,                -- Human-readable observation
    value_quantity FLOAT,                -- Numeric value
    value_unit VARCHAR,                  -- Unit of measurement
    value_string VARCHAR,                -- Text value
    effective_time TIMESTAMP,            -- When observation was taken
    issued_time TIMESTAMP                -- When observation was recorded
);
```

---

## 🤖 AI-Powered Clinical Assistant

The project includes a sophisticated AI clinical assistant that provides intelligent healthcare data analysis and patient information retrieval through natural language interactions.

### **🧠 Multi-LLM Support**

The AI assistant supports multiple large language models for flexibility and performance optimization:

#### **Supported Models:**
- **Claude 3.5 Sonnet** (Anthropic) - High-performance reasoning
- **Claude 3 Haiku** (Anthropic) - Fast, cost-effective responses
- **Llama 3.3 70B** (via Groq) - Open-source, versatile model
- **Mixtral Saba 24B** (via Groq) - Efficient mixture-of-experts model
- **GPT-4o Mini** (OpenAI) - Compact, powerful model
- **Gemini 2.5 Flash** (Google) - Fast, multimodal capabilities

#### **Default Configuration:**
```python
DEFAULT_LLM_TYPE = "llama_groq"  # Llama 3.3 70B via Groq
DEFAULT_API_BASE_URL = "http://localhost:8000/api/v2"
```

### **🛠️ Specialized Healthcare Tools**

The AI assistant is equipped with specialized tools for healthcare data interaction:

#### **Patient and clinical tools:**
- **get_patient_info** - Patient demographics by ID or identifier
- **search_patients** - Find patients by name, DOB, gender
- **get_patient_conditions** - Diagnoses and problems for a patient
- **get_patient_encounters** - Visits and appointments for a patient
- **get_patient_observations** - All lab results and vitals for a patient
- **get_patient_observation_by_type** - Filter by type (e.g. glucose, blood pressure) with summary stats (latest, range, average)
- **get_patient_summary** - Combined patient overview (info + conditions + encounters)

#### **Advanced Analytics:**
- **Cross-Patient Analysis** - Identify patterns across patient populations
- **Temporal Analysis** - Track changes over time in patient conditions
- **Clinical Decision Support** - Provide evidence-based recommendations
- **Data Quality Assessment** - Identify gaps or inconsistencies in records

### **💬 Interactive Chatbot Interface**

#### **Streamlit Web Application:**
- **User-Friendly Interface** - Clean, intuitive chat interface
- **Real-Time Responses** - Instant AI-powered healthcare insights
- **Context-Aware Conversations** - Maintains conversation context
- **Multi-Modal Support** - Handles text, structured queries, and natural language

#### **Access Methods:**
```bash
# From project root (recommended)
./start-frontend.sh

# Or
python run_chatbot.py

# Backend must be running first (separate terminal)
./start-backend.sh
```

**Web Interface:** http://localhost:8501  
**API:** http://localhost:8000

### **🎯 Clinical Use Cases**

#### **For Healthcare Professionals:**
- **Patient Lookup** - "Find all patients with diabetes in the last 6 months"
- **Clinical Summaries** - "Give me a summary of patient John Doe's recent encounters"
- **Trend Analysis** - "Show me the trend of blood pressure readings for patient 123"
- **Provider Information** - "Which cardiologists are available at City Hospital?"

#### **For Healthcare Administrators:**
- **Population Health** - "How many patients have active hypertension conditions?"
- **Resource Planning** - "What are the most common encounter types this month?"
- **Quality Metrics** - "Show me patients with incomplete demographic information"
- **Compliance Monitoring** - "Identify patients with missing required documentation"

#### **For Clinical Researchers:**
- **Data Mining** - "Find all patients with specific condition codes"
- **Cohort Analysis** - "Identify patients meeting specific criteria"
- **Outcome Tracking** - "Monitor treatment effectiveness across patient groups"
- **Pattern Recognition** - "Identify unusual patterns in patient data"

### **🔒 Privacy & Security Features**

#### **Data Protection:**
- **HIPAA-Compliant Design** - Built with healthcare privacy standards
- **Secure API Integration** - Encrypted communication with healthcare systems
- **Access Control** - Role-based access to sensitive information
- **Audit Logging** - Track all data access and modifications

#### **Clinical Safety:**
- **Factual Responses** - AI provides accurate, data-driven insights
- **Uncertainty Handling** - Clearly indicates when information is incomplete
- **Clinical Context** - Maintains medical accuracy and relevance
- **Error Prevention** - Validates data before presenting to users

### **⚙️ Configuration & Customization**

#### **Model Selection:**
```python
# In agent_config.py
DEFAULT_LLM_TYPE = "llama_groq"  # Change to preferred model
```

#### **Available Options:**
- `"haiku"` - Claude 3 Haiku (fast, cost-effective)
- `"sonnet"` - Claude 3.5 Sonnet (high-performance)
- `"llama_groq"` - Llama 3.3 70B (open-source, versatile)
- `"mixtral_groq"` - Mixtral Saba 24B (efficient)
- `"openai"` - GPT-4o Mini (compact, powerful)
- `"gemini"` - Gemini 2.5 Flash (fast, multimodal)

#### **Custom Instructions:**
The AI assistant uses specialized clinical instructions in `backend/src/agents/prompts/clinical_instructions.md` for healthcare workflows and requirements.

### **🚀 Getting Started with AI Assistant**

#### **1. Start backend and chatbot:**
```bash
# Terminal 1: start FastAPI backend
./start-backend.sh

# Terminal 2: start Streamlit chatbot
./start-frontend.sh
# or: python run_chatbot.py
```

#### **2. Access the interface:**
- Chatbot: http://localhost:8501
- API docs: http://localhost:8000/docs

#### **3. Example queries:**
```
"Find all patients with diabetes"
"Show me patient 3's glucose levels"
"What are the conditions for patient 2?"
"Give me a summary of recent encounters"
```

#### **4. Docker (optional):**
```bash
# From project root
docker compose -f infra/compose/docker-compose.yml up

# Chatbot: http://localhost:8501  |  API: http://localhost:8000
```

### **🔧 AI Assistant Architecture**

#### **Component overview:**
```
AI Clinical Assistant
├── backend/src/agents/
│   ├── agent_factory.py    # LLM config, tools, response generation
│   ├── agent_config.py     # Model selection
│   ├── tools/
│   │   ├── patient_tools.py  # get_patient_info, observations, conditions, etc.
│   │   └── base_tools.py     # API client, formatters
│   └── prompts/
│       └── clinical_instructions.md
└── frontend/
    └── streamlit_app.py    # Chat UI (Streamlit)
```

#### **Data Flow:**
```
User Query → Streamlit Interface → AI Agent → Healthcare Tools → API → Database
                ↓
            AI Response ← Clinical Analysis ← Data Processing ← FHIR Data
```

---

## 🧪 API Documentation

### **API**
- **v2**: `/api/v2/*` - FHIR-style API (patients, encounters, conditions, observations, organizations, practitioners)

### **Interactive Documentation**
Once running, open http://localhost:8000/docs for the interactive Swagger UI.

### **Health Check**
```bash
GET /api/v2/health
Response: {"status": "ok", "api": "v2"}
```

### **Complete API Endpoints (v2) - IMPLEMENTED ✅**

#### **🏥 Patients**
```bash
GET    /api/v2/patients           # List patients with filtering
GET    /api/v2/patients/{id}      # Get patient by ID
POST   /api/v2/patients           # Create new patient
PUT    /api/v2/patients/{id}      # Update patient
DELETE /api/v2/patients/{id}      # Delete patient

# Query Parameters for GET /api/v2/patients:
# - limit, offset (pagination)
# - identifier, first_name, last_name, active (filtering)
```

#### **🏥 Encounters**
```bash
GET    /api/v2/encounters         # List encounters with patient-based filtering
GET    /api/v2/encounters/{id}    # Get encounter by ID
POST   /api/v2/encounters         # Create new encounter
PUT    /api/v2/encounters/{id}    # Update encounter
DELETE /api/v2/encounters/{id}    # Delete encounter

# Query Parameters for GET /api/v2/encounters:
# - patient_id (patient-based filtering)
# - practitioner_id, organization_id, status
# - start_from, start_to (date range)
# - class_code, limit, offset
```

#### **🩺 Conditions**
```bash
GET    /api/v2/conditions         # List conditions with patient-based filtering
GET    /api/v2/conditions/{id}    # Get condition by ID
POST   /api/v2/conditions         # Create new condition
PUT    /api/v2/conditions/{id}    # Update condition
DELETE /api/v2/conditions/{id}    # Delete condition

# Query Parameters for GET /api/v2/conditions:
# - patient_id (patient-based filtering)
# - encounter_id, code, clinical_status
# - verification_status, category_code
# - onset_from, onset_to (date range)
```

#### **🏢 Organizations**
```bash
GET    /api/v2/organizations      # List organizations with filtering
GET    /api/v2/organizations/{id} # Get organization by ID
POST   /api/v2/organizations      # Create new organization
PUT    /api/v2/organizations/{id} # Update organization
DELETE /api/v2/organizations/{id} # Delete organization

# Query Parameters for GET /api/v2/organizations:
# - name, type_code, city, state
# - identifier, limit, offset
```

#### **👨‍⚕️ Practitioners**
```bash
GET    /api/v2/practitioners      # List practitioners with organization-based filtering
GET    /api/v2/practitioners/{id} # Get practitioner by ID
POST   /api/v2/practitioners      # Create new practitioner
PUT    /api/v2/practitioners/{id} # Update practitioner
DELETE /api/v2/practitioners/{id} # Delete practitioner

# Query Parameters for GET /api/v2/practitioners:
# - organization_id (organization-based filtering)
# - name, specialty_code, gender
# - identifier, limit, offset
```

#### **📊 Observations**
```bash
GET    /api/v2/observations      # List observations (filter by patient_id, code_display, etc.)
GET    /api/v2/observations/{id} # Get observation by ID

# Query Parameters for GET /api/v2/observations:
# - patient_id, code_display, code (LOINC)
# - limit, offset
```

### **🔍 Advanced Filtering Examples**

#### **Patient-Based Filtering**
```bash
# Get all encounters for patient 123
GET /api/v2/encounters?patient_id=123

# Get all conditions for patient 123
GET /api/v2/conditions?patient_id=123

# Get active conditions for patient 123
GET /api/v2/conditions?patient_id=123&clinical_status=active

# Get encounters for patient 123 in date range
GET /api/v2/encounters?patient_id=123&start_from=2024-01-01&start_to=2024-12-31
```

#### **Organization-Based Filtering**
```bash
# Get all practitioners at organization 1
GET /api/v2/practitioners?organization_id=1

# Get all cardiologists at organization 1
GET /api/v2/practitioners?organization_id=1&specialty_code=cardiology

# Get all hospitals in New York
GET /api/v2/organizations?state=NY&type_code=hospital
```

#### **Cross-Entity Queries**
```bash
# Get practitioners named "Smith"
GET /api/v2/practitioners?name=Smith

# Get organizations with "City" in name
GET /api/v2/organizations?name=City

# Get completed encounters
GET /api/v2/encounters?status=completed

# Get confirmed conditions
GET /api/v2/conditions?verification_status=confirmed
```

---

## 🏗️ API Architecture & Features

### **✅ Implemented Features**

#### **1. Complete CRUD Operations**
- **Create**: POST endpoints for all entities
- **Read**: GET endpoints with filtering and pagination
- **Update**: PUT endpoints for partial updates
- **Delete**: DELETE endpoints with proper error handling

#### **2. Advanced Filtering System**
- **Patient-Based Filtering**: Get encounters and conditions for specific patients
- **Organization-Based Filtering**: Get practitioners at specific organizations
- **Date Range Filtering**: Filter by time periods (onset, start, end dates)
- **Status Filtering**: Filter by clinical status, verification status, encounter status
- **Text Search**: Partial matching on names, codes, and identifiers

#### **3. Pagination & Performance**
- **Limit/Offset Pagination**: Control result set size
- **Default Limits**: 20 items per page, max 100
- **Ordered Results**: Consistent sorting for better UX
- **Database Indexes**: Optimized queries on frequently filtered fields

#### **4. Data Validation & Error Handling**
- **Pydantic Schemas**: Request/response validation
- **HTTP Status Codes**: Proper REST status codes (200, 201, 204, 404)
- **Error Messages**: Clear, descriptive error responses
- **Input Validation**: Query parameter constraints and validation

#### **5. API Documentation**
- **Swagger UI**: Interactive API documentation at `/docs`
- **ReDoc**: Alternative documentation at `/redoc`
- **OpenAPI Schema**: Machine-readable API specification
- **Endpoint Descriptions**: Detailed documentation for each endpoint

### **🔗 API Relationships**

```
Patient (Central Entity)
├── Encounters (visits, appointments)
├── Conditions (diagnoses, problems)
└── Observations (measurements, test results)

Organization (Healthcare Facility)
├── Practitioners (doctors, nurses)
└── Encounters (hosted visits)

Practitioner (Healthcare Provider)
├── Encounters (conducted visits)
└── Observations (performed tests)
```

### **📊 Response Formats**

#### **List Endpoints**
```json
[
  {
    "id": 1,
    "patient_id": 123,
    "status": "completed",
    "start_time": "2024-01-15T10:00:00"
  }
]
```

#### **Single Item Endpoints**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "birth_date": "1990-05-15",
  "active": true
}
```

#### **Error Responses**
```json
{
  "detail": "Patient not found"
}
```

---

## 🗃️ Tech Stack

### **Backend & API:**
- **Backend Framework**: FastAPI 0.116.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Data Validation**: Pydantic
- **API Documentation**: Swagger UI (OpenAPI)
- **Development Server**: Uvicorn

### **AI & Machine Learning:**
- **LLM Framework**: LangChain
- **AI Models**: Claude 3.5 Sonnet, Llama 3.3 70B, GPT-4o Mini, Gemini 2.5 Flash
- **AI Providers**: Anthropic, Groq, OpenAI, Google AI
- **Agent Framework**: Custom healthcare-focused agent system
- **Chat Interface**: Streamlit

### **DevOps & Deployment:**
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Code Quality**: Black, isort, flake8, mypy
- **Testing**: pytest with coverage reporting
- **Security**: Safety, Bandit security scanning

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- PostgreSQL (for API data); optional for AI chatbot only

### **Local development (recommended)**
```bash
# Clone the repository
git clone <your-repository-url>
cd AI-Powered-Healthcare-API

# Terminal 1: start backend (uses uv, loads .env)
./start-backend.sh
# API: http://localhost:8000  |  Docs: http://localhost:8000/docs

# Terminal 2: start Streamlit chatbot
./start-frontend.sh
# Chatbot: http://localhost:8501
```

### **Using Docker**
```bash
docker compose -f infra/compose/docker-compose.yml up -d
# API: http://localhost:8000  |  Chatbot: http://localhost:8501
```

### **Quick API testing**
```bash
./start-backend.sh
# Then open http://localhost:8000/docs (Swagger) or http://localhost:8000/redoc
```

### **Quick AI assistant testing**
```bash
./start-backend.sh   # Terminal 1
./start-frontend.sh # Terminal 2
# Open http://localhost:8501 and try: "What are patient 3's glucose levels?"
```

### **🔍 API Testing Examples**

#### **1. Test Patient-Based Filtering**
```bash
# Get all encounters for a patient
curl "http://localhost:8000/api/v2/encounters?patient_id=1&limit=5"

# Get all conditions for a patient
curl "http://localhost:8000/api/v2/conditions?patient_id=1&limit=5"

# Get all patients
curl "http://localhost:8000/api/v2/patients?limit=10"
```

#### **4. Test Organization-Based Filtering**
```bash
# Get practitioners at an organization
curl "http://localhost:8000/api/v2/practitioners?organization_id=1&limit=5"

# Get organizations by type
curl "http://localhost:8000/api/v2/organizations?type_code=hospital&limit=5"
```

#### **3. Create New Records**
```bash
# Create a new patient
curl -X POST "http://localhost:8000/api/v2/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "birth_date": "1990-05-15",
    "email": "john@example.com"
  }'

# Create a new encounter
curl -X POST "http://localhost:8000/api/v2/encounters" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "status": "completed",
    "start_time": "2024-01-15T10:00:00"
  }'
```

---

## 📊 Database Schema Visualization

View the complete database schema in [docs/database_uml_diagram.puml](docs/database_uml_diagram.puml).

---

## 🔧 Data Import

Import FHIR bundle data from the project root (requires PostgreSQL and tables created):

```bash
cd backend/src
PYTHONPATH=. python scripts/import_patients_v2.py
PYTHONPATH=. python scripts/import_practitioners_v2.py
PYTHONPATH=. python scripts/import_encounters_v2.py
PYTHONPATH=. python scripts/import_conditions_v2.py
PYTHONPATH=. python scripts/import_observations_v2.py
PYTHONPATH=. python scripts/import_organizations_v2.py
```

---

## 🧪 Testing

```bash
# Run tests (from project root)
cd backend/src && PYTHONPATH=. pytest tests/ -v

# Or with uv from project root
PYTHONPATH=backend/src uv run pytest backend/src/tests/ -v

# Test database connection
python test_db_conn.py
```

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Server won't start**
```bash
# Free port 8000 if needed (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Start backend again
./start-backend.sh
```

#### **2. Database connection**
```bash
python test_db_conn.py
# Create tables: from backend/src, PYTHONPATH=. python -c "from api.v2.create_tables_v2 import *; create_tables()"
```

#### **3. Import errors**
Run from project root; use `./start-backend.sh` or set `PYTHONPATH=backend/src` when running scripts.

#### **4. No data in API**
Ensure PostgreSQL is running and tables exist. Import data from `backend/src` with `PYTHONPATH=.` (see Data Import).

#### **5. API not found**
- Use base URL: `http://localhost:8000/api/v2/`
- Check server: http://localhost:8000/docs

### **Health Check**
```bash
# Test if API is running
curl http://localhost:8000/api/v2/health

# Expected response: {"status": "ok", "api": "v2"}
```

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


---

## 🤝 Acknowledgments

- Built following FHIR (Fast Healthcare Interoperability Resources) standards
- Inspired by real-world healthcare data management challenges
- Uses industry-standard technologies for healthcare applications



