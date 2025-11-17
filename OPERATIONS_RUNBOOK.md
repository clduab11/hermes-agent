# HERMES Operations Runbook

**For:** Production operations team
**Purpose:** Incident response and troubleshooting for HERMES voice agent system
**Audience:** On-call engineers, DevOps, SRE teams
**Last Updated:** November 17, 2025

---

## 📞 Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| **Technical Lead** | Chris (clduab11) | 24/7 for P0 incidents |
| **Database (Supabase)** | support@supabase.com | 24/7 |
| **OpenAI API** | https://status.openai.com | Status page |
| **Clio API** | https://status.clio.com | Status page |
| **Infrastructure** | Cloud provider support | 24/7 |

---

## 🚨 Incident Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| **P0 - Critical** | Complete outage, data loss risk | 15 minutes | API down, database unreachable |
| **P1 - High** | Major degradation, customer impact | 1 hour | Voice pipeline slow (>2s latency) |
| **P2 - Medium** | Partial degradation, limited impact | 4 hours | Clio integration failing |
| **P3 - Low** | Minor issue, no customer impact | 24 hours | Dashboard slow, logs filling up |

---

## 📋 Common Incident Scenarios

### 1. Voice Pipeline High Latency (P1)

**Symptoms:**
- Voice responses taking >1 second
- Customer complaints about slow agent
- `voice_pipeline_latency` metric spiking

**Diagnosis Steps:**

```bash
# 1. Check performance metrics
curl https://hermes.yourdomain.com/api/v1/monitoring/performance

# 2. Check health endpoints
curl https://hermes.yourdomain.com/health/detailed

# 3. Check Docker container status
docker-compose ps

# 4. Check container logs for errors
docker-compose logs api --tail=100

# 5. Check specific pipeline stage latencies
curl https://hermes.yourdomain.com/api/v1/monitoring/performance | jq '.stage_breakdown'
```

**Common Causes & Fixes:**

| Cause | Solution | Time to Fix |
|-------|----------|-------------|
| OpenAI API slow | Check https://status.openai.com, consider fallback | 5 min |
| Database connection pool exhausted | Restart API service: `docker-compose restart api` | 2 min |
| High CPU usage | Scale horizontally (add API instances) | 15 min |
| Memory leak | Restart API service, investigate logs | 5 min |
| Network latency to STT/TTS | Check network, consider regional failover | 30 min |

**Resolution:**

```bash
# Quick fix: Restart API service
docker-compose restart api

# Monitor for 5 minutes
watch -n 5 'curl -s https://hermes.yourdomain.com/health/detailed | jq .'

# If still slow, check OpenAI API
curl -w "@curl-format.txt" https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Scale horizontally if needed (edit docker-compose.yml)
docker-compose up -d --scale api=3
```

**Post-Incident:**
- Review performance metrics in `/api/v1/monitoring/performance`
- Check for patterns (time of day, specific tenants)
- Update capacity planning if scaling was needed

---

### 2. Complete API Outage (P0)

**Symptoms:**
- Health check returning 503/504
- All voice calls failing
- No response from API endpoints

**Diagnosis Steps:**

```bash
# 1. Check if API container is running
docker-compose ps api

# 2. Check API logs
docker-compose logs api --tail=200

# 3. Check database connectivity
docker-compose exec api python -c "from hermes.database import db_manager; import asyncio; asyncio.run(db_manager.health_check())"

# 4. Check Redis connectivity
docker-compose exec redis redis-cli ping

# 5. Check Nginx status
docker-compose ps nginx
docker-compose logs nginx --tail=50
```

**Common Causes & Fixes:**

| Cause | Solution | Time to Fix |
|-------|----------|-------------|
| API container crashed | `docker-compose up -d api` | 1 min |
| Database connection lost | Check Supabase status, restart API | 5 min |
| Redis out of memory | `docker-compose restart redis` | 2 min |
| Nginx misconfiguration | Revert to last known good config | 5 min |
| Out of disk space | Clear logs, scale storage | 10 min |
| SSL certificate expired | Renew certificate (see SSL section) | 15 min |

**Resolution:**

