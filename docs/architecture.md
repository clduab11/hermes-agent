
# HERMES Architecture Documentation

## System Overview

HERMES is a microservices-based AI voice agent system designed for law firms, featuring MCP (Model Context Protocol) orchestration for intelligent automation.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HERMES AI Voice Agent System                 │
├─────────────────────────────────────────────────────────────────┤
│  Client Layer                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Web UI    │  │ Mobile App  │  │  API Clients │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
                    ┌───────────────────┐
                    │   Load Balancer   │
                    └───────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application Layer                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ REST API    │  │ WebSocket   │  │ Auth Layer  │             │
│  │ Endpoints   │  │ Handler     │  │ (JWT)       │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Orchestration Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Orchestrator│  │ Database    │  │ Knowledge   │             │
│  │   Manager   │  │ Optimizer   │  │ Integrator  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                      Voice Processing Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Whisper   │  │ OpenRouter  │  │   Kokoro    │             │
│  │    STT      │  │    LLM      │  │    TTS      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                      External MCP Servers                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Supabase   │  │    Mem0     │  │   GitHub    │             │
│  │  Database   │  │ Knowledge   │  │Version Ctrl │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Puppeteer   │  │ Omnisearch  │  │ Sequential  │             │
│  │ Browser     │  │Multi-Search │  │ Thinking    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Application Layer

**Purpose**: HTTP/WebSocket API server with authentication and routing

**Key Components**:
- REST API endpoints for system control
- WebSocket handler for real-time voice interactions  
- JWT authentication middleware with tenant isolation
- Request/response logging and error handling

**Technologies**: FastAPI, Uvicorn, Pydantic, python-jose

### 2. MCP Orchestration Layer

**Purpose**: Intelligent coordination of multiple AI/automation services

**Key Components**:
- **MCP Orchestrator**: Central coordinator for strategic tasks
- **Database Optimizer**: Redis caching + Supabase optimization
- **Knowledge Integrator**: Mem0 knowledge graph + search integration

**Technologies**: Custom MCP clients, asyncio, httpx

### 3. Voice Processing Layer

**Purpose**: Real-time speech processing with <100ms latency

**Key Components**:
- **Speech-to-Text**: OpenAI Whisper for accurate transcription
- **Language Model**: OpenRouter API with multiple 8B LLMs
- **Text-to-Speech**: Kokoro FastAPI for natural voice synthesis
- **Voice Pipeline**: Orchestrates STT → LLM → TTS flow

**Technologies**: OpenAI Whisper, OpenRouter API, Kokoro TTS

### 4. External MCP Servers

**Purpose**: Specialized services for enhanced capabilities

**Services**:
- **Supabase**: Multi-tenant database with row-level security
- **Mem0**: Persistent knowledge graph with relationship learning
- **GitHub**: Automated documentation and version control
- **Puppeteer**: Browser automation for UI testing
- **mcp-omnisearch**: Multi-provider legal research
- **sequential-thinking**: Complex decision tree reasoning

## Data Flow Architecture

### Voice Interaction Flow

1. **Audio Input** → WebSocket connection receives audio stream
2. **Speech Recognition** → Whisper processes audio to text
3. **Context Enrichment** → Knowledge Integrator adds legal context
4. **AI Processing** → LLM generates response with legal safety checks
5. **Speech Synthesis** → Kokoro converts response to audio
6. **Audio Output** → WebSocket streams audio back to client
7. **Learning** → Interaction data updates knowledge graph

### MCP Orchestration Flow

1. **Task Request** → API receives strategic task execution request
2. **Server Coordination** → Orchestrator determines required MCP servers
3. **Parallel Execution** → Multiple MCP servers execute concurrently
4. **Result Synthesis** → Orchestrator combines and validates results
5. **State Updates** → Database and knowledge graph updated
6. **Response** → Consolidated results returned to client

## Security Architecture

### Multi-Tenant Isolation

- **Database Level**: Supabase row-level security policies
- **API Level**: JWT tokens with tenant_id claims  
- **Cache Level**: Redis namespacing by tenant
- **Knowledge Level**: Tenant-specific knowledge graph partitions

### Data Protection

- **Encryption**: TLS 1.3 for all communications
- **Authentication**: RS256 JWT with key rotation
- **Authorization**: Role-based access control
- **Audit**: Comprehensive logging for compliance

### Legal Compliance

- **HIPAA**: Encrypted storage, access controls, audit trails
- **GDPR**: Data minimization, right to deletion, consent tracking
- **Attorney-Client Privilege**: Confidentiality protections built-in

## Performance Architecture

### Latency Optimization

- **Target**: <100ms voice processing, <500ms total response
- **Caching**: Redis for conversation state and knowledge
- **Connection Pooling**: Database and external API connections
- **Async Processing**: Non-blocking I/O throughout pipeline

### Scalability Design

- **Horizontal Scaling**: Cloud Run auto-scaling (1-100 instances)
- **Load Distribution**: Connection-based WebSocket load balancing
- **Resource Management**: Per-tenant resource quotas and throttling
- **Caching Strategy**: Multi-level caching (Redis, application, CDN)

## Monitoring and Observability

### Metrics Collection

- **Performance**: Response times, throughput, error rates
- **Business**: Conversation counts, user satisfaction, billing metrics
- **Technical**: CPU/memory usage, database performance, MCP health
- **Legal**: Compliance violations, audit events, data retention

### Alerting Strategy

- **Critical**: System outages, security breaches, legal violations
- **Warning**: Performance degradation, high error rates, capacity limits
- **Info**: Successful deployments, scheduled maintenance, usage reports

## Deployment Architecture

### Google Cloud Platform

- **Cloud Run**: Serverless container platform for main application
- **Cloud SQL**: Managed PostgreSQL for persistent data
- **Cloud Storage**: File storage for audio/document processing
- **Cloud CDN**: Global content delivery network
- **Cloud Logging**: Centralized log aggregation
- **Cloud Monitoring**: Metrics and alerting

### CI/CD Pipeline

- **Source**: GitHub repository with branch protection
- **Build**: Docker container build with security scanning
- **Test**: Automated testing including legal compliance checks
- **Deploy**: Blue-green deployment to Cloud Run
- **Validate**: Post-deployment health checks and smoke tests

## Disaster Recovery

### Backup Strategy

- **Database**: Automated daily backups with 30-day retention
- **Knowledge Graph**: Mem0 cloud backup with versioning
- **Configuration**: Infrastructure as Code in version control
- **Secrets**: Google Secret Manager with rotation

### Recovery Procedures

- **RTO**: 4 hours for full system recovery
- **RPO**: 1 hour maximum data loss
- **Failover**: Automated region failover for critical services
- **Testing**: Monthly disaster recovery drills

## Future Architecture Considerations

### Planned Enhancements

- **Multi-Region**: Global deployment for reduced latency
- **Edge Computing**: Voice processing at edge locations
- **Advanced AI**: Custom fine-tuned models for legal domain
- **Integration Expansion**: Additional CRM and legal software
- **Mobile SDK**: Native mobile applications
- **API Gateway**: Centralized API management and analytics
        