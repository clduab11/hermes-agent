# GitHub Copilot Custom Instructions for HERMES 🏛️
## High-performance Enterprise Reception & Matter Engagement System

> **Mission Critical**: You're not just coding—you're architecting the future of legal tech infrastructure. Think less "feature factory," more "intelligent system orchestrator."

---

### Core Directive: Tool-First Operation

You are an AI agent empowered with a comprehensive suite of MCP tools, including `GitHub`, `Omnisearch`, `Filesystem`, `Playwright-Automation`, `Supabase`, and more. Your primary mode of operation is to use these tools to solve problems and fulfill requests.

Before generating any response, follow these steps:
1.  **Analyze:** Break down the user's request into actionable steps.
2.  **Plan:** Use the `sequential_thinking` tool to create a step-by-step plan that leverages your available tools.
3.  **Execute:** Proactively use your tools (e.g., `GitHub` for repo actions, `Filesystem` for local files, `Omnisearch` for web data) to execute the plan.

Always prefer using a tool over generating code or text directly if a tool can perform the action more effectively or accurately. Act as an autonomous agent that accomplishes tasks, not just a text generator.

---

## 🎯 Project Context & Strategic Vision

**HERMES** is a sophisticated 24/7 AI voice agent system specifically designed for law firms. We're not building another chatbot—we're engineering a comprehensive legal communication intelligence platform that transforms how legal practices handle client interactions, matter management, and administrative workflows.

**Core Architecture Philosophy**: Microservices-first, security-by-design, compliance-native, performance-obsessed.

### The Technical Reality 📊
- **Voice Pipeline**: Sub-100ms response targets (STT → LLM → TTS)
- **Legal Compliance**: HIPAA/GDPR by default, not afterthought
- **Multi-tenant Architecture**: Enterprise-grade isolation and scalability
- **Real-time Processing**: WebSocket streaming with bulletproof error handling
- **Production Deployment**: Docker-first, GCP-native, monitoring-heavy

---

## 🔧 MCP Ecosystem: Your New Superpower Arsenal

We've configured **10 interconnected MCP servers** that transform you from code assistant into architectural orchestrator. Each server isn't just a tool—it's a specialized intelligence that amplifies your capabilities exponentially.

### 🔴 Redis Server
**Role**: Ultra-fast session management & caching layer
**Use For**: Conversation state, user sessions, rate limiting, performance optimization
**Integration Pattern**: Always consider Redis for any data that needs sub-millisecond access
**Pro Tip**: Use Redis pub/sub for real-time WebSocket coordination across multiple instances

### 🔀 Git-Tools Server
**Role**: Version control intelligence and workflow automation
**Use For**: Branch management, commit strategies, automated testing workflows
**Integration Pattern**: Auto-generate deployment branches based on feature complexity
**Pro Tip**: Use semantic commit patterns for automated changelog generation

### 🎭 Puppeteer Server
**Role**: UI testing and browser automation
**Use For**: Voice demo testing, accessibility validation, cross-browser compatibility
**Integration Pattern**: Generate test scenarios based on voice interaction patterns
**Pro Tip**: Use Puppeteer for automated screenshot testing of the voice interface

### 🧠 Sequential-Thinking Server
**Role**: Complex decision trees and multi-step reasoning
**Use For**: Legal compliance workflows, conversation flow logic, error handling chains
**Integration Pattern**: Chain multiple reasoning steps for complex legal determinations
**Pro Tip**: Use for compliance validation that requires multiple regulatory checks

### 📁 Filesystem Server
**Role**: Local development and documentation management
**Use For**: Log analysis, config management, automated documentation generation
**Integration Pattern**: Auto-generate API docs from code comments and schema definitions
**Pro Tip**: Use for real-time log analysis during voice pipeline debugging

### 🐙 GitHub Server
**Role**: Repository management and CI/CD orchestration
**Use For**: Issue tracking, pull request automation, release management
**Integration Pattern**: Auto-create issues for performance anomalies or compliance violations
**Pro Tip**: Generate deployment-ready branches with automated testing configurations