```bash
# Step 1: Quick restart (fixes 80% of issues)
docker-compose restart api redis nginx

# Step 2: Check logs for root cause
docker-compose logs api --tail=500 | grep -i error

# Step 3: Verify health
curl https://hermes.yourdomain.com/health/detailed

# Step 4: If database issue, check Supabase dashboard
# If Redis issue, check memory: docker-compose exec redis redis-cli info memory

# Step 5: Smoke test critical path
curl -X POST https://hermes.yourdomain.com/api/v1/voice/session \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"session_id": "test"}'
```

**Escalation:**
- If restart doesn't work within 5 minutes → P0 escalation to Technical Lead
- If database unreachable → Contact Supabase support
- If suspected DDoS → Enable additional rate limiting, contact hosting provider

---

### 3. Clio Integration Failing (P2)

**Symptoms:**
- Matters not creating in Clio
- OAuth authentication errors
- `clio_api_errors` metric increasing

**Diagnosis Steps:**

```bash
# 1. Check Clio API status
curl https://status.clio.com

# 2. Check Clio integration health
curl https://hermes.yourdomain.com/api/v1/health/integrations

# 3. Check Dead Letter Queue for failed Clio operations
curl https://hermes.yourdomain.com/api/v1/dlq/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 4. Check integration logs
docker-compose logs api | grep -i "clio"

# 5. Test Clio API manually
curl https://app.clio.com/api/v4/matters \
  -H "Authorization: Bearer $CLIO_ACCESS_TOKEN"
```

**Common Causes & Fixes:**

| Cause | Solution | Time to Fix |
|-------|----------|-------------|
| OAuth token expired | Refresh token (automatic with retry) | 5 min |
| Clio API down | Wait for recovery, check status page | Variable |
| Rate limiting | Implement exponential backoff (already done) | 0 min |
| Invalid payload | Check DLQ for failed requests, fix schema | 30 min |
| Network timeout | Increase timeout setting, check network | 10 min |

**Resolution:**

```bash
# Check DLQ for failed Clio operations
curl -X GET https://hermes.yourdomain.com/api/v1/dlq/list?message_type=clio_matter \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Retry failed operations from DLQ
curl -X POST https://hermes.yourdomain.com/api/v1/dlq/retry \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"message_ids": ["dlq_123", "dlq_456"]}'

# If token issue, trigger manual refresh
curl -X POST https://hermes.yourdomain.com/api/v1/integrations/clio/refresh-token \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Graceful Degradation:**
- Operations automatically queue in DLQ when Clio is down
- Process DLQ when Clio recovers
- No data loss, just delayed sync

---

### 4. Database Connection Pool Exhausted (P1)

**Symptoms:**
- "Too many connections" errors in logs
- API timeouts
- Health check showing database degraded

**Diagnosis Steps:**

```bash
# 1. Check active connections
curl https://hermes.yourdomain.com/api/v1/monitoring/database-stats

# 2. Check logs for connection errors
docker-compose logs api | grep -i "connection pool"

# 3. Check database metrics
curl https://hermes.yourdomain.com/health/detailed | jq '.components[] | select(.component=="database")'
```

**Common Causes & Fixes:**

| Cause | Solution | Time to Fix |
|-------|----------|-------------|
| Connection leak | Restart API service | 2 min |
| High traffic spike | Scale API instances | 10 min |
| Slow queries | Optimize queries, add indexes | 1 hour |
| Pool size too small | Increase pool size in config | 5 min |

**Resolution:**

```bash
# Quick fix: Restart API to reset connections
docker-compose restart api

# If persistent, increase pool size
# Edit hermes/database/optimized_connection.py
# Change: pool_size = 20 -> pool_size = 40
# Then rebuild: docker-compose up -d --build api

# Monitor connections
watch -n 2 'curl -s https://hermes.yourdomain.com/api/v1/monitoring/database-stats'
```

---

### 5. High Error Rate (P1)

**Symptoms:**
- Error rate >1% in SLA compliance report
- Customer complaints
- Errors in application logs

**Diagnosis Steps:**

```bash
# 1. Check SLA compliance report
curl https://hermes.yourdomain.com/api/v1/monitoring/sla-compliance

# 2. Check error breakdown by stage
curl https://hermes.yourdomain.com/api/v1/monitoring/performance | jq '.sla_compliance.error_breakdown'

