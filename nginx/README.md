# HERMES Nginx Configuration

Production-grade Nginx reverse proxy configuration for the HERMES AI voice agent system.

## Features

- ✅ **WebSocket Support** - Real-time voice streaming with 24/7 uptime
- ✅ **Rate Limiting** - API (100 r/s), Voice (50 r/s), Auth (10 r/m)
- ✅ **SSL/TLS** - Modern TLS 1.2/1.3 with A+ security rating
- ✅ **Load Balancing** - Least connections with health checks
- ✅ **Security Headers** - HSTS, CSP, X-Frame-Options, etc.
- ✅ **Gzip Compression** - Optimized for JSON/JavaScript/CSS
- ✅ **Access Logging** - JSON format with request timing
- ✅ **Error Handling** - Custom error pages
- ✅ **HTTP/2** - Modern protocol support

## Directory Structure

```
nginx/
├── nginx.conf              # Main Nginx configuration
├── conf.d/
│   └── hermes.conf        # HERMES virtual host configuration
├── ssl/                   # SSL certificates (not in git)
│   ├── cert.pem
│   └── key.pem
└── README.md             # This file
```

## Quick Start

### 1. SSL Certificate Setup

**Option A: Let's Encrypt (Recommended for Production)**

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d hermes.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

**Option B: Self-Signed Certificate (Development Only)**

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### 2. Update Domain Configuration

Edit `nginx/conf.d/hermes.conf` and replace:

```nginx
server_name hermes.yourdomain.com;
```

With your actual domain name.

### 3. Start with Docker Compose

```bash
# Start all services including Nginx
docker-compose up -d

# Check Nginx status
docker-compose exec nginx nginx -t  # Test configuration
docker-compose logs nginx           # View logs
```

### 4. Verify Setup

```bash
# Test HTTP to HTTPS redirect
curl -I http://localhost

# Test API endpoint
curl -k https://localhost/health

# Test WebSocket (requires wscat)
wscat -c wss://localhost/ws/voice
```

## Configuration Details

### Rate Limiting Zones

| Zone | Limit | Burst | Purpose |
|------|-------|-------|---------|
| `api_limit` | 100 r/s | 20 | General API endpoints |
| `voice_limit` | 50 r/s | 10 | WebSocket voice connections |
| `auth_limit` | 10 r/m | 5 | Authentication/login attempts |
| `conn_limit` | 10 conn | - | Max concurrent connections per IP |

### WebSocket Configuration

Critical settings for 24/7 voice agent support:

```nginx
proxy_connect_timeout 7d;
proxy_send_timeout 7d;
proxy_read_timeout 7d;
proxy_buffering off;
```

**Why 7 days?**
- Law firm voice agents may maintain long-duration calls
- Prevent timeout during extended hold periods
- Support 24/7 availability requirements

### SSL/TLS Security

**Protocols:** TLS 1.2, TLS 1.3
**Cipher Suites:** Modern, secure ciphers only
**HSTS:** 2 year max-age with includeSubDomains
**OCSP Stapling:** Enabled for performance

**Test SSL Configuration:**

```bash
# Using SSL Labs
https://www.ssllabs.com/ssltest/analyze.html?d=hermes.yourdomain.com

# Using testssl.sh
docker run --rm -ti drwetter/testssl.sh hermes.yourdomain.com
```

### Load Balancing

Configured for horizontal scaling:

```nginx
upstream hermes_api {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
    # Add more servers for scaling:
    # server api2:8000 max_fails=3 fail_timeout=30s;
    # server api3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

**Scaling Steps:**
1. Update `docker-compose.yml` to add `api2`, `api3` services
2. Uncomment additional server lines in `nginx/conf.d/hermes.conf`
3. Reload Nginx: `docker-compose exec nginx nginx -s reload`

### Security Headers

All responses include:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer-when-downgrade
Content-Security-Policy: default-src 'self' ...
Permissions-Policy: geolocation=(), microphone=(self), camera=()
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

### Logging

**Access Logs:**
- `/var/log/nginx/access.log` - All requests (main format)
- `/var/log/nginx/auth.log` - Authentication attempts
- `/var/log/nginx/websocket.log` - WebSocket connections

**Error Log:**
- `/var/log/nginx/error.log` - Errors and warnings

**Log Format:**

```
main: $remote_addr - $remote_user [$time_local] "$request"
      $status $body_bytes_sent "$http_referer"
      "$http_user_agent" "$http_x_forwarded_for"
      rt=$request_time uct="$upstream_connect_time"
      uht="$upstream_header_time" urt="$upstream_response_time"