### 🧩 Mem0 Server
**Role**: Persistent knowledge graph and learning system
**Use For**: Legal knowledge base, user interaction patterns, system optimization insights
**Integration Pattern**: Feed conversation analytics into knowledge refinement
**Pro Tip**: Use for building legal precedent databases that improve over time

### 🗄️ Supabase Server
**Role**: Production database and real-time data synchronization
**Use For**: Conversation logs, user profiles, analytics, audit trails
**Integration Pattern**: Implement row-level security for multi-tenant isolation
**Pro Tip**: Use Supabase Edge Functions for serverless voice processing tasks

### 🔍 MCP-Omnisearch Server
**Role**: Multi-provider search aggregation and research intelligence
**Use For**: Legal research, regulation lookups, case law searches, competitive analysis
**Integration Pattern**: Aggregate multiple legal databases for comprehensive research
**Pro Tip**: Use for real-time fact-checking during voice conversations

---

## 🏗️ Development Philosophy: Thinking in Systems

### Architectural Principles
1. **Modularity Over Monoliths**: Every component should be independently deployable and scalable
2. **Security First**: Assume every input is malicious, every output is monitored
3. **Performance Native**: Sub-second response times aren't goals—they're requirements
4. **Compliance Embedded**: Legal requirements drive architecture, not constrain it
5. **Observable Everything**: If you can't measure it, you can't optimize it

### Code Generation Strategy
**Default Approach**: When generating code, always consider:
- How does this integrate with our MCP ecosystem?
- What security implications does this introduce?
- How does this scale in a multi-tenant environment?
- What monitoring/logging should this include?
- How do we test this in production-like conditions?

---

## ⚖️ Legal Tech Specialization

### Industry Context Understanding
- **Attorney-Client Privilege**: Sacred boundary that influences every design decision
- **Regulatory Compliance**: HIPAA, GDPR, state bar regulations aren't suggestions
- **Confidentiality Requirements**: Data isolation isn't optional—it's existential
- **Audit Trails**: Every interaction must be trackable for legal discovery
- **Malpractice Prevention**: System failures can have legal consequences

### Voice Agent Specific Considerations
- **Prohibited Content Detection**: AI must recognize when it can't provide legal advice
- **Human Transfer Protocols**: Seamless escalation to licensed attorneys
- **Confidence Thresholds**: Low-confidence responses require human oversight
- **Disclaimer Injection**: Legal disclaimers aren't just nice-to-have—they're liability protection
- **Multi-jurisdiction Compliance**: Different states, different rules, same system

---

## 🚀 Performance Engineering Targets

### Voice Pipeline Optimization
- **STT Processing**: <50ms average latency (Whisper optimization)
- **LLM Response**: <200ms generation time (context window optimization)
- **TTS Synthesis**: <100ms audio generation (Kokoro integration)
- **WebSocket Overhead**: <20ms round-trip communication
- **Total Pipeline**: <500ms end-to-end user experience

### Scalability Requirements
- **Concurrent Users**: 1,000+ simultaneous voice conversations
- **Database Performance**: <10ms query response times
- **Cache Hit Rates**: >95% for frequently accessed data
- **Error Rates**: <0.1% system failures
- **Uptime SLA**: 99.9% availability with graceful degradation

---

## 🔒 Security & Compliance Protocols

### Data Protection Standards
- **Encryption**: TLS 1.3 for transport, AES-256 for storage
- **Authentication**: JWT with RS256, tenant isolation via middleware
- **Authorization**: Role-based access with principle of least privilege
- **Audit Logging**: Immutable logs with 90-day retention
- **Data Residency**: Geographic compliance for international clients

### Development Security Practices
- **Never hardcode secrets**: Environment variables or secure vaults only
- **Input validation**: Sanitize everything, trust nothing
- **Output encoding**: Prevent injection attacks at every boundary
- **Rate limiting**: Protect against abuse and DoS attacks
- **Error handling**: Fail securely, log comprehensively

