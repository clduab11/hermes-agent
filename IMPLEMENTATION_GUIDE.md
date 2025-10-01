# 🚀 HERMES Marketing Command Center - Implementation Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying and using the HERMES Marketing Command Center, a complete marketing automation suite for law firms.

## ✨ Features

### 🎯 Lead Pipeline Management
- Track law firm prospects through the sales funnel
- Manage lead status from initial contact to closed deals
- Calculate pipeline value and win probability
- Filter and search by status, source, and practice area

### 📱 Social Media Content Generator
- AI-powered content generation for LinkedIn, Facebook, Instagram
- Platform-specific templates optimized for legal industry
- Practice area targeting (Personal Injury, Family Law, Criminal Defense, etc.)
- Bulk scheduling with calendar view
- Performance analytics tracking

### 📊 Marketing Analytics Dashboard
- Real-time conversion funnel metrics
- Pipeline value calculations with probability weighting
- Social media performance tracking (impressions, engagement, clicks)
- ROI calculator showing cost savings and revenue impact
- Comprehensive reporting across all marketing channels

### ⚙️ Zapier Integration
- Connect to 8,000+ apps via webhooks
- Automated workflows for lead capture and follow-up
- Event-driven triggers for CRM sync
- Webhook event logging and retry mechanism

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Style**: RESTful with Pydantic validation
- **Authentication**: Tenant-based isolation

### Frontend
- **Framework**: React 18.x with Vite 6.x
- **Routing**: React Router 6.x
- **State Management**: TanStack Query (React Query) 5.x
- **Styling**: Tailwind CSS 3.x + DaisyUI 4.x
- **Charts**: Chart.js 4.x with react-chartjs-2
- **HTTP Client**: Axios

## 📁 Project Structure

```
hermes-agent/
├── hermes/                              # Backend
│   ├── api/
│   │   ├── leads_endpoints.py          # Lead management API
│   │   ├── social_endpoints.py         # Social media API
│   │   ├── marketing_analytics_endpoints.py  # Analytics API
│   │   └── webhooks_endpoints.py       # Zapier webhooks API
│   ├── database/
│   │   └── models.py                   # Database models
│   ├── services/
│   │   ├── zapier_service.py          # Zapier integration
│   │   ├── social_service.py          # Social media logic
│   │   └── analytics_service.py       # Analytics calculations
│   └── main.py                         # FastAPI app with routes
├── frontend/                            # Frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── dashboard/             # Dashboard components
│   │   ├── pages/                     # Page components
│   │   ├── services/
│   │   │   └── api.js                 # API client
│   │   └── App.jsx                    # Main app with routing
│   ├── tailwind.config.js             # Tailwind configuration
│   └── package.json                    # Frontend dependencies
└── alembic/
    └── versions/
        └── 003_marketing_tables.py     # Database migration
```

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **PostgreSQL**: 14 or higher
- **Git**: For cloning the repository

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/clduab11/hermes-agent.git
   cd hermes-agent
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/hermes
   
   # API Configuration
   DEBUG=false
   DEMO_MODE=false
   
   # CORS Origins (for frontend)
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   
   # Optional: OpenAI for enhanced content generation
   OPENAI_API_KEY=your_openai_key
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn hermes.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the `frontend` directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173` (or `http://localhost:3000`)

5. **Build for production**
   ```bash
   npm run build
   ```

   Production files will be in the `dist` directory.

## 🔧 Configuration

### Database Models

Three new tables are created by the migration:

#### `leads` Table
Stores law firm prospect information:
- Basic info: firm name, contact details
- Status tracking: new → contacted → qualified → demo → proposal → won/lost
- Pipeline metrics: value, probability, expected close date
- Source tracking: website, referral, social media, campaigns

#### `social_posts` Table
Manages social media content:
- Platform: LinkedIn, Facebook, Instagram, Twitter
- Content and media URLs
- Scheduling: draft, scheduled, published
- Analytics: impressions, engagements, clicks, conversions

#### `webhook_events` Table
Logs integration events:
- Event type and source (Zapier, Clio, etc.)
- Payload data
- Processing status and retry tracking

### API Endpoints

#### Leads API
- `GET /api/leads` - List all leads (with filters)
- `GET /api/leads/{id}` - Get specific lead
- `POST /api/leads` - Create new lead
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead

#### Social Media API
- `GET /api/social/posts` - List posts (with filters)
- `GET /api/social/posts/{id}` - Get specific post
- `POST /api/social/posts` - Create new post
- `POST /api/social/generate` - Generate AI content
- `POST /api/social/posts/{id}/schedule` - Schedule post
- `POST /api/social/posts/{id}/publish` - Publish post

#### Marketing Analytics API
- `GET /api/marketing/analytics/metrics` - Get all metrics
- `GET /api/marketing/analytics/funnel` - Get conversion funnel
- `GET /api/marketing/analytics/pipeline` - Get pipeline value
- `GET /api/marketing/analytics/social` - Get social performance
- `GET /api/marketing/analytics/roi` - Get ROI metrics

#### Webhooks API
- `POST /api/webhooks/incoming` - Receive webhook from Zapier
- `POST /api/webhooks/trigger` - Trigger outgoing webhook
- `GET /api/webhooks/events` - List webhook events
- `GET /api/webhooks/events/{id}` - Get specific event

## 📊 Usage Examples

### Creating a Lead via API

