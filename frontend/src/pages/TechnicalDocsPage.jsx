/**
 * Technical Documentation Page
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React, { useState } from 'react';

export default function TechnicalDocsPage() {
  const [activeTab, setActiveTab] = useState('endpoints');

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Technical Documentation</h1>

      <div className="tabs tabs-boxed">
        <a
          className={`tab ${activeTab === 'endpoints' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('endpoints')}
        >
          API Endpoints
        </a>
        <a
          className={`tab ${activeTab === 'webhooks' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('webhooks')}
        >
          Webhooks
        </a>
        <a
          className={`tab ${activeTab === 'integration' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('integration')}
        >
          Integration Guide
        </a>
      </div>

      {activeTab === 'endpoints' && (
        <div className="space-y-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Leads API</h2>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Method</th>
                      <th>Endpoint</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/leads</code></td>
                      <td>List all leads</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/leads/:id</code></td>
                      <td>Get specific lead</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-info">POST</span></td>
                      <td><code>/api/leads</code></td>
                      <td>Create new lead</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-warning">PUT</span></td>
                      <td><code>/api/leads/:id</code></td>
                      <td>Update lead</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-error">DELETE</span></td>
                      <td><code>/api/leads/:id</code></td>
                      <td>Delete lead</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="divider">Example Request</div>
              <div className="mockup-code">
                <pre data-prefix="$"><code>curl -X POST http://localhost:8000/api/leads \</code></pre>
                <pre data-prefix=""><code>  -H "Content-Type: application/json" \</code></pre>
                <pre data-prefix=""><code>  -d '{`{`}</code></pre>
                <pre data-prefix=""><code>    "firm_name": "Smith & Associates",</code></pre>
                <pre data-prefix=""><code>    "contact_email": "john@smithlaw.com",</code></pre>
                <pre data-prefix=""><code>    "status": "new",</code></pre>
                <pre data-prefix=""><code>    "pipeline_value": 2497</code></pre>
                <pre data-prefix=""><code>  {`}`}'</code></pre>
              </div>
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Social Media API</h2>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Method</th>
                      <th>Endpoint</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/social/posts</code></td>
                      <td>List all posts</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-info">POST</span></td>
                      <td><code>/api/social/posts</code></td>
                      <td>Create new post</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-info">POST</span></td>
                      <td><code>/api/social/generate</code></td>
                      <td>Generate AI content</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-info">POST</span></td>
                      <td><code>/api/social/posts/:id/schedule</code></td>
                      <td>Schedule post</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-info">POST</span></td>
                      <td><code>/api/social/posts/:id/publish</code></td>
                      <td>Publish post</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Analytics API</h2>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Method</th>
                      <th>Endpoint</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/marketing/analytics/metrics</code></td>
                      <td>Get all metrics</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/marketing/analytics/funnel</code></td>
                      <td>Get conversion funnel</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/marketing/analytics/pipeline</code></td>
                      <td>Get pipeline value</td>
                    </tr>
                    <tr>
                      <td><span className="badge badge-success">GET</span></td>
                      <td><code>/api/marketing/analytics/roi</code></td>
                      <td>Get ROI metrics</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'webhooks' && (
        <div className="space-y-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Zapier Integration</h2>
              <p>Connect HERMES to 8,000+ apps via Zapier webhooks.</p>

              <div className="divider">Incoming Webhook</div>
              <p className="text-sm">Receive data from external systems:</p>
              <div className="mockup-code">
                <pre data-prefix="$"><code>curl -X POST http://localhost:8000/api/webhooks/incoming \</code></pre>
                <pre data-prefix=""><code>  -H "Content-Type: application/json" \</code></pre>
                <pre data-prefix=""><code>  -d '{`{`}</code></pre>
                <pre data-prefix=""><code>    "event_type": "lead.created",</code></pre>
                <pre data-prefix=""><code>    "source": "zapier",</code></pre>
                <pre data-prefix=""><code>    "data": {`{`} "firm_name": "Test Firm" {`}`}</code></pre>
                <pre data-prefix=""><code>  {`}`}'</code></pre>
              </div>

              <div className="divider">Outgoing Webhook</div>
              <p className="text-sm">Send data to external systems:</p>
              <div className="mockup-code">
                <pre data-prefix="$"><code>curl -X POST http://localhost:8000/api/webhooks/trigger \</code></pre>
                <pre data-prefix=""><code>  -H "Content-Type: application/json" \</code></pre>
                <pre data-prefix=""><code>  -d '{`{`}</code></pre>
                <pre data-prefix=""><code>    "webhook_url": "https://hooks.zapier.com/...",</code></pre>
                <pre data-prefix=""><code>    "payload": {`{`} ... {`}`}</code></pre>
                <pre data-prefix=""><code>  {`}`}'</code></pre>
              </div>
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Available Event Types</h2>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Event Type</th>
                      <th>Description</th>
                      <th>Trigger</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><code>lead.created</code></td>
                      <td>New lead added to pipeline</td>
                      <td>Manual or API</td>
                    </tr>
                    <tr>
                      <td><code>lead.updated</code></td>
                      <td>Lead status changed</td>
                      <td>Manual or API</td>
                    </tr>
                    <tr>
                      <td><code>lead.won</code></td>
                      <td>Deal closed successfully</td>
                      <td>Status change</td>
                    </tr>
                    <tr>
                      <td><code>social.published</code></td>
                      <td>Social post published</td>
                      <td>Scheduled or manual</td>
                    </tr>
                    <tr>
                      <td><code>social.scheduled</code></td>
                      <td>Post scheduled for future</td>
                      <td>Manual or API</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'integration' && (
        <div className="space-y-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Quick Start Guide</h2>
              
              <div className="steps steps-vertical lg:steps-horizontal">
                <div className="step step-primary">
                  <div className="text-left">
                    <h3 className="font-bold">1. Get API Access</h3>
                    <p className="text-sm">Contact us for API credentials</p>
                  </div>
                </div>
                <div className="step step-primary">
                  <div className="text-left">
                    <h3 className="font-bold">2. Test Endpoints</h3>
                    <p className="text-sm">Use Postman or curl to test</p>
                  </div>
                </div>
                <div className="step">
                  <div className="text-left">
                    <h3 className="font-bold">3. Integrate</h3>
                    <p className="text-sm">Connect to your systems</p>
                  </div>
                </div>
                <div className="step">
                  <div className="text-left">
                    <h3 className="font-bold">4. Go Live</h3>
                    <p className="text-sm">Deploy to production</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Common Integration Scenarios</h2>
              
              <div className="collapse collapse-arrow bg-base-200">
                <input type="radio" name="integration-accordion" defaultChecked />
                <div className="collapse-title text-xl font-medium">
                  CRM Integration (Clio, HubSpot, Salesforce)
                </div>
                <div className="collapse-content">
                  <p>Sync leads and contacts bidirectionally with your CRM system.</p>
                  <ul className="list-disc list-inside mt-2">
                    <li>Automatic lead creation from web forms</li>
                    <li>Status updates sync back to CRM</li>
                    <li>Contact enrichment with social data</li>
                  </ul>
                </div>
              </div>

              <div className="collapse collapse-arrow bg-base-200">
                <input type="radio" name="integration-accordion" />
                <div className="collapse-title text-xl font-medium">
                  Social Media Automation
                </div>
                <div className="collapse-content">
                  <p>Schedule and publish content across multiple platforms.</p>
                  <ul className="list-disc list-inside mt-2">
                    <li>AI-generated content for each platform</li>
                    <li>Bulk scheduling with calendar view</li>
                    <li>Performance tracking and analytics</li>
                  </ul>
                </div>
              </div>

              <div className="collapse collapse-arrow bg-base-200">
                <input type="radio" name="integration-accordion" />
                <div className="collapse-title text-xl font-medium">
                  Email Marketing (Mailchimp, SendGrid)
                </div>
                <div className="collapse-content">
                  <p>Trigger email campaigns based on lead behavior.</p>
                  <ul className="list-disc list-inside mt-2">
                    <li>Automated follow-up sequences</li>
                    <li>Personalized content based on practice area</li>
                    <li>A/B testing integration</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
