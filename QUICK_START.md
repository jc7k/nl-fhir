# 🚀 Quick Start Guide

Get NL-FHIR running locally in 5 minutes!

## ⚠️ Medical Software Notice

**This software is for research and development purposes only.** Not intended for clinical decision-making or patient care without proper validation and compliance review. See [MEDICAL_SAFETY.md](docs/MEDICAL_SAFETY.md) for healthcare integration guidelines.

## 📋 Prerequisites

- **Python 3.10** (Required - medical NLP models have specific version requirements)
- **uv** package manager (Recommended for fastest setup)
- **Docker** (Optional - for HAPI FHIR validation)
- **OpenAI API Key** (Required for LLM processing)

## ⚡ 5-Minute Setup

### 1. Clone & Install
```bash
git clone https://github.com/your-org/nl-fhir.git
cd nl-fhir

# Install with uv (recommended)
pip install uv
uv sync

# Or install with pip
pip install -e .
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenAI API key
# Get key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-actual-api-key-here
```

### 3. Run Application
```bash
# Start the server
uv run uvicorn src.nl_fhir.main:app --host 0.0.0.0 --port 8001 --reload

# Or with make
make dev
```

### 4. Test It Works
```bash
# Health check
curl http://localhost:8001/health

# Try conversion
curl -X POST http://localhost:8001/convert \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_text": "Prescribe 10mg Lisinopril daily for hypertension",
    "patient_ref": "patient-123"
  }'
```

## 🌐 Access Points

- **Web UI**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Metrics**: http://localhost:8001/metrics

## 🧪 Run Tests (Optional)

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/api/ -v

# Run with coverage
uv run pytest --cov=src/nl_fhir
```

## 🏥 Optional: HAPI FHIR Validation

For full FHIR validation (healthcare standard compliance):

```bash
# Start HAPI FHIR server
docker-compose up hapi-fhir

# Update .env to enable validation
FHIR_VALIDATION_ENABLED=true
HAPI_FHIR_URL=http://localhost:8080/fhir
```

## 🚨 Troubleshooting

### Common Issues

**Import Error with Medical Models:**
```bash
# Download medical NLP models
python -m spacy download en_core_web_sm
python -m spacy download en_core_sci_sm
```

**OpenAI API Errors:**
- Verify API key is correct in `.env`
- Check API usage limits at platform.openai.com
- Ensure account has sufficient credits

**Port Already in Use:**
```bash
# Change port in command
uv run uvicorn src.nl_fhir.main:app --port 8002
```

**Memory Issues with NLP Models:**
- Minimum 4GB RAM recommended
- Models download ~500MB on first run
- Use `LLM_ESCALATION_ENABLED=false` to reduce memory usage

## 📚 Next Steps

1. **Read the Documentation**: [docs/](docs/)
2. **Try Examples**: [docs/examples/](docs/examples/)
3. **Medical Safety Guidelines**: [docs/MEDICAL_SAFETY.md](docs/MEDICAL_SAFETY.md)
4. **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
5. **API Reference**: http://localhost:8001/docs

## 🤝 Community

- **Issues**: [GitHub Issues](https://github.com/your-org/nl-fhir/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/nl-fhir/discussions)
- **Medical AI Community**: Join healthcare informatics forums

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Need help?** Open an issue or check our [FAQ](docs/FAQ.md).