# 3. Check recent errors
docker-compose logs api --tail=500 | grep -i "error"

# 4. Check external API status
curl https://status.openai.com
curl https://status.clio.com
```

**Common Causes & Fixes:**

| Cause | Solution | Time to Fix |
|-------|----------|-------------|
| External API down | Wait for recovery or implement fallback | Variable |
| Invalid input data | Add validation, reject bad requests | 30 min |
| Timeout issues | Increase timeouts, optimize code | 1 hour |
| Memory issues | Restart service, investigate leak | 10 min |
| Rate limiting | Implement backoff (already done) | 0 min |

**Resolution:**

```bash
# Identify error patterns
docker-compose logs api --tail=1000 | grep "ERROR" | sort | uniq -c | sort -rn

# Check if specific tenant causing issues
curl https://hermes.yourdomain.com/api/v1/monitoring/performance-by-tenant

# Temporary mitigation: Rate limit problematic tenant
# (Requires admin API access)
```

---

### 6. Disk Space Full (P1)

**Symptoms:**
- Health check showing disk space degraded
- Logs indicating "No space left on device"
- Container failures

**Diagnosis Steps:**

```bash
# 1. Check disk usage
df -h

# 2. Find largest directories
du -h --max-depth=1 / | sort -rh | head -10

# 3. Check Docker disk usage
docker system df

# 4. Check log sizes
du -h /var/log/ | sort -rh | head -10
```

**Resolution:**

```bash
# Quick fix: Clean Docker resources
docker system prune -a -f

# Clean old logs
find /var/log/nginx -name "*.log" -mtime +7 -delete
find /var/log -name "*.log" -mtime +30 -delete

# Rotate logs manually
logrotate -f /etc/logrotate.conf

# Check disk space after cleanup
df -h

# Long-term: Set up log rotation
# Create /etc/logrotate.d/hermes:
cat > /etc/logrotate.d/hermes <<EOF
/var/log/nginx/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 nginx nginx
    sharedscripts
    postrotate
        docker-compose exec nginx nginx -s reload
    endscript
}
EOF
```

---

### 7. Memory Leak (P2)

**Symptoms:**
- API container memory usage constantly increasing
- Container OOM kills
- Slow performance over time

**Diagnosis Steps:**

```bash
# 1. Check container memory usage
docker stats

# 2. Check application memory metrics
curl https://hermes.yourdomain.com/health/detailed | jq '.components[] | select(.component=="memory")'

# 3. Check for memory warnings in logs
docker-compose logs api | grep -i "memory"
```

**Resolution:**

```bash
# Short-term fix: Restart API service
docker-compose restart api

# Monitor memory over time
watch -n 5 'docker stats --no-stream api'

# If leak persists:
# 1. Capture memory profile (requires profiling tools in container)
# 2. Contact Technical Lead with profile data
# 3. Schedule maintenance window for fix deployment
```

---

## 🔧 Maintenance Procedures

### Database Backup & Restore

**Backup:**

```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres hermes_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

**Restore:**

```bash
# CAUTION: This will overwrite production data!

# 1. Stop API to prevent writes
docker-compose stop api

# 2. Restore database
cat backup_20251117_100000.sql | docker-compose exec -T postgres psql -U postgres hermes_production

# 3. Verify restore
docker-compose exec postgres psql -U postgres hermes_production -c "SELECT COUNT(*) FROM matters;"

# 4. Restart API
docker-compose start api

# 5. Smoke test
curl https://hermes.yourdomain.com/health/detailed
```

---

### SSL Certificate Renewal

**Check Expiry:**

```bash
# Check current certificate expiry
echo | openssl s_client -connect hermes.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**Renew (Let's Encrypt):**

```bash
# 1. Stop Nginx to free port 80
docker-compose stop nginx

# 2. Renew certificate
certbot renew

# 3. Copy new certificates to Docker volume
cp /etc/letsencrypt/live/hermes.yourdomain.com/fullchain.pem /path/to/nginx/ssl/
cp /etc/letsencrypt/live/hermes.yourdomain.com/privkey.pem /path/to/nginx/ssl/

# 4. Start Nginx
docker-compose start nginx

