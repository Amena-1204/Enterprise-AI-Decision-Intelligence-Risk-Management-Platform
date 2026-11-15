# Enterprise AI Decision Intelligence & Risk Management Platform

A production-grade platform combining machine learning, explainable AI, RAG, and AI agents to deliver real-time business intelligence, churn prediction, fraud detection, and sales forecasting.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                     Flask Backend                            │
│  Auth │ Customers │ Predictions │ Dashboard │ AI Assistant   │
└──────┬───────────┬──────────────┬───────────────────────────┘
       │           │              │
┌──────▼──┐  ┌─────▼──────┐  ┌───▼──────────────────────────┐
│  MySQL  │  │  ML Models  │  │        AI Layer               │
│ Database│  │ Churn/Fraud │  │  LLM │ RAG │ Agents │ SHAP   │
└─────────┘  │ Sales/Seg.  │  └──────────────────────────────┘
             └─────────────┘
```

---

## Features

- **Customer Churn Prediction** — RandomForest/XGBoost with SHAP explainability
- **Fraud Detection** — Real-time transaction risk scoring with 4 risk levels
- **Sales Forecasting** — Time-series forecasting with lag/rolling features
- **Customer Segmentation** — KMeans clustering (High Value, Loyal, At Risk, New, Low Engagement)
- **AI Assistant** — Natural language queries routed to specialized agents
- **RAG Pipeline** — Document indexing and retrieval (PDF, DOCX, TXT)
- **Dashboard API** — Aggregated KPIs for frontend dashboards
- **MLOps** — MLflow experiment tracking, model monitoring, retraining workflow
- **Security** — JWT auth, PBKDF2 password hashing, RBAC, audit logging

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0 |
| Database | MySQL 8.0 |
| ML | scikit-learn, XGBoost, SHAP |
| AI/LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI / sentence-transformers |
| Vector Store | FAISS |
| MLOps | MLflow |
| Containerization | Docker, Docker Compose |
| Testing | pytest |

---

## Folder Structure

```
enterprise-ai-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Application factory
│   │   ├── config.py            # Environment-based config
│   │   ├── routes/              # Flask blueprints
│   │   ├── models/              # DB model classes
│   │   ├── services/            # Business logic
│   │   ├── ai/                  # LLM, RAG, agents
│   │   ├── database/            # Connection pool, schema, seed
│   │   └── utils/               # Security, validators, logger
│   ├── run.py
│   └── requirements.txt
├── ml/
│   ├── preprocessing/           # Data cleaning, feature engineering
│   ├── training/                # train_churn/fraud/sales/segmentation
│   ├── evaluation/              # evaluate_*.py scripts
│   ├── inference/               # predictor.py (unified inference)
│   └── models/                  # Saved .pkl model bundles
├── mlops/
│   ├── mlflow/tracking.py       # MLflow utilities
│   ├── monitoring/monitor.py    # Drift detection
│   └── retraining/retrain.py    # Retraining workflow
├── documents/                   # RAG source documents
├── tests/                       # pytest test suite
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── .env.example
```

---

## Database Setup

### Tables Created
`users`, `customers`, `products`, `transactions`, `sales`, `support_tickets`,
`churn_predictions`, `fraud_predictions`, `sales_predictions`, `customer_segments`,
`ai_queries`, `ai_responses`, `documents`, `model_versions`, `audit_logs`

### Manual Setup
```bash
mysql -u root -p < backend/app/database/schema.sql
mysql -u root -p enterprise_ai < backend/app/database/seed.sql
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_SECRET_KEY` | Flask session secret | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | Yes |
| `DB_HOST` | MySQL host | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | DB username | Yes |
| `DB_PASSWORD` | DB password | Yes |
| `OPENAI_API_KEY` | OpenAI API key (for AI features) | No |
| `LLM_MODEL` | LLM model name | No |
| `MLFLOW_TRACKING_URI` | MLflow server URL | No |

---

## Local Installation

```bash
# 1. Clone and enter project
cd enterprise-ai-platform

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your DB credentials and API keys

