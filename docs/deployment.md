# HERMES Platform Integration Guide

This guide explains how to integrate your systems with the HERMES hosted platform. No deployment or infrastructure management required.

## Platform Overview

HERMES is now available exclusively as a fully hosted SaaS platform. All infrastructure, scaling, security, and maintenance is handled by Parallax Analytics.

**Platform URL**: [https://hermes.parallax-ai.app](https://hermes.parallax-ai.app)

## Getting Started

### Step 1: Create Your Account

1. Visit [https://hermes.parallax-ai.app/signup](https://hermes.parallax-ai.app/signup)
2. Choose your firm size and practice areas
3. Complete the 14-day free trial setup (no credit card required)
4. Verify your email and phone number

### Step 2: Configure Your Phone System

HERMES integrates with any SIP-compatible phone system:

**Supported Systems:**
- RingCentral
- 8x8
- Vonage Business
- Microsoft Teams Phone
- Cisco Webex Calling
- Any SIP trunk provider

**Configuration Steps:**
1. Access the Setup Wizard in your HERMES dashboard
2. Enter your SIP trunk details (provided by your phone provider)
3. Configure call forwarding rules for after-hours and overflow
4. Test the integration with a live call

### Step 3: Legal Compliance Setup

1. Select your jurisdiction (all 50 US states supported)
2. Configure legal disclaimers for your practice areas
3. Set up attorney-client privilege protections
4. Enable HIPAA compliance if handling medical cases
5. Configure audit trails for legal discovery

## Integration Options

### CRM Integration

**Supported Platforms:**
- Clio Manage (recommended)
- MyCase
- PracticePanther
- Smokeball
- Filevine
- LawPay
- Custom integrations via API

**Setup Process:**
1. Navigate to Integrations in your HERMES dashboard
2. Click "Connect" next to your CRM platform
3. Authorize HERMES access (read-only permissions recommended)
4. Map client data fields and matter types
5. Test client lookup and data sync

### Business Automation

**Zapier Integration:**
- 3,000+ app integrations
- Automatic matter creation
- Client intake workflows
- Document generation
- Calendar scheduling
- Email notifications

**Microsoft 365 / Google Workspace:**
- Calendar integration for appointment scheduling
- Email sync for client communications
- Document management connections
- Contact directory synchronization

## API Integration

For custom integrations, HERMES provides enterprise APIs:

**Base URL**: `https://api.hermes.parallax-ai.app`

**Authentication**: Bearer token (provided in dashboard)

**Key Endpoints:**
- `/v1/calls` - Call history and recordings
- `/v1/clients` - Client data management
- `/v1/matters` - Matter tracking and updates
- `/v1/webhooks` - Real-time event notifications
- `/v1/settings` - Configuration management

**Documentation**: [https://api.hermes.parallax-ai.app/docs](https://api.hermes.parallax-ai.app/docs)

## Security & Compliance

### SOC 2 Type II Certification
- Annual third-party security audits
- Penetration testing and vulnerability assessments
- 24/7 security monitoring and incident response

### Data Protection
- End-to-end encryption (AES-256)
- Data residency options (US, EU, Canada)
- Automatic backup and disaster recovery
- GDPR compliance for international clients

### Legal Industry Compliance
- Attorney-client privilege protection
- State bar regulation compliance (all 50 states)
- Legal ethics rules integration
- Malpractice insurance compatibility

## Monitoring & Analytics

### Real-time Dashboard
- Live call monitoring
- Response time metrics
- Client satisfaction scores
- Matter conversion tracking
- Revenue attribution

### Reporting
- Monthly performance reports
- Client interaction analytics
- Call volume and patterns
- Integration health monitoring
- Compliance audit trails

## Support & Training

### 24/7 Technical Support
- Phone: +1 (662) 848-3547
- Email: support@parallax-ai.app
- Live chat: Available in dashboard
- Emergency escalation: Available for enterprise clients

### Training Resources
- Video tutorial library
- Best practices documentation
- Weekly office hours with experts
- Custom training sessions for large firms

### Professional Services
- Implementation consulting
- Custom integration development
- Workflow optimization
- Change management support

## Pricing & Plans

### Professional Plan - $99/month per line
- Unlimited calls and messages
- Basic CRM integrations
- Standard support (business hours)
- 99.9% uptime SLA

### Enterprise Plan - Custom pricing
- Volume discounts available
- Advanced integrations and APIs
- 24/7 priority support
- Custom SLA options
- Dedicated customer success manager

### White Label - Contact sales
- Custom branding and domain
- Private deployment options
- Advanced security features
- Regulatory compliance packages

## Migration from Self-Hosted

If you were previously running a self-hosted version of HERMES:

1. **Data Export**: Contact support to export your existing data
2. **Configuration Import**: We'll migrate your settings and integrations
3. **Testing Period**: 30-day parallel running to ensure smooth transition
4. **Go-Live Support**: Dedicated engineer during cutover
5. **Training**: Team training on platform differences

**Migration Timeline**: Typically 1-2 weeks depending on complexity

## Getting Help

- **Platform Status**: [https://status.hermes.parallax-ai.app](https://status.hermes.parallax-ai.app)
- **Documentation**: [https://docs.hermes.parallax-ai.app](https://docs.hermes.parallax-ai.app)
- **Community Forum**: [https://community.hermes.parallax-ai.app](https://community.hermes.parallax-ai.app)
- **Contact Sales**: enterprise@parallax-ai.app

---

**Ready to get started?** [Start your free 14-day trial](https://hermes.parallax-ai.app/signup) or [schedule a personalized demo](https://hermes.parallax-ai.app/demo).