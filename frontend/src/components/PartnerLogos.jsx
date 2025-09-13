import React from 'react';

export default function PartnerLogos() {
  const integrations = [
    { name: 'Clio', description: 'Native CRM Integration', icon: '⚖️' },
    { name: 'Zapier', description: '5,000+ App Connections', icon: '🔗' },
    { name: 'Supabase', description: 'Scalable Database', icon: '🗄️' },
    { name: 'OpenAI', description: 'Advanced AI Processing', icon: '🧠' },
    { name: 'GitHub', description: 'Secure Code Repository', icon: '🐙' },
    { name: 'Playwright', description: 'Automated Testing', icon: '🎭' },
    { name: 'Mem0', description: 'Knowledge Graph', icon: '🧩' },
    { name: 'WebSocket', description: 'Real-time Communication', icon: '⚡' }
  ];

  const styles = {
    section: {
      textAlign: 'center'
    },
    title: {
      fontSize: '2rem',
      marginBottom: '1rem',
      color: '#1f2937'
    },
    subtitle: {
      fontSize: '1.1rem',
      color: '#6b7280',
      marginBottom: '3rem'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1.5rem',
      marginTop: '2rem'
    },
    card: {
      background: 'white',
      padding: '1.5rem',
      borderRadius: '10px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb',
      transition: 'transform 0.3s ease, box-shadow 0.3s ease'
    },
    cardHover: {
      transform: 'translateY(-5px)',
      boxShadow: '0 8px 20px rgba(0,0,0,0.15)'
    },
    icon: {
      fontSize: '2.5rem',
      marginBottom: '1rem'
    },
    name: {
      fontWeight: 'bold',
      marginBottom: '0.5rem',
      color: '#1f2937'
    },
    description: {
      color: '#6b7280',
      fontSize: '0.9rem'
    },
    architectureSection: {
      background: '#f8fafc',
      padding: '3rem 2rem',
      borderRadius: '15px',
      marginTop: '3rem',
      border: '1px solid #e5e7eb'
    },
    architectureDiagram: {
      fontFamily: 'monospace',
      background: '#1f2937',
      color: '#10b981',
      padding: '2rem',
      borderRadius: '10px',
      whiteSpace: 'pre',
      fontSize: '0.8rem',
      overflowX: 'auto',
      textAlign: 'left'
    }
  };

  return (
    <section style={styles.section}>
      <h2 style={styles.title}>🔗 Platform Integrations & MCP Technology Stack</h2>
      <p style={styles.subtitle}>
        Seamlessly connects with your existing legal technology ecosystem
      </p>
      
      <div style={styles.grid}>
        {integrations.map((integration, index) => (
          <div 
            key={index} 
            style={styles.card}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)';
              e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            }}
          >
            <div style={styles.icon}>{integration.icon}</div>
            <div style={styles.name}>{integration.name}</div>
            <div style={styles.description}>{integration.description}</div>
          </div>
        ))}
      </div>

      <div style={styles.architectureSection}>
        <h3 style={{ marginBottom: '2rem', color: '#1f2937' }}>🏗️ Technical Architecture</h3>
        <p style={{ marginBottom: '2rem', color: '#6b7280' }}>
          HERMES is built on a microservices architecture designed for enterprise-scale legal operations
        </p>
        <div style={styles.architectureDiagram}>
{`┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Voice Pipeline │────│   AI Engine    │────│  CRM Adapters   │
│   (Whisper)     │    │  (OpenRouter)   │    │     (Clio)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  TTS Service    │    │ Legal Validators│    │   Monitoring    │
│   (Kokoro)      │    │ & Compliance    │    │ & Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘`}
        </div>
        
        <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>&lt;100ms</div>
            <div style={{ color: '#6b7280' }}>Voice Response Latency</div>
          </div>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>1,000+</div>
            <div style={{ color: '#6b7280' }}>Concurrent Users</div>
          </div>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>99.9%</div>
            <div style={{ color: '#6b7280' }}>Uptime SLA</div>
          </div>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>&lt;500ms</div>
            <div style={{ color: '#6b7280' }}>End-to-End Processing</div>
          </div>
        </div>
      </div>
    </section>
  );
}
