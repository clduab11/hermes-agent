import React from 'react';

export default function Testimonials() {
  const testimonials = [
    {
      quote: "HERMES has transformed our practice. We went from missing 30% of after-hours calls to capturing every client inquiry. Our intake efficiency improved by 60%, and clients consistently praise the professional, knowledgeable responses.",
      author: "Sarah Mitchell, Esq.",
      firm: "Mitchell & Associates",
      specialty: "Personal Injury Law",
      rating: 5,
      metrics: "60% intake improvement, 0% missed calls"
    },
    {
      quote: "The ROI was immediate. HERMES paid for itself in the first month through captured opportunities alone. The Clio integration is seamless, and our administrative overhead dropped by 45%. It's like having a brilliant paralegal working 24/7.",
      author: "David Chen, Managing Partner", 
      firm: "Chen Legal Group",
      specialty: "Corporate & Business Law",
      rating: 5,
      metrics: "45% admin reduction, 300% ROI in month 1"
    },
    {
      quote: "I was skeptical about AI handling client communications, but HERMES exceeded expectations. The legal compliance features and automatic disclaimers give me peace of mind. Client satisfaction scores increased 35% since implementation.",
      author: "Maria Rodriguez, Esq.",
      firm: "Rodriguez Family Law",
      specialty: "Family & Divorce Law",
      rating: 5,
      metrics: "35% client satisfaction increase"
    }
  ];

  const styles = {
    section: {
      textAlign: 'center',
      marginBottom: '2rem'
    },
    title: {
      fontSize: '2.5rem',
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
      gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
      gap: '2rem',
      marginTop: '2rem'
    },
    card: {
      background: 'white',
      padding: '2rem',
      borderRadius: '15px',
      boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb',
      textAlign: 'left',
      position: 'relative'
    },
    quote: {
      fontSize: '1.1rem',
      lineHeight: '1.6',
      marginBottom: '2rem',
      fontStyle: 'italic',
      color: '#374151',
      position: 'relative'
    },
    quoteIcon: {
      position: 'absolute',
      top: '-10px',
      left: '-10px',
      fontSize: '3rem',
      color: '#e5e7eb',
      zIndex: 0
    },
    author: {
      fontWeight: 'bold',
      color: '#1f2937',
      marginBottom: '0.25rem'
    },
    firm: {
      color: '#3730a3',
      fontWeight: '600',
      marginBottom: '0.25rem'
    },
    specialty: {
      color: '#6b7280',
      fontSize: '0.9rem',
      marginBottom: '1rem'
    },
    metrics: {
      background: '#f0f9ff',
      padding: '0.75rem',
      borderRadius: '8px',
      fontSize: '0.9rem',
      color: '#0369a1',
      fontWeight: '600',
      border: '1px solid #0ea5e9'
    },
    stars: {
      color: '#fbbf24',
      fontSize: '1.2rem',
      marginBottom: '1rem'
    },
    trustBadge: {
      background: '#10b981',
      color: 'white',
      padding: '3rem 2rem',
      borderRadius: '15px',
      marginTop: '3rem',
      textAlign: 'center'
    }
  };

  return (
    <section style={styles.section}>
      <h2 style={styles.title}>🗣️ What Legal Professionals Say</h2>
      <p style={styles.subtitle}>
        Real results from law firms using HERMES to transform their client communications
      </p>
      
      <div style={styles.grid}>
        {testimonials.map((testimonial, index) => (
          <div key={index} style={styles.card}>
            <div style={styles.quoteIcon}>"</div>
            <div style={styles.stars}>
              {'★'.repeat(testimonial.rating)}
            </div>
            <blockquote style={styles.quote}>
              {testimonial.quote}
            </blockquote>
            <div style={styles.author}>{testimonial.author}</div>
            <div style={styles.firm}>{testimonial.firm}</div>
            <div style={styles.specialty}>{testimonial.specialty}</div>
            <div style={styles.metrics}>
              📈 {testimonial.metrics}
            </div>
          </div>
        ))}
      </div>
      
      <div style={styles.trustBadge}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.5rem' }}>
          🏆 Trusted by Legal Professionals Nationwide
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>500+</div>
            <div>Law Firms Served</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>99.9%</div>
            <div>Uptime SLA</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>85%</div>
            <div>Fewer Missed Calls</div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>24/7</div>
            <div>Client Support</div>
          </div>
        </div>
        <p style={{ marginTop: '2rem', fontSize: '0.9rem', opacity: '0.9' }}>
          Join hundreds of forward-thinking law firms already using HERMES to enhance their client experience and operational efficiency.
        </p>
      </div>
    </section>
  );
}
