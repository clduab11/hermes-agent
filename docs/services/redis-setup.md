# Redis Cache Setup Guide

This guide walks you through setting up Redis for caching and performance optimization in HERMES.

---

## Overview

Redis is **optional** but highly recommended for HERMES performance:
- Session storage and management
- API rate limiting counters
- Response caching (reduce OpenAI API calls)
- Temporary data storage
- Real-time metrics

**Without Redis**: HERMES falls back to in-memory storage (works, but no persistence across restarts)

**Reference**: `requirements.txt` line 18 (`redis[hiredis]==5.1.1`)

---

## Benefits of Redis

| Feature | With Redis | Without Redis |
|---------|------------|---------------|
| **Response Time** | 10-50ms | 50-200ms |
| **Rate Limiting** | Distributed | In-memory only |
| **Session Persistence** | Yes | Lost on restart |
| **Caching** | Persistent | In-memory only |
| **Multi-instance** | Shared cache | Isolated |

**Recommendation**: Use Redis for production, optional for development

---

## Option 1: GCP Memorystore (Recommended for GCP)

Best for production deployments on Google Cloud Platform.

### Create Redis Instance

```bash
# Set variables
export PROJECT_ID=your-project-id
export REGION=us-central1
export REDIS_INSTANCE=hermes-redis

# Create Redis instance
gcloud redis instances create $REDIS_INSTANCE \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_6_x \
    --tier=basic \
    --project=$PROJECT_ID

# Wait for creation (2-5 minutes)
gcloud redis instances describe $REDIS_INSTANCE --region=$REGION
```

### Get Connection Info

```bash
# Get host and port
export REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE \
    --region=$REGION --format='value(host)')
export REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE \
    --region=$REGION --format='value(port)')

echo "Redis URL: redis://$REDIS_HOST:$REDIS_PORT"
```

### Configure HERMES

Add to `.env`:
```bash
REDIS_URL=redis://10.x.x.x:6379  # Use actual IP from above
```

### Cost

- **Basic Tier (1GB)**: ~$50/month
- **Standard Tier (1GB)**: ~$150/month (HA, automatic failover)
- **Scaling**: ~$50/GB/month

---

## Option 2: Redis Cloud (Multi-cloud)

Good for development or if using multiple cloud providers.

### Create Account

1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Sign up with email or Google
3. Verify email

### Create Database

1. Click "New database"
2. Configure:
   - **Cloud**: GCP (or AWS, Azure)
   - **Region**: Same as your deployment
   - **Name**: `hermes-cache`
   - **Type**: Redis Stack (includes modules)
3. Choose plan:
   - **Free**: 30MB (dev only)
   - **Pay As You Go**: Starting at $0.014/hr (~$10/month)
4. Click "Create database"
5. Wait for provisioning (1-2 minutes)

### Get Connection Info

1. Click on database name
2. Copy **Public endpoint**
3. Format: `redis-12345.c123.us-central1-gcp.cloud.redislabs.com:12345`
4. Get password from "Security" tab

### Configure HERMES

Add to `.env`:
```bash
REDIS_URL=redis://default:your-password@redis-12345.c123.us-central1-gcp.cloud.redislabs.com:12345
```

### Cost

- **Free**: $0/month (30MB, dev only)
- **Pay As You Go**: $10-100/month (1-10GB)
- **Pro**: $100-200/month (50GB+, HA)

---

## Option 3: Upstash (Serverless Redis)

Best for low-traffic or cost-sensitive deployments.

### Create Account

1. Go to [upstash.com](https://upstash.com/)
2. Sign up with GitHub, Google, or email
3. Verify email

### Create Database

1. Click "Create Database"
2. Configure:
   - **Name**: `hermes-cache`
   - **Type**: Regional
   - **Region**: Same as your deployment
   - **TLS**: Enabled
3. Click "Create"

### Get Connection Info

1. Copy **REST URL** and **REST Token** (for serverless)
   - Or copy **Redis URL** (for traditional connection)
2. Format: `rediss://user:password@host:port`

### Configure HERMES

Add to `.env`:
```bash
REDIS_URL=rediss://default:your-password@host:6379
```

### Cost

- **Free**: $0/month (10,000 commands/day)
- **Pay As You Go**: $0.20 per 100k commands
- **Pro**: $120/month (unlimited commands)

**Best for**: Development, demos, low-traffic sites

---

## Option 4: Self-Hosted (Not Recommended)

For development only. Not recommended for production.

### Install Redis (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
# Expected: PONG
```

### Configure HERMES

Add to `.env`:
```bash
REDIS_URL=redis://localhost:6379
```

### Limitations

- No automatic backups
- No high availability
- Manual scaling
- Security configuration required
- Maintenance overhead

---

## Configuration Options

### Basic Configuration

```bash
# Required
REDIS_URL=redis://host:port

# Optional settings
REDIS_MAX_CONNECTIONS=10  # Max connections in pool
REDIS_TIMEOUT=5  # Connection timeout (seconds)
```

### Connection Pooling

HERMES automatically uses connection pooling:

```python
# In hermes/cache/redis_client.py
from redis import Redis, ConnectionPool

pool = ConnectionPool.from_url(
    os.getenv("REDIS_URL"),
    max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 10)),
    socket_timeout=int(os.getenv("REDIS_TIMEOUT", 5))
)