# 5. Verify SSL
curl -vI https://hermes.yourdomain.com 2>&1 | grep "subject\|issuer\|expire"
```

---

### Scaling Operations

**Horizontal Scaling (Add API Instances):**

```bash
# 1. Update docker-compose.yml to scale API
docker-compose up -d --scale api=3

# 2. Verify all instances running
docker-compose ps api

# 3. Check Nginx load balancing
docker-compose logs nginx | grep "upstream"

# 4. Monitor performance
curl https://hermes.yourdomain.com/api/v1/monitoring/performance
```

**Vertical Scaling (Increase Resources):**

```bash
# 1. Edit docker-compose.yml resource limits
# Under api service:
#   deploy:
#     resources:
#       limits:
#         cpus: '2.0'
#         memory: 4G

# 2. Restart with new limits
docker-compose up -d api

# 3. Verify new limits
docker inspect api | jq '.[0].HostConfig.Memory'
```

---

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Target | Alert Threshold | Priority |
|--------|--------|-----------------|----------|
| Voice pipeline p95 latency | <500ms | >1000ms | P1 |
| Error rate | <0.1% | >1% | P1 |
| API uptime | >99.9% | <99.5% | P0 |
| Database connections | <80% pool | >90% pool | P1 |
| Disk space free | >30% | <10% | P1 |
| Memory usage | <80% | >90% | P2 |
| DLQ critical messages | 0 | >10 | P2 |

### Monitoring Dashboards

```bash
# SLA Compliance Report
curl https://hermes.yourdomain.com/api/v1/monitoring/sla-compliance | jq .

# Performance Dashboard
curl https://hermes.yourdomain.com/api/v1/monitoring/performance | jq .

# Health Check
curl https://hermes.yourdomain.com/health/detailed | jq .

# DLQ Status
curl https://hermes.yourdomain.com/api/v1/dlq/stats -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```

---

## 🔍 Debugging Tools

### Log Analysis

```bash
# Tail live logs
docker-compose logs -f api

# Search for errors in last hour
docker-compose logs --since 1h api | grep -i error

# Count error types
docker-compose logs api | grep "ERROR" | awk '{print $NF}' | sort | uniq -c | sort -rn

# Extract stack traces
docker-compose logs api | grep -A 10 "Traceback"

# Check specific session
docker-compose logs api | grep "session_id:abc123"
```

### Performance Profiling

```bash
# Check container resource usage
docker stats --no-stream

# Check API response time
curl -w "@curl-format.txt" -o /dev/null -s https://hermes.yourdomain.com/api/v1/health

# Create curl-format.txt:
cat > curl-format.txt <<EOF
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
EOF
```

---

## 📚 Reference Commands

### Docker Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs [service]

# Restart service
docker-compose restart [service]

# Enter container shell
docker-compose exec [service] /bin/bash

# View resource usage
docker stats

# Clean up resources
docker system prune -a
```

### Database Commands

```bash
# Connect to database
docker-compose exec postgres psql -U postgres hermes_production

# Run query
docker-compose exec postgres psql -U postgres hermes_production -c "SELECT COUNT(*) FROM users;"

# Check active connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis Commands

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Get Redis info
docker-compose exec redis redis-cli info

# Check memory
docker-compose exec redis redis-cli info memory

# Flush cache (DANGEROUS - only if necessary)
docker-compose exec redis redis-cli FLUSHALL
```

---

## 📝 Post-Incident Template

After resolving any P0 or P1 incident, create a post-mortem:

```markdown
# Incident Post-Mortem: [Title]

**Date:** YYYY-MM-DD
**Duration:** [Start time] - [End time] ([Total duration])
**Severity:** P0/P1/P2
**Impact:** [Customer impact description]

## Timeline

- HH:MM - Incident detected
- HH:MM - Initial response started
- HH:MM - Root cause identified
- HH:MM - Resolution implemented
- HH:MM - Incident resolved

## Root Cause

[Detailed technical explanation]

## Resolution

[Steps taken to resolve]

## Prevention

[Action items to prevent recurrence]

## Lessons Learned

[What we learned from this incident]
```

---

**Document Version:** 1.0.0
**Last Updated:** November 17, 2025
**Maintained By:** DevOps Team