```

**View Logs:**

```bash
# Real-time access log
docker-compose logs -f nginx

# Last 100 lines
docker-compose exec nginx tail -n 100 /var/log/nginx/access.log

# WebSocket connections only
docker-compose exec nginx tail -f /var/log/nginx/websocket.log

# Failed authentication attempts
docker-compose exec nginx grep "401" /var/log/nginx/auth.log
```

## Monitoring

### Health Check Endpoint

```bash
# Check API health
curl https://hermes.yourdomain.com/health

# Expected response
{"status": "healthy", "timestamp": "2025-11-17T..."}
```

### Metrics Endpoint (Internal Only)

Restricted to private networks (10.x.x.x, 172.16-31.x.x, 192.168.x.x):

```bash
# From internal network
curl http://internal-ip/metrics

# Prometheus scraping endpoint
```

### Nginx Status (Optional)

Add to `hermes.conf` for Nginx metrics:

```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
}
```

## Troubleshooting

### Common Issues

**1. WebSocket Connection Fails**

```bash
# Check Nginx logs
docker-compose logs nginx | grep "ws/"

# Verify WebSocket upgrade headers
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  https://hermes.yourdomain.com/ws/voice
```

**2. 502 Bad Gateway**

- Check if API service is running: `docker-compose ps api`
- Verify upstream configuration: `docker-compose exec nginx nginx -t`
- Check API logs: `docker-compose logs api`

**3. SSL Certificate Error**

```bash
# Verify certificate validity
docker-compose exec nginx openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Check certificate expiration
docker-compose exec nginx openssl x509 -in /etc/nginx/ssl/cert.pem -noout -dates
```

**4. Rate Limit Exceeded (429)**

- Adjust rate limits in `nginx.conf`
- Increase burst value in `hermes.conf`
- Consider IP whitelisting for trusted clients

**5. High Response Time**

```bash
# Check upstream timing in access logs
docker-compose exec nginx grep "urt=" /var/log/nginx/access.log | tail -20

# Analyze slow requests
docker-compose exec nginx awk '{print $NF}' /var/log/nginx/access.log | sort -n | tail -20
```

### Testing Configuration

```bash
# Test configuration syntax
docker-compose exec nginx nginx -t

# Reload configuration (no downtime)
docker-compose exec nginx nginx -s reload

# View configuration
docker-compose exec nginx cat /etc/nginx/nginx.conf
```

## Performance Tuning

### For High Traffic (1000+ req/s)

```nginx
# In nginx.conf
worker_processes auto;  # Use all CPU cores
worker_connections 4096;  # Increase from 2048

# Connection pooling
keepalive 64;  # Increase from 32

# Rate limits
limit_req_zone $binary_remote_addr zone=api_limit:20m rate=1000r/s;
```

### For Large Audio Files

```nginx
# In hermes.conf
client_max_body_size 500M;  # Increase from 100M
client_body_buffer_size 256k;  # Increase from 128k
```

### Enable HTTP/3 (QUIC)

Requires Nginx compiled with HTTP/3 support:

```nginx
listen 443 quic reuseport;
listen 443 ssl http2;
add_header Alt-Svc 'h3=":443"; ma=86400';
```

## Security Best Practices

1. **Always Use HTTPS** - Enforce with HTTP to HTTPS redirect
2. **Keep Nginx Updated** - `docker pull nginx:latest`
3. **Monitor Logs** - Set up alerts for 4xx/5xx errors
4. **Implement WAF** - Consider ModSecurity or Cloudflare
5. **Regular Security Audits** - Use `testssl.sh` monthly
6. **Backup Certificates** - Store securely, test restoration
7. **IP Whitelisting** - For admin/metrics endpoints
8. **DDoS Protection** - Use Cloudflare or AWS Shield

## Production Checklist

Before going live:

- [ ] Replace self-signed certificates with valid SSL
- [ ] Update `server_name` to actual domain
- [ ] Configure DNS A/AAAA records
- [ ] Set up Let's Encrypt auto-renewal
- [ ] Enable access log rotation (logrotate)
- [ ] Configure monitoring/alerting
- [ ] Test failover and load balancing
- [ ] Review and adjust rate limits
- [ ] Enable HTTP/2 push for static assets
- [ ] Set up backup Nginx instance
- [ ] Document runbook for common issues
- [ ] Test disaster recovery procedures

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

---

**Last Updated:** 2025-11-17
**Maintainer:** HERMES Development Team
**Status:** Production Ready
