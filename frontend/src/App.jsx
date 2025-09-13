import React, { useState } from 'react';
import DemoContainer from './components/DemoContainer.jsx';
import RoiCalculator from './components/RoiCalculator.jsx';
import Testimonials from './components/Testimonials.jsx';
import PartnerLogos from './components/PartnerLogos.jsx';

export default function App() {
  const [scenario, setScenario] = useState(null);
  const [activeSection, setActiveSection] = useState('home');
  
  const SCENARIOS = {
    INTAKE: 'intake',
    EMERGENCY: 'emergency',
    BILLING: 'billing',
    COURT: 'court'
  };

  const styles = {
    app: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      lineHeight: '1.6',
      color: '#333',
      margin: 0
    },
    header: {
      background: 'linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%)',
      color: 'white',
      padding: '4rem 2rem',
      textAlign: 'center',
      position: 'relative'
    },
    hero: {
      maxWidth: '1200px',
      margin: '0 auto'
    },
    title: {
      fontSize: '3.5rem',
      fontWeight: 'bold',
      marginBottom: '1rem',
      textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
    },
    subtitle: {
      fontSize: '1.5rem',
      marginBottom: '2rem',
      opacity: '0.9'
    },
    ctaButtons: {
      display: 'flex',
      gap: '1rem',
      justifyContent: 'center',
      flexWrap: 'wrap',
      marginTop: '2rem'
    },
    ctaButton: {
      padding: '1rem 2rem',
      fontSize: '1.1rem',
      fontWeight: 'bold',
      border: 'none',
      borderRadius: '50px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      textDecoration: 'none',
      display: 'inline-block'
    },
    ctaPrimary: {
      background: '#10b981',
      color: 'white'
    },
    ctaSecondary: {
      background: 'rgba(255,255,255,0.2)',
      color: 'white',
      backdropFilter: 'blur(10px)'
    },
    section: {
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '4rem 2rem'
    },
    sectionAlt: {
      background: '#f8fafc',
      margin: 0,
      padding: '4rem 0'
    },
    featuresGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: '2rem',
      marginTop: '3rem'
    },
    featureCard: {
      background: 'white',
      padding: '2rem',
      borderRadius: '15px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb'
    },
    featureIcon: {
      fontSize: '2.5rem',
      marginBottom: '1rem'
    },
    pricingGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
      gap: '2rem',
      marginTop: '3rem'
    },
    pricingCard: {
      background: 'white',
      padding: '2.5rem',
      borderRadius: '15px',
      boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
      border: '2px solid #e5e7eb',
      textAlign: 'center'
    },
    pricingCardEnterprise: {
      border: '2px solid #3730a3',
      transform: 'scale(1.05)'
    },
    disclaimer: {
      background: '#fef3c7',
      border: '1px solid #f59e0b',
      borderRadius: '10px',
      padding: '2rem',
      margin: '3rem 0',
      fontSize: '0.95rem'
    },
    footer: {
      background: '#1f2937',
      color: 'white',
      textAlign: 'center',
      padding: '3rem 2rem'
    }
  };

  return (
    <div style={styles.app}>
      {/* Header / Hero Section */}
      <header style={styles.header}>
        <div style={styles.hero}>
          <h1 style={styles.title}>🏛️ HERMES</h1>
          <h2 style={styles.subtitle}>High-performance Enterprise Reception & Matter Engagement System</h2>
          <p style={{ fontSize: '1.2rem', marginBottom: '2rem' }}>
            Revolutionizing Legal Client Communications with AI-Powered Voice Technology
          </p>
          <div style={styles.ctaButtons}>
            <a 
              href="#demo" 
              style={{...styles.ctaButton, ...styles.ctaPrimary}}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              🎙️ Try Voice Demo
            </a>
            <a 
              href="#pricing" 
              style={{...styles.ctaButton, ...styles.ctaSecondary}}
              onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.3)'}
              onMouseOut={(e) => e.target.style.background = 'rgba(255,255,255,0.2)'}
            >
              💰 View Pricing
            </a>
          </div>
        </div>
      </header>

      {/* Core Capabilities Section */}
      <section style={styles.section}>
        <h2 style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: '1rem' }}>
          🎯 Core Capabilities
        </h2>
        <p style={{ textAlign: 'center', fontSize: '1.1rem', marginBottom: '3rem', color: '#6b7280' }}>
          Transforming legal practice operations through cutting-edge AI technology
        </p>
        <div style={styles.featuresGrid}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🎙️</div>
            <h3>Ultra-Low Latency Voice Processing</h3>
            <ul>
              <li>Real-time speech-to-text with OpenAI Whisper</li>
              <li>High-fidelity text-to-speech via Kokoro FastAPI</li>
              <li>WebSocket streaming with &lt;100ms response times</li>
              <li>99.9% uptime SLA with enterprise-grade reliability</li>
            </ul>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🧠</div>
            <h3>Intelligent Response Engine</h3>
            <ul>
              <li>Advanced LLM integration via cloud-based APIs</li>
              <li>Tree of Thought reasoning for complex legal queries</li>
              <li>Legal safety validators with 0.85 confidence thresholds</li>
              <li>Automatic human transfer for complex matters</li>
            </ul>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>⚖️</div>
            <h3>Legal Compliance First</h3>
            <ul>
              <li>Strict safety constraints and prohibited phrase filtering</li>
              <li>Automatic disclaimer injection in all responses</li>
              <li>HIPAA and GDPR compliant data handling</li>
              <li>90-day audit trails with secure transcript retention</li>
            </ul>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔗</div>
            <h3>Seamless CRM Integration</h3>
            <ul>
              <li>Native Clio integration via OAuth 2.0</li>
              <li>Zapier automation support for 5,000+ apps</li>
              <li>Webhook-driven real-time data synchronization</li>
              <li>Multi-tenant architecture with enterprise security</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section id="demo" style={{...styles.sectionAlt}}>
        <div style={styles.section}>
          <h2 style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: '2rem' }}>
            🎬 Interactive Voice Demo
          </h2>
          <p style={{ textAlign: 'center', fontSize: '1.1rem', marginBottom: '2rem', color: '#6b7280' }}>
            Experience HERMES in action with realistic legal scenarios
          </p>
          <div className="scenario-buttons" style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '2rem' }}>
            <button 
              onClick={() => setScenario(SCENARIOS.INTAKE)}
              style={{
                padding: '1rem 1.5rem',
                background: scenario === SCENARIOS.INTAKE ? '#3730a3' : '#e5e7eb',
                color: scenario === SCENARIOS.INTAKE ? 'white' : '#374151',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🚗 Car Accident Intake
            </button>
            <button 
              onClick={() => setScenario(SCENARIOS.EMERGENCY)}
              style={{
                padding: '1rem 1.5rem',
                background: scenario === SCENARIOS.EMERGENCY ? '#3730a3' : '#e5e7eb',
                color: scenario === SCENARIOS.EMERGENCY ? 'white' : '#374151',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🚨 2 AM Arrest Call
            </button>
            <button 
              onClick={() => setScenario(SCENARIOS.BILLING)}
              style={{
                padding: '1rem 1.5rem',
                background: scenario === SCENARIOS.BILLING ? '#3730a3' : '#e5e7eb',
                color: scenario === SCENARIOS.BILLING ? 'white' : '#374151',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              💳 Invoice Question
            </button>
            <button 
              onClick={() => setScenario(SCENARIOS.COURT)}
              style={{
                padding: '1rem 1.5rem',
                background: scenario === SCENARIOS.COURT ? '#3730a3' : '#e5e7eb',
                color: scenario === SCENARIOS.COURT ? 'white' : '#374151',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              ⚖️ Court Reminder
            </button>
          </div>
          {scenario && <DemoContainer scenario={scenario} />}
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" style={styles.section}>
        <h2 style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: '1rem' }}>
          💰 Investment & Pricing
        </h2>
        <p style={{ textAlign: 'center', fontSize: '1.1rem', marginBottom: '3rem', color: '#6b7280' }}>
          Transparent pricing designed for law firms of all sizes
        </p>
        <div style={styles.pricingGrid}>
          <div style={styles.pricingCard}>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#3730a3' }}>Professional Tier</h3>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#10b981', marginBottom: '1rem' }}>
              $2,497<span style={{ fontSize: '1rem', color: '#6b7280' }}>/month</span>
            </div>
            <p style={{ color: '#6b7280', marginBottom: '2rem' }}>Perfect for Small to Medium Practices (1-10 attorneys)</p>
            <ul style={{ textAlign: 'left', marginBottom: '2rem' }}>
              <li>✅ Up to 2,000 client interactions/month</li>
              <li>✅ Clio CRM integration included</li>
              <li>✅ Basic Zapier automation (100 tasks/month)</li>
              <li>✅ Standard legal compliance features</li>
              <li>✅ 8x5 support (business hours)</li>
              <li>✅ 30-day money-back guarantee</li>
            </ul>
          </div>
          <div style={{...styles.pricingCard, ...styles.pricingCardEnterprise}}>
            <div style={{ background: '#3730a3', color: 'white', padding: '0.5rem', borderRadius: '20px', fontSize: '0.9rem', marginBottom: '1rem' }}>
              MOST POPULAR
            </div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#3730a3' }}>Enterprise Tier</h3>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#10b981', marginBottom: '1rem' }}>
              $7,497<span style={{ fontSize: '1rem', color: '#6b7280' }}>/month</span>
            </div>
            <p style={{ color: '#6b7280', marginBottom: '2rem' }}>Designed for Large Practices (11-50 attorneys)</p>
            <ul style={{ textAlign: 'left', marginBottom: '2rem' }}>
              <li>✅ Unlimited client interactions</li>
              <li>✅ Advanced CRM integrations (Clio, LawPay, etc.)</li>
              <li>✅ Premium Zapier automation (unlimited tasks)</li>
              <li>✅ Custom legal compliance configurations</li>
              <li>✅ White-label branding options</li>
              <li>✅ 24/7 priority support</li>
              <li>✅ Dedicated success manager</li>
            </ul>
          </div>
          <div style={styles.pricingCard}>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#3730a3' }}>Custom Enterprise</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#6b7280', marginBottom: '1rem' }}>
              Contact Us
            </div>
            <p style={{ color: '#6b7280', marginBottom: '2rem' }}>For Large Firms (50+ attorneys)</p>
            <ul style={{ textAlign: 'left', marginBottom: '2rem' }}>
              <li>✅ Multi-location deployment</li>
              <li>✅ Custom API development</li>
              <li>✅ Advanced analytics and reporting</li>
              <li>✅ On-premise deployment options</li>
              <li>✅ Custom SLA agreements</li>
              <li>✅ Dedicated technical team</li>
            </ul>
          </div>
        </div>
        
        <div style={{ textAlign: 'center', marginTop: '3rem', padding: '2rem', background: '#f0f9ff', borderRadius: '15px', border: '1px solid #0ea5e9' }}>
          <h4 style={{ color: '#0369a1', marginBottom: '1rem' }}>📊 ROI Calculator</h4>
          <p style={{ marginBottom: '2rem' }}>Average firm saves $15,000-$45,000 annually through:</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', textAlign: 'left' }}>
            <div>• Reduced missed client opportunities (85% improvement)</div>
            <div>• Decreased administrative overhead (40-60% reduction)</div>
            <div>• Improved client retention (25% increase)</div>
            <div>• Enhanced attorney productivity (20-35% more billable hours)</div>
          </div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section style={{...styles.sectionAlt}}>
        <div style={styles.section}>
          <RoiCalculator />
        </div>
      </section>

      {/* Testimonials */}
      <section style={styles.section}>
        <Testimonials />
      </section>

      {/* Legal Disclaimer */}
      <section style={styles.section}>
        <div style={styles.disclaimer}>
          <h3 style={{ color: '#92400e', marginBottom: '1rem' }}>⚖️ LEGAL DISCLAIMER</h3>
          <p style={{ marginBottom: '1rem' }}>
            <strong>IMPORTANT LEGAL NOTICE</strong>: HERMES is a technology demonstration platform and AI voice agent system designed to assist law firms with client communications and administrative tasks.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            <strong>NOT LEGAL ADVICE</strong>: HERMES does not provide legal advice, legal opinions, or attorney services. All interactions with HERMES are for administrative and informational purposes only. Any information provided by HERMES should not be construed as legal advice or create an attorney-client relationship.
          </p>
          <p style={{ marginBottom: '1rem' }}>
            <strong>ATTORNEY-CLIENT PRIVILEGE</strong>: While HERMES is designed with privacy and confidentiality in mind, users should not share privileged or confidential client information through HERMES without appropriate legal safeguards and compliance with applicable professional conduct rules.
          </p>
          <p>
            <strong>PROFESSIONAL RESPONSIBILITY</strong>: Law firms using HERMES remain fully responsible for all legal services provided to their clients. HERMES is a tool to enhance efficiency, not to replace professional legal judgment or attorney oversight.
          </p>
        </div>
      </section>

      {/* Partner Logos */}
      <section style={{...styles.sectionAlt}}>
        <div style={styles.section}>
          <PartnerLogos />
        </div>
      </section>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h3 style={{ marginBottom: '1rem' }}>🤝 Partnership Opportunities</h3>
          <p style={{ marginBottom: '2rem' }}>
            Interested in becoming a certified HERMES implementation partner? We offer technical training, revenue sharing, co-marketing opportunities, and priority support.
          </p>
          <p style={{ marginBottom: '2rem' }}>
            <strong>Parallax Analytics LLC</strong><br />
            📧 <a href="mailto:info@parallax-ai.app" style={{ color: '#60a5fa' }}>info@parallax-ai.app</a><br />
            📞 +1 (662) 848-3547<br />
            🌐 <a href="https://parallax-ai.app/" style={{ color: '#60a5fa' }}>https://parallax-ai.app/</a>
          </p>
          <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid #4b5563' }} />
          <p style={{ fontSize: '0.9rem', opacity: '0.8' }}>
            © 2025 Parallax Analytics LLC. All Rights Reserved. | Built with ❤️ by the Legal Technology Experts at Parallax Analytics
          </p>
          <p style={{ fontSize: '0.85rem', opacity: '0.7', marginTop: '1rem' }}>
            <em>HERMES: Transforming Legal Practice Through Intelligent Voice Technology</em>
          </p>
        </div>
      </footer>
    </div>
  );
}
