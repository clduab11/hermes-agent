# MCP Server Configuration Guide

## Overview

HERMES utilizes the Model Context Protocol (MCP) to integrate with various external systems and services. This document provides detailed configuration instructions for each MCP server component.

## Quick Setup

### 1. Install MCP Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Clio CRM Integration
CLIO_CLIENT_ID=your_clio_client_id
CLIO_CLIENT_SECRET=your_clio_client_secret
CLIO_REDIRECT_URI=https://your-domain.com/oauth/clio/callback

# Zapier Integration
ZAPIER_API_KEY=your_zapier_api_key

# GitHub Repository Management
GITHUB_TOKEN=your_github_personal_access_token

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key

# Mem0 Knowledge Graph
MEM0_API_KEY=your_mem0_api_key
```

### 3. Initialize MCP Servers

```bash
python -m hermes.mcp.init --config mcp-config.json
```

## Detailed Server Configuration

### Clio CRM Integration

The Clio MCP server handles:
- Matter management and case file operations
- Client data synchronization
- Time tracking and billing integration
- Document management and sharing

**Setup Steps:**

1. **Create Clio App**
   - Log into your Clio account
   - Navigate to API/Integrations settings
   - Create a new application with the following scopes:
     - `read:matters`
     - `write:matters`
     - `read:contacts`
     - `write:contacts`
     - `read:activities`
     - `write:activities`

2. **Configure OAuth Flow**
   ```python
   # Example configuration
   CLIO_CONFIG = {
       "client_id": "your_client_id",
       "client_secret": "your_client_secret",
       "redirect_uri": "https://your-domain.com/oauth/clio/callback",
       "scopes": ["read:matters", "write:matters", "read:contacts", "write:contacts"]
   }
   ```

3. **Test Connection**
   ```bash
   python -m hermes.mcp.test clio-integration
   ```

### Zapier Automation

Enables workflow automation across 5,000+ applications.

**Configuration:**

1. **Get API Key**
   - Log into Zapier Developer Platform
   - Create a new app or use existing
   - Generate API key with appropriate permissions

2. **Configure Webhooks**
   ```json
   {
     "webhooks": {
       "client_intake": "https://hooks.zapier.com/hooks/catch/12345/abcdef/",
       "matter_update": "https://hooks.zapier.com/hooks/catch/12345/ghijkl/",
       "appointment_scheduled": "https://hooks.zapier.com/hooks/catch/12345/mnopqr/"
     }
   }
   ```

### Supabase Database

Provides scalable PostgreSQL database for conversation logs and analytics.

**Setup:**

1. **Create Project**
   - Visit [Supabase Dashboard](https://supabase.com/dashboard)
   - Create new project
   - Note the project URL and API keys

2. **Initialize Schema**
   ```sql
   -- Run in Supabase SQL editor
   CREATE TABLE conversations (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     tenant_id UUID NOT NULL,
     client_phone VARCHAR(20) NOT NULL,
     transcript JSONB NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);
   CREATE INDEX idx_conversations_phone ON conversations(client_phone);
   ```

3. **Configure Row Level Security**
   ```sql
   ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
   
   CREATE POLICY "Tenant isolation" ON conversations
   FOR ALL USING (tenant_id = auth.jwt()->>'tenant_id');
   ```

### Mem0 Knowledge Graph

Manages legal context and client relationship intelligence.

**Configuration:**

1. **Get API Access**
   - Sign up at [Mem0 Platform](https://mem0.ai)
   - Generate API key from dashboard
   - Note your organization ID

2. **Initialize Knowledge Base**
   ```python
   # Example setup
   from mem0 import MemoryClient
   
   client = MemoryClient(api_key="your_api_key")
   
   # Create legal practice knowledge base
   client.create_entity({
       "name": "Legal Practice Areas",
       "type": "knowledge_base",
       "observations": [
           "Corporate law involves business formations and compliance",
           "Litigation requires court procedures and evidence management",
           "Real estate law covers property transactions and disputes"
       ]
   })
   ```

### Playwright Browser Automation

Enables automated legal research and form processing.

**Setup:**

1. **Install Browser Dependencies**
   ```bash
   playwright install chromium
   ```

2. **Configure Security**
   ```python
   PLAYWRIGHT_CONFIG = {
       "headless": True,
       "args": [
           "--no-sandbox",
           "--disable-dev-shm-usage",
           "--disable-gpu"
       ]
   }
   ```

## Security Configuration

### Environment Variable Management

Never commit sensitive data. Use a secrets management system in production:

```bash
set -a; source .env; set +a

# Production (use your platform's secret manager)
# Google Cloud: gcloud secrets versions access latest --secret="clio-client-secret"
# AWS: aws secretsmanager get-secret-value --secret-id clio-client-secret
```

### Network Security

Configure firewall rules to restrict MCP server access:

```bash
# Allow only HERMES application access
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

### Monitoring and Logging

Each MCP server includes comprehensive logging:

```python
# Example logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "filename": "/var/log/hermes/mcp-servers.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "syslog": {
            "address": ("localhost", 514),
            "facility": "local0"
        }
    }
}
```

## Testing MCP Servers

### Integration Tests

```bash
# Test all servers
python -m pytest tests/mcp/integration/

# Test specific server
python -m pytest tests/mcp/integration/test_clio.py -v

# Test with coverage
python -m pytest tests/mcp/ --cov=hermes.mcp --cov-report=html
```

### Health Checks

```bash
# Check server status
curl -X GET http://localhost:8000/mcp/health

# Check specific server
curl -X GET http://localhost:8000/mcp/clio/status
```

## Troubleshooting

### Common Issues

1. **OAuth Flow Failures**
   ```bash
   # Check redirect URI configuration
   python -m hermes.mcp.debug oauth --provider clio
   ```

2. **Database Connection Issues**
   ```bash
   # Test Supabase connection
   python -m hermes.mcp.debug database --provider supabase
   ```

3. **API Rate Limiting**
   ```bash
   # Check API quotas
   python -m hermes.mcp.debug quotas --all
   ```

### Log Analysis

```bash
# View recent MCP server logs
tail -f /var/log/hermes/mcp-servers.log

# Search for specific errors
grep -i "error\|exception" /var/log/hermes/mcp-servers.log | tail -20
```

## Performance Optimization

### Connection Pooling

```python
# Example connection pool configuration
DATABASE_CONFIG = {
    "max_connections": 20,
    "min_connections": 5,
    "connection_timeout": 30,
    "idle_timeout": 300
}
```

### Caching Strategy

```python
# Redis caching for frequently accessed data
CACHE_CONFIG = {
    "default_ttl": 3600,  # 1 hour
    "max_memory": "256mb",
    "eviction_policy": "allkeys-lru"
}
```

## Support

For technical support with MCP server configuration:

- 📧 Email: support@parallaxanalytics.com
- 📞 Phone: +1 (555) 123-4567
- 🌐 Documentation: https://docs.parallaxanalytics.com/hermes/mcp
- 💬 Community: https://community.parallaxanalytics.com

---

*This guide is part of the HERMES AI Voice Agent System documentation.*
*Copyright © 2024 Parallax Analytics LLC. All rights reserved.*