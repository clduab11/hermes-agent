# HERMES 🏛️
## High-performance Enterprise Reception & Matter Engagement System

**Production-grade AI voice agent platform for law firms**

HERMES is a 24/7 AI-powered voice agent designed specifically for law firms, handling client intake, matter management, CRM integration, and administrative workflows while maintaining attorney-client privilege and legal compliance.

> 📢 **For marketing materials and pricing information, see [MARKETING.md](MARKETING.md)**

---

## 🏗️ Architecture Overview

HERMES is built on a modern, cloud-native architecture:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │────▶│  FastAPI     │────▶│  Supabase    │
│  (Voice/Web) │     │  Backend     │     │  PostgreSQL  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────────┐ ┌──────────────┐
            │  OpenAI      │ │  Stripe      │
            │  (AI/Voice)  │ │  (Billing)   │
            └──────────────┘ └──────────────┘
```

### Core Technologies

- **Backend**: FastAPI (Python 3.11+), async/await architecture
- **Database**: Supabase (PostgreSQL) with Row-Level Security
- **AI/Voice**: OpenAI API (GPT-4, Whisper STT), Kokoro TTS
- **Billing**: Stripe (subscriptions, usage metering)
- **Integrations**: Clio CRM, LawPay, Zapier
- **Automation**: Playwright for web automation
- **Deployment**: Google Cloud Platform (App Engine)
- **Monitoring**: Prometheus metrics, Cloud Logging

---

## 📁 Project Structure

```
hermes/
├── hermes/                  # Main application package
│   ├── api/                # FastAPI routes and endpoints
│   ├── core/               # Core business logic
│   ├── integrations/       # External service integrations
│   ├── security/           # Security and compliance modules
│   ├── billing/            # Stripe billing integration
│   ├── voice/              # Voice pipeline components
│   └── main.py             # Application entry point
├── alembic/                # Database migrations
├── scripts/                # Deployment and utility scripts
├── deployment/             # Deployment configurations
├── docs/                   # Documentation
├── tests/                  # Test suite
├── static/                 # Static assets
├── templates/              # HTML templates
├── requirements.txt        # Python dependencies
├── app.yaml                # GCP App Engine config
└── security.yaml           # Security headers config
```

---

## 🚀 Quick Start

See **[QUICKSTART.md](QUICKSTART.md)** for detailed local development setup instructions.

### Prerequisites

- Python 3.11+
- Google Cloud account (for deployment)
- Supabase project
- OpenAI API key
- Stripe account (for billing features)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/clduab11/hermes-agent.git
cd hermes-agent

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn hermes.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for the interactive API documentation.

---

## 🚢 Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete production deployment instructions.

### Prerequisites

Before deploying, review:
- **[DEPLOYMENT_PREREQUISITES.md](DEPLOYMENT_PREREQUISITES.md)** - Required accounts and services
- **[COST_ESTIMATION.md](COST_ESTIMATION.md)** - Monthly cost breakdown
- **[SECURITY.md](SECURITY.md)** - Security checklist

### Deployment Process

```bash
# 1. Validate prerequisites
./scripts/validate-production.sh --pre-deploy

# 2. Configure secrets
./scripts/generate-secrets.sh
./scripts/upload-secrets.sh

# 3. Setup VPC connector (if needed)
./scripts/setup-vpc-connector.sh

# 4. Deploy to GCP
./scripts/deploy-gcp.sh
```

---

## 🔒 Security & Compliance

HERMES implements enterprise-grade security:

- **Authentication**: JWT-based auth with RS256
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Secrets Management**: GCP Secret Manager (production)
- **Database**: Row-Level Security (RLS) policies
- **Audit Logging**: Immutable logs for compliance
- **Rate Limiting**: API rate limits per endpoint

### Compliance Features

- HIPAA-compliant data handling
- GDPR data protection support
- Attorney-client privilege protection
- SOC 2 security controls

See **[SECURITY.md](SECURITY.md)** for complete security documentation.

---

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=hermes --cov-report=html tests/

# Run integration tests
pytest tests/integration/

# Run E2E tests
python tests/e2e_test_suite.py
```

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Local development setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[DEPLOYMENT_PREREQUISITES.md](DEPLOYMENT_PREREQUISITES.md)** - Required services
- **[COST_ESTIMATION.md](COST_ESTIMATION.md)** - Cost breakdown
- **[SECURITY.md](SECURITY.md)** - Security documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[MARKETING.md](MARKETING.md)** - Marketing and pricing info
- **docs/services/** - External service setup guides
  - [Supabase Setup](docs/services/supabase-setup.md)
  - [Stripe Setup](docs/services/stripe-setup.md)
  - [OpenAI Setup](docs/services/openai-setup.md)
  - [Redis Setup](docs/services/redis-setup.md)
  - [GCP Secret Manager](docs/services/gcp-secret-manager-setup.md)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code style guidelines (PEP 8, type hints, docstrings)
- Development workflow
- Testing requirements
- Pull request process

---

## 📄 License

See [LICENSE](LICENSE) for license information.

---

## 📞 Support

- **Technical Issues**: Create an issue on GitHub
- **Security Issues**: security@parallax-ai.app
- **General Contact**: info@parallax-ai.app

---

**© 2024 Parallax Analytics LLC. All rights reserved.**