# 5. Set up database
mysql -u root -p < backend/app/database/schema.sql
mysql -u root -p enterprise_ai < backend/app/database/seed.sql
```

---

## Docker Setup

```bash
# Copy env file
cp .env.example .env
# Edit .env — set FLASK_SECRET_KEY, JWT_SECRET_KEY, DB_PASSWORD

# Build and start all services
cd docker
docker-compose up --build

# Services:
#   Backend:  http://localhost:5000
#   MLflow:   http://localhost:5001
#   Frontend: http://localhost:3000
#   MySQL:    localhost:3306
```

---

## Running the Backend

```bash
# Development
cd enterprise-ai-platform
export PYTHONPATH=$(pwd)
python backend/run.py

# Or with Flask CLI
export FLASK_APP=backend/run.py
flask run --port 5000
```

---

## Running ML Training

```bash
# From project root with PYTHONPATH set
export PYTHONPATH=$(pwd)

# Train all models
python -m ml.training.train_churn
python -m ml.training.train_fraud
python -m ml.training.train_sales
python -m ml.training.train_segmentation

# Or retrain all at once
python -m mlops.retraining.retrain --model all

# Evaluate models
python -m ml.evaluation.evaluate_churn
python -m ml.evaluation.evaluate_fraud
python -m ml.evaluation.evaluate_sales
```

---

## Running Tests

```bash
# From project root
export PYTHONPATH=$(pwd)
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v
pytest tests/test_ml.py -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## API Documentation

### Authentication

```
POST /api/auth/register
POST /api/auth/login
```

All other endpoints require: `Authorization: Bearer <token>`

### Customers
```
GET    /api/customers?limit=100&offset=0
GET    /api/customers/<id>
POST   /api/customers
PUT    /api/customers/<id>
DELETE /api/customers/<id>
```

### Predictions
```
GET    /api/predictions/churn
POST   /api/predictions/churn
GET    /api/predictions/fraud
POST   /api/predictions/fraud
GET    /api/predictions/sales
POST   /api/predictions/sales
```

### Dashboard
```
GET    /api/dashboard/summary
```

### AI Assistant
```
POST   /api/ai/ask
POST   /api/ai/report
POST   /api/ai/index-documents
```

### Sales & Fraud
```
GET    /api/sales
GET    /api/sales/summary
GET    /api/fraud
GET    /api/fraud/regional
GET    /api/churn
GET    /api/churn/at-risk
```

### Admin
```
POST   /api/admin/retrain    (admin role required)
```

---

## Example API Requests

### Register & Login
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@company.com","password":"AdminPass1","role":"admin"}'

curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"AdminPass1"}'
```

### Churn Prediction
```bash
curl -X POST http://localhost:5000/api/predictions/churn \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 5,
    "days_since_last_purchase": 120,
    "total_orders": 3,
    "lifetime_value": 800,
    "support_tickets": 4
  }'
```

### AI Assistant
```bash
curl -X POST http://localhost:5000/api/ai/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Which customers have the highest churn risk?"}'

curl -X POST http://localhost:5000/api/ai/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Which region has the highest fraud rate?"}'
```

### Dashboard
```bash
curl http://localhost:5000/api/dashboard/summary \
  -H "Authorization: Bearer <token>"
```

---

## Screenshots

> _Add dashboard screenshots here_

---

## Future Improvements

- [ ] Real-time streaming predictions via WebSocket
- [ ] Advanced SHAP waterfall plots served as API responses
- [ ] Multi-tenant support with organization isolation
- [ ] Automated retraining scheduler (Celery/APScheduler)
- [ ] React dashboard with Chart.js visualizations
- [ ] Slack/email alerting for high-risk customers
- [ ] A/B testing framework for model comparison
- [ ] GraphQL API layer
- [ ] Kubernetes deployment manifests
