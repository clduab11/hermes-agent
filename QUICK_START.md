# ⚡ 5-Minute Quick Start

Get judicAIta running in 5 minutes or less!

---

## Prerequisites (30 seconds)

```bash
# Check Python version (requires 3.11+)
python --version

# If you need to install Python 3.11+:
# Ubuntu/Debian: sudo apt install python3.11
# macOS: brew install python@3.11
# Windows: Download from python.org
```

---

## Step 1: Installation (2 minutes)

```bash
# Clone repository
git clone https://github.com/clduab11/hermes-agent.git
cd hermes-agent

# Install dependencies
pip install -r requirements-legal-ai.txt

# This installs:
# - transformers (for LEGAL-BERT)
# - torch (for deep learning)
# - networkx (for graph analysis)
# - cryptography (for security)
# - pydantic (for data validation)
# - pytest (for testing)
```

---

## Step 2: Run Quick Demo (2 minutes)

```bash
# Run the 5-minute demonstration
python examples/quick_start.py
```

**What you'll see:**
1. ✅ Legal reasoning analysis (negligence case)
2. ✅ Citation graph with PageRank
3. ✅ Attorney-client privilege protection
4. ✅ Encryption demonstration
5. ✅ Audit logging

---

## Step 3: Explore More (1 minute)

### Option A: Interactive Jupyter Notebook
```bash
jupyter notebook kaggle/LEGAL_AI_DEMO.ipynb
```

### Option B: Run Tests
```bash
pytest tests/test_legal_reasoning.py -v -s
```

### Option C: Read Full Documentation
```bash
# Open in your browser:
# docs/LEGAL_AI_USER_GUIDE.md
```

---

## 💻 Code Example (Copy & Paste)

```python
import asyncio
from hermes.reasoning.legal_reasoning_engine import LegalReasoningEngine, LegalDomain

async def analyze_case():
    # Initialize engine
    engine = LegalReasoningEngine()

    # Analyze a legal query
    result = await engine.analyze_legal_query(
        query="""
        A grocery store customer slipped on a wet floor with no warning sign.
        The customer broke their wrist. Does the customer have a negligence claim?
        """,
        domain=LegalDomain.TORT_LAW,
        jurisdiction="California"
    )

    # Review results
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Conclusion: {result.conclusion}")
    print(f"Cases Cited: {len(result.cited_cases)}")

    # See reasoning steps
    for i, step in enumerate(result.reasoning_steps, 1):
        print(f"{i}. {step.description}")

# Run
asyncio.run(analyze_case())
```

**Expected Output:**
```
Confidence: 87.3%
Conclusion: Based on analysis of 6 reasoning steps and 2 legal syllogisms...
Cases Cited: 5

1. Identified 2 legal issues: Negligence, Duty Of Care
2. Apply legal rule: To establish negligence, plaintiff must prove...
3. Analyze Palsgraf v. Long Island Railroad Co.: Duty of care is owed...
4. Analyze 3 relevant facts against legal framework
5. Legal syllogism 1: Based on common_law, the elements of tort_negligence_001...
6. Synthesize conclusion with confidence: 87.3%
```

---

## 🎯 What's Next?

### Learn More
- **Full User Guide**: `docs/LEGAL_AI_USER_GUIDE.md` (60+ pages)
- **Architecture**: `docs/ARCHITECTURE.md` (system design)
- **API Reference**: Inline docstrings in all modules

### Try Advanced Features
1. **Citation Graph Analysis**: See `tests/test_legal_reasoning.py::TestCitationGraphAnalysis`
2. **Security Features**: See `tests/test_legal_reasoning.py::TestLegalSecurity`
3. **Multi-Database Search**: See `hermes/integrations/legal_databases.py`

### Customize
- **Add Legal Domains**: Extend `LegalDomain` enum
- **Custom Rules**: Add to legal rules database
- **New Databases**: Implement `LegalDatabaseClient` interface

---

## ⚠️ Troubleshooting

### Issue: "No module named 'transformers'"
**Solution**:
```bash
pip install transformers torch
```

### Issue: "LEGAL-BERT download slow"
**Solution**: First download takes ~2-3 minutes for 400MB model. Subsequent runs are instant (cached).

### Issue: "Tests failing"
**Solution**: Some tests require optional dependencies:
```bash
pip install pytest pytest-asyncio openai cryptography
```

### Issue: "Python version error"
**Solution**: judicAIta requires Python 3.11+
```bash
python --version  # Should show 3.11 or higher
```

---

## 🏆 Key Features Demonstrated

| Feature | Description | Demo Location |
|---------|-------------|---------------|
| **Legal Reasoning** | LEGAL-BERT + LSP | `examples/quick_start.py` |
| **Citation Graph** | PageRank + HITS | `examples/quick_start.py` |
| **Security** | Privilege + Encryption | `examples/quick_start.py` |
| **Explainability** | Step-by-step traces | All analysis outputs |
| **Multi-Database** | 4 integrated sources | `hermes/integrations/` |

---

## 📊 Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| **Analysis Time** | <2 seconds |
| **Confidence Score** | 80-95% |
| **Cases Cited** | 5-10 relevant |
| **Reasoning Steps** | 6-12 steps |
| **Explainability** | 100% traceable |

---

## 🚀 Production Deployment

Ready for production? See:
- **Deployment Guide**: `docs/ARCHITECTURE.md` (deployment section)
- **Security Checklist**: `docs/LEGAL_AI_USER_GUIDE.md` (security section)
- **API Documentation**: Source code docstrings

---

## 📞 Need Help?

- **Email**: info@parallax-ai.app
- **GitHub Issues**: https://github.com/clduab11/hermes-agent/issues
- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Tests**: `tests/` directory

---

## ⚖️ Legal Disclaimer

**IMPORTANT**: This software provides research assistance only and does NOT constitute legal advice. Always consult with a qualified, licensed attorney for legal matters.

---

**judicAIta - Production-Ready Legal AI in 5 Minutes**

**© 2025 Parallax Analytics LLC**
