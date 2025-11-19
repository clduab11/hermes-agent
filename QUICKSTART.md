# HERMES Quick Start Guide

This guide will help you set up HERMES for local development in under 15 minutes.

---

## Prerequisites

Before starting, ensure you have:

### Required Tools
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **pip** (comes with Python)

### Required Accounts
- **Supabase** account ([Sign up](https://supabase.com/))
- **OpenAI** account with API access ([Sign up](https://platform.openai.com/))
- **Stripe** account (optional, for billing features) ([Sign up](https://stripe.com/))

### Recommended Tools
- **Python virtual environment** (venv or conda)
- **VS Code** or PyCharm for development
- **Postman** or similar for API testing

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/clduab11/hermes-agent.git
cd hermes-agent
```

---

## Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Optional: Install development tools
pip install -r requirements-dev.txt
```

**Note**: Installation may take 5-10 minutes due to large dependencies like `torch` and `openai-whisper`.

### Troubleshooting Installation

If you encounter issues:

```bash
# Upgrade pip first
pip install --upgrade pip

# Install torch separately if it fails
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install remaining dependencies
pip install -r requirements.txt
```

---

## Step 4: Configure Environment Variables

### Create Environment File

```bash
# Copy the template
cp .env.template .env
```

### Edit Required Variables

Open `.env` in your text editor and set these **required** variables:

```bash
# === REQUIRED FOR LOCAL DEVELOPMENT ===

# Database (Supabase)
DATABASE_URL="postgresql://user:password@host:port/database"
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# AI Services (OpenAI)
OPENAI_API_KEY="sk-your-openai-api-key"

# Security (generate these)
JWT_PRIVATE_KEY="your-rsa-private-key-base64"
JWT_PUBLIC_KEY="your-rsa-public-key-base64"
API_KEY_ENCRYPTION_SECRET="your-fernet-key"

# App Configuration
DEBUG="true"
DEMO_MODE="true"
API_HOST="0.0.0.0"
API_PORT="8000"
```

### Generate Security Keys

Use the provided script to generate JWT and encryption keys:

```bash
# Generate keys automatically
./scripts/generate-secrets.sh

# Or manually generate them:

# JWT Keys (RSA 2048)
openssl genpkey -algorithm RSA -out private_key.pem -pkcs8 -pass pass: 2048
openssl rsa -pubout -in private_key.pem -out public_key.pem

# Convert to base64 and add to .env
cat private_key.pem | base64 -w 0 > jwt_private.txt
cat public_key.pem | base64 -w 0 > jwt_public.txt

# Encryption Key (Fernet)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database**
3. Copy the **Connection String** (set as `DATABASE_URL`)
4. Navigate to **Settings** → **API**
5. Copy **URL** (set as `SUPABASE_URL`)
6. Copy **service_role key** (set as `SUPABASE_SERVICE_ROLE_KEY`)

### Get OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Copy and set as `OPENAI_API_KEY`

---

## Step 5: Setup Database

### Run Migrations

```bash
# Apply all database migrations
alembic upgrade head
```

If migrations fail, check:
- `DATABASE_URL` is correct in `.env`
- Database is accessible (not firewalled)
- Supabase project is active

### Verify Database Tables

Connect to your Supabase database and verify these tables exist:
- `users`
- `api_keys`
- `usage_logs`
- `conversations`
- `matters`

---

## Step 6: Start the Development Server

```bash
# Start with auto-reload
uvicorn hermes.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Step 7: Test the Application

### Health Check

Open your browser or use curl:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-XX-XXTXX:XX:XX.XXXXXXZ"
}
```

### Interactive API Docs

Visit http://localhost:8000/docs to see the Swagger UI with all API endpoints.

### Test Voice Endpoint (Optional)

If you have a test audio file:

```bash
# Test speech-to-text
curl -X POST http://localhost:8000/api/voice/stt \
  -H "Content-Type: audio/wav" \
  --data-binary @test_audio.wav
```

---

## Step 8: Development Workflow

### Code Changes

With `--reload` flag, Uvicorn automatically restarts when you modify Python files.

### View Logs

Watch the terminal where uvicorn is running for real-time logs.

### Test Your Changes

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_voice_pipeline.py

# With coverage
pytest --cov=hermes tests/
```

---

## Common Issues & Solutions

### Issue: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'hermes'`

**Solution**: Make sure you're in the project root and `PYTHONPATH` includes current directory:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Database Connection Failed

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**: 
- Verify `DATABASE_URL` is correct
- Check Supabase project is not paused
- Ensure firewall allows your IP
- Try direct connection using `psql` to verify credentials

### Issue: OpenAI API Rate Limits

**Problem**: `openai.error.RateLimitError: Rate limit exceeded`

**Solution**:
- Check your OpenAI account has credits
- Reduce concurrent requests
- Add delays between API calls

### Issue: Port Already in Use

**Problem**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000
# Or on Windows:
netstat -ano | findstr :8000

# Kill the process
kill <PID>
```

### Issue: Torch Installation Fails

**Problem**: `torch` or `torchaudio` fails to install

**Solution**:
```bash
# Install CPU-only version
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or use pre-built wheels
pip install torch==2.2.0 torchaudio==2.2.0 --find-links https://download.pytorch.org/whl/torch_stable.html
```

---

## Next Steps

Now that you have HERMES running locally:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the Code**: Start with `hermes/main.py`
3. **Make Changes**: Modify code and test immediately
4. **Run Tests**: Ensure your changes don't break existing functionality
5. **Deploy**: When ready, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Development Best Practices

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings (Google style)
- Use async/await for I/O operations

### Testing

- Write tests for new features
- Maintain >80% code coverage
- Run tests before committing

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit
git add .
git commit -m "feat: add your feature"

# Push and create PR
git push origin feature/your-feature-name
```

---

## Useful Commands

```bash
# Format code
black hermes/

# Lint code
flake8 hermes/

# Type check
mypy hermes/

# Run tests with coverage
pytest --cov=hermes --cov-report=html tests/

# View coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux

# Start with different port
uvicorn hermes.main:app --reload --port 8001

# Start with debug logging
uvicorn hermes.main:app --reload --log-level debug
```

---

## Getting Help

- **Documentation**: Check [README.md](README.md) and [docs/](docs/)
- **Issues**: Search/create [GitHub issues](https://github.com/clduab11/hermes-agent/issues)
- **Email**: info@parallax-ai.app

---

**Happy coding! 🚀**
