Clio Integration Setup Guide
================================

Overview
- Purpose: Connect Hermes to Clio using OAuth 2.0 for contacts, matters, activities, documents, and billing.
- Flow: User initiates OAuth → Clio prompts for consent → Clio redirects back to Hermes callback → Hermes exchanges code for tokens.

Prerequisites
- A Clio Developer account and an application created at https://developers.clio.com/
- A deployed Hermes backend with a stable HTTPS domain (recommended). For local testing, http://localhost:8000 works.

Scopes
- Minimum recommended scopes for full functionality:
  - read, write
  - contacts:read, contacts:write
  - matters:read, matters:write
  - activities:read, activities:write
  - time_entries:read, time_entries:write
  - documents:read, documents:write
  - calendar_entries:read, calendar_entries:write

Hermes Endpoints
- Start authorization: GET /api/clio/oauth/authorize
- OAuth callback (Clio redirects here): GET /api/clio/oauth/callback?code=...&state=...
  - A trailing slash variant /api/clio/oauth/callback/ is also supported for convenience.

Important: The OAuth callback must be configured in your Clio application to exactly match Hermes’ callback URL; otherwise Clio will reject the redirect.

Clio App Configuration
1) Create a Clio app at https://developers.clio.com/
2) Set the following fields:
   - Application (Client) ID: provided by Clio (store as CLIO_CLIENT_ID)
   - Client Secret: provided by Clio (store as CLIO_CLIENT_SECRET)
   - Website URL: informational; does not affect OAuth. Use your project page or product site.
   - Redirect URL: set to the Hermes callback endpoint, e.g.:
     - Production: https://your-hermes-domain.com/api/clio/oauth/callback
     - Local: http://localhost:8000/api/clio/oauth/callback
   - Deauthorization Callback URL: optional. Leave blank if you don't have a deauth endpoint; Hermes does not require it.

Environment Variables
Add these to your runtime environment (do not commit secrets):
- CLIO_CLIENT_ID
- CLIO_CLIENT_SECRET
- CLIO_REDIRECT_URI (must match the Redirect URL above, including scheme and path)

Example (bash):
  export CLIO_CLIENT_ID="<from clio dev app>"
  export CLIO_CLIENT_SECRET="<from clio dev app>"
  export CLIO_REDIRECT_URI="https://your-hermes-domain.com/api/clio/oauth/callback"

How Authorization Works in Hermes
- Authorization URL: Hermes uses a signed state parameter embedding the tenant ID and timestamp. No server-side state storage is required for CSRF validation.
- Callback: Hermes validates the state and exchanges the code for access and refresh tokens.
- Token Storage: The repository currently includes the OAuth flow but not persistent token storage. You must wire storage for tokens (by tenant/user), ideally in your database with encryption at rest and periodic rotation.

Testing the Flow
1) Ensure Hermes is running and reachable at the domain set as CLIO_REDIRECT_URI.
2) Initiate authorization:
   curl -s "https://your-hermes-domain.com/api/clio/oauth/authorize" | jq
   The response contains { "authorization_url": "https://app.clio.com/oauth/authorize?..." }
3) Open the authorization_url in a browser; sign in and authorize the app.
4) Clio redirects to /api/clio/oauth/callback with code/state. Hermes exchanges tokens and returns a success JSON message.

Next Steps: Token Storage
- Create a small repository/service for storing tokens (per tenant and optionally per user):
  - Fields: tenant_id, user_id, access_token, refresh_token, expires_at, token_type
  - Encryption: Use KMS/Secret Manager for the encryption key. Apply envelope encryption.
  - Rotation: Use the refresh token endpoint to rotate access tokens before expiry.
  - Revocation: Expose an admin UI or endpoint to revoke and reauthorize as needed.

Security Checklist
- Never log access or refresh tokens.
- Store only encrypted tokens with least-privileged DB access.
- Validate state and tenant context in the callback.
- Restrict CORS to trusted origins in production (CORS_ALLOW_ORIGINS env var).
- Enforce HTTPS in production and set HSTS headers (enabled by SecurityHeadersMiddleware).

Troubleshooting
- Error: redirect_uri_mismatch
  - Ensure CLIO_REDIRECT_URI matches the Clio app Redirect URL exactly (scheme, host, path).
- Error: invalid_client or unauthorized_client
  - Verify CLIO_CLIENT_ID and CLIO_CLIENT_SECRET are correct and not expired.
- Error: state invalid
  - Do not modify the state parameter. Ensure the tenant context is present when initiating.
- Callback never hits Hermes
  - Verify your Hermes endpoint is publicly reachable and the domain matches the Redirect URL.

References
- Clio Developer Docs: https://docs.developers.clio.com/api-docs/applications/
- OAuth 2.0 spec (Authorization Code flow)