```bash
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "firm_name": "Smith & Associates",
    "contact_name": "John Smith",
    "contact_email": "john@smithlaw.com",
    "contact_phone": "+1-555-0100",
    "status": "new",
    "firm_size": "11-50",
    "practice_areas": ["personal_injury", "family_law"],
    "jurisdiction": "CA",
    "pipeline_value": 7497,
    "probability": 25,
    "source": "website",
    "campaign": "2025-Q1-PPC"
  }'
```

### Generating Social Media Content

```bash
curl -X POST http://localhost:8000/api/social/generate \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "practice_area": "personal_injury",
    "content_type": "thought_leadership"
  }'
```

### Getting Dashboard Metrics

```bash
curl http://localhost:8000/api/marketing/analytics/metrics
```

### Zapier Webhook Integration

**Incoming webhook (from Zapier):**
```bash
curl -X POST http://localhost:8000/api/webhooks/incoming \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "lead.created",
    "source": "zapier",
    "data": {
      "firm_name": "New Law Firm",
      "contact_email": "contact@newlawfirm.com",
      "source": "facebook_ad"
    }
  }'
```

**Outgoing webhook (to Zapier):**
```bash
curl -X POST http://localhost:8000/api/webhooks/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://hooks.zapier.com/hooks/catch/123456/abcdef/",
    "payload": {
      "event": "lead.won",
      "lead_id": 42,
      "firm_name": "Smith & Associates",
      "value": 7497
    }
  }'
```

## 🎨 Frontend Usage

### Dashboard Navigation

The Marketing Command Center is accessible at `/dashboard` and includes:

1. **Overview** (`/dashboard`) - Key metrics and charts
2. **Leads** (`/dashboard/leads`) - Lead pipeline management
3. **Social Media** (`/dashboard/social`) - Content creation and scheduling
4. **Analytics** (`/dashboard/analytics`) - Detailed performance metrics
5. **Technical Docs** (`/dashboard/technical`) - API documentation

### Lead Management Workflow

1. Click "Add New Lead" to create a new prospect
2. Fill in firm details, contact info, and pipeline value
3. Filter leads by status, source, or other criteria
4. Click "Edit" to update lead information
5. Track progression through the sales funnel

### Social Media Content Generation

1. Navigate to Social Media page
2. Click "Generate Content" button
3. Select platform (LinkedIn, Facebook, Instagram)
4. Choose practice area and content type
5. Click "Generate Content" to create AI-powered post
6. Edit the generated content if needed
7. Save as draft or schedule for publication

### Analytics Dashboard

View comprehensive metrics including:
- Total leads and conversion rates
- Pipeline value (total and weighted)
- Social media performance
- ROI calculations and cost savings

## 🔐 Security Considerations

### Multi-Tenant Isolation
All API endpoints support tenant-based isolation via the `tenant_id` field. Ensure proper tenant context is set for production deployments.

### Input Validation
All endpoints use Pydantic models for request validation, preventing SQL injection and malformed data.

### CORS Configuration
Configure `CORS_ORIGINS` environment variable to restrict frontend access to authorized domains only.

### Authentication
The current implementation includes authentication middleware. Ensure API keys or JWT tokens are properly configured for production use.

## 🐛 Troubleshooting

### Database Connection Errors
```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -l

# Test connection
psql postgresql://user:password@localhost:5432/hermes
```

### Frontend Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

### API Not Responding
```bash
# Check if port 8000 is available
lsof -i :8000

# View application logs
tail -f logs/hermes.log

# Test API endpoint
curl http://localhost:8000/health
```

### Migration Errors
```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Rollback one version
alembic downgrade -1

# Re-apply migrations
alembic upgrade head
```

## 📈 Performance Optimization

### Database Indexing
The migration automatically creates indexes on frequently queried fields:
- `leads`: firm_name, contact_email, status, tenant_id
- `social_posts`: platform, status, scheduled_time, tenant_id
- `webhook_events`: event_type, source, processed, tenant_id

### API Response Caching
Consider implementing Redis caching for analytics endpoints that aggregate large datasets.

### Frontend Optimization
- React Query automatically caches API responses
- Use pagination for large result sets
- Implement virtual scrolling for long lists

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_leads_api.py

# Run with coverage
pytest --cov=hermes --cov-report=html
```

### Frontend Testing
```bash
# Run tests (when implemented)
npm test

# Run in watch mode
npm test -- --watch
```

### Manual API Testing
Use the interactive API documentation at `http://localhost:8000/docs` to test all endpoints with a visual interface.

## 🚀 Deployment

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "hermes.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: hermes
      POSTGRES_USER: hermes
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://hermes:${DB_PASSWORD}@postgres:5432/hermes
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Production Checklist

- [ ] Set `DEBUG=false` in environment variables
- [ ] Configure production database with connection pooling
- [ ] Set up SSL/TLS certificates for HTTPS
- [ ] Configure CORS origins for production domains
- [ ] Set up monitoring and logging (e.g., Sentry, CloudWatch)
- [ ] Implement backup strategy for database
- [ ] Configure rate limiting on API endpoints
- [ ] Set up CDN for frontend static assets
- [ ] Enable gzip compression
- [ ] Configure health check endpoints for load balancer

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Router Documentation](https://reactrouter.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [DaisyUI Components](https://daisyui.com/components/)

### API Reference
- Full API documentation available at `/docs` endpoint
- OpenAPI schema available at `/openapi.json`

### Support
- GitHub Issues: https://github.com/clduab11/hermes-agent/issues
- Email: info@parallax-ai.app
- Phone: +1 (662) 848-3547

## 📝 License

Copyright (c) 2025 Parallax Analytics LLC. All Rights Reserved.

---

**Built with ❤️ by the Legal Technology Experts at Parallax Analytics**