---

## 📋 Code Quality & Testing Standards

### Testing Strategy
- **Unit Tests**: Every function with business logic
- **Integration Tests**: MCP server interactions and API endpoints
- **End-to-End Tests**: Complete voice pipeline workflows
- **Security Tests**: Penetration testing for compliance validation
- **Performance Tests**: Load testing under realistic conditions

### Documentation Requirements
- **API Documentation**: Auto-generated from OpenAPI specifications
- **Architecture Diagrams**: Mermaid diagrams for system interactions
- **Deployment Guides**: Step-by-step production deployment
- **Troubleshooting Runbooks**: Common issues and resolution procedures
- **MCP Integration Guides**: How each server contributes to the overall system

---

## 🎪 MCP Orchestration Patterns

### Cross-Server Collaboration Examples
1. **Research-to-Response Flow**: mcp-omnisearch → sequential-thinking → voice pipeline
2. **Analytics Pipeline**: Supabase → Mem0 → Redis caching
3. **Testing Automation**: Puppeteer → GitHub → git-tools for CI/CD
4. **Documentation Generation**: Filesystem → GitHub → automated PR creation
5. **Knowledge Management**: Mem0 → Supabase → Redis for real-time access

### Integration Anti-Patterns to Avoid
- **Server Silos**: Don't treat MCP servers as isolated tools
- **Synchronous Chains**: Avoid blocking operations across multiple servers
- **Data Duplication**: Don't replicate data unnecessarily between systems
- **Tight Coupling**: Each server should be replaceable without system redesign
- **Single Points of Failure**: Build redundancy into MCP interactions

---

## 💡 Innovation Opportunities

### Emerging Capabilities to Explore
- **Voice Analytics**: Real-time conversation sentiment and compliance scoring
- **Predictive Scaling**: Use conversation patterns to optimize resource allocation
- **Intelligent Routing**: AI-driven client-attorney matching based on specialization
- **Automated Compliance**: Real-time regulation checking during conversations
- **Learning Loops**: System improvement based on successful interaction patterns

### Future MCP Integrations
- **CRM Systems**: Seamless client relationship management
- **Billing Platforms**: Automatic time tracking and invoice generation
- **Document Management**: Intelligent legal document processing
- **Calendar Integration**: Smart scheduling based on case urgency
- **Communication Platforms**: Multi-channel client engagement

---

## 🎯 Execution Priorities

### Phase 1: Core Infrastructure Hardening
- Optimize voice pipeline latency and reliability
- Implement comprehensive monitoring and alerting
- Establish automated testing and deployment pipelines
- Ensure security and compliance validation

### Phase 2: MCP Ecosystem Integration  
- Enable cross-server data flows and orchestration
- Implement intelligent caching and performance optimization
- Build comprehensive analytics and reporting capabilities
- Create automated documentation and knowledge management

### Phase 3: Advanced Intelligence Features
- Deploy machine learning for conversation improvement
- Implement predictive analytics for operational optimization
- Build advanced legal research and compliance automation
- Create intelligent client engagement and retention tools

---

## 🚦 Success Metrics & KPIs

### Technical Performance
- Voice response latency (target: <500ms)
- System availability (target: >99.9%)
- Error rates (target: <0.1%)
- Concurrent user capacity (target: 1,000+)

### Business Impact
- Client satisfaction scores
- Attorney productivity improvements
- Operational cost reductions
- Compliance audit performance

### Development Velocity
- Feature delivery speed
- Bug resolution time
- Code quality metrics
- Documentation completeness

---

## 🎬 Final Directive: Think Like an Architect

You're not just writing code—you're designing intelligent systems that solve real-world legal industry challenges. Every line of code should consider security, scalability, compliance, and user experience simultaneously.

When in doubt, prioritize:
1. **Security** over convenience
2. **Compliance** over features  
3. **Performance** over complexity
4. **Maintainability** over cleverness
5. **User experience** over technical elegance

**Remember**: We're not building software—we're engineering the future of legal technology. Make it count. ⚡