redis_client = Redis(connection_pool=pool)
```

### Key Eviction Policy

Recommended for HERMES:

```bash
# Set via Redis CLI
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Or in redis.conf
maxmemory-policy allkeys-lru
```

**Policy Explanation**:
- `allkeys-lru`: Evict least recently used keys when memory is full
- Good for cache use cases

---

## Test Redis Connection

### Using redis-cli

```bash
# Test connection
redis-cli -u $REDIS_URL ping

# Set a test key
redis-cli -u $REDIS_URL SET test_key "Hello HERMES"

# Get the key
redis-cli -u $REDIS_URL GET test_key

# Delete the key
redis-cli -u $REDIS_URL DEL test_key
```

### Using Python

```python
import redis
import os

# Connect to Redis
client = redis.from_url(os.getenv("REDIS_URL"))

# Test connection
print("Ping:", client.ping())  # Should print: True

# Set and get test data
client.set("test_key", "Hello HERMES", ex=60)  # Expires in 60s
print("Value:", client.get("test_key").decode())

# Delete test key
client.delete("test_key")
```

---

## Monitoring & Performance

### Monitor Memory Usage

```bash
# Get info
redis-cli INFO memory

# Key metrics:
# - used_memory_human: Current memory usage
# - maxmemory_human: Maximum memory limit
# - mem_fragmentation_ratio: Memory efficiency
```

### Monitor Hit Rate

```bash
redis-cli INFO stats | grep keyspace

# Key metrics:
# - keyspace_hits: Cache hits
# - keyspace_misses: Cache misses
# - Hit rate = hits / (hits + misses)
```

### Slow Log

```bash
# View slow queries (> 10ms)
redis-cli SLOWLOG GET 10
```

---

## Security Best Practices

### Enable Authentication

```bash
# Set password
redis-cli CONFIG SET requirepass your-strong-password

# Update connection URL
REDIS_URL=redis://:your-strong-password@host:port
```

### Use TLS/SSL

```bash
# Use rediss:// (note the extra 's')
REDIS_URL=rediss://:password@host:port
```

### Network Security

- ✅ Use VPC/private network when possible
- ✅ Restrict IP access (firewall rules)
- ✅ Use TLS in production
- ❌ Don't expose Redis publicly without authentication

---

## Performance Impact Analysis

### With Redis

**Benefits**:
- 80% reduction in duplicate OpenAI API calls
- 70% faster response times for repeated queries
- Distributed rate limiting across instances
- Persistent sessions (no loss on restart)

**Costs**:
- $50-200/month (depending on tier)
- ~5ms overhead per Redis operation (negligible)

### Without Redis

**Fallback Behavior**:
- In-memory caching (per-instance only)
- Sessions lost on restart
- No shared state across instances
- More OpenAI API calls (higher cost)

**When to Skip Redis**:
- Single-instance development
- Very low traffic (<100 requests/day)
- Cost-sensitive proof-of-concept

---

## Disable Redis (If Needed)

To run HERMES without Redis:

1. **Don't set REDIS_URL** in `.env`
2. HERMES will automatically fall back to in-memory storage
3. No code changes required

**Logs will show**:
```
[INFO] Redis not configured, using in-memory fallback
```

---

## Troubleshooting

### Issue: Connection Refused

**Error**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:
- Verify Redis is running: `redis-cli ping`
- Check firewall allows connection
- Verify host/port are correct
- Check authentication password

### Issue: Authentication Failed

**Error**: `NOAUTH Authentication required`

**Solutions**:
- Add password to URL: `redis://:password@host:port`
- Verify password is correct
- Check Redis `requirepass` setting

### Issue: Timeout

**Error**: `redis.exceptions.TimeoutError: Timeout reading from socket`

**Solutions**:
- Increase timeout: `REDIS_TIMEOUT=10`
- Check network latency
- Verify Redis instance isn't overloaded
- Check connection pool size

### Issue: Out of Memory

**Error**: `OOM command not allowed when used memory > 'maxmemory'`

**Solutions**:
- Increase Redis memory (upgrade plan)
- Set eviction policy: `allkeys-lru`
- Reduce key TTL (expire faster)
- Clear unnecessary keys

---

## Cost Optimization

### Reduce Memory Usage

```python
# Set shorter TTLs
redis_client.setex("cache_key", 300, value)  # 5 minutes instead of 1 hour

# Use efficient data structures
# Bad: Store JSON strings
redis_client.set("user:123", json.dumps(user_dict))  # 500 bytes

# Good: Use Redis Hash
redis_client.hset("user:123", mapping=user_dict)  # 200 bytes
```

### Monitor Unused Keys

```bash
# Find large keys
redis-cli --bigkeys

# Delete unused keys
redis-cli KEYS "temp:*" | xargs redis-cli DEL
```

---

## Next Steps

Once Redis is configured (or skipped):

1. ✅ Choose hosting option (GCP Memorystore, Redis Cloud, Upstash, or skip)
2. ✅ Get connection URL
3. ✅ Configure `.env` with `REDIS_URL`
4. ✅ Test connection
5. ✅ Continue with deployment: [DEPLOYMENT.md](../../DEPLOYMENT.md)

---

## Support

- **Redis Docs**: [redis.io/docs](https://redis.io/docs/)
- **GCP Memorystore**: [cloud.google.com/memorystore/docs/redis](https://cloud.google.com/memorystore/docs/redis)
- **Redis Cloud**: [redis.com/docs](https://redis.com/docs/)
- **Upstash**: [docs.upstash.com](https://docs.upstash.com/)
- **HERMES Support**: info@parallax-ai.app

---

**Last Updated**: 2024-11-19
