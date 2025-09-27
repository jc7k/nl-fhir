# NL-FHIR Scripts

## SpaCy Model Installation

The NL-FHIR application uses MedSpaCy for clinical NLP, which requires spaCy and additional biomedical models.

### Automatic Installation

After installing the main application dependencies:

```bash
# Install NL-FHIR dependencies
uv pip install -e .

# Install spaCy models
python scripts/install_spacy_models.py
```

### Manual Installation (if script fails)

```bash
# Standard spaCy model (required for MedSpaCy)
python -m spacy download en_core_web_sm

# Or via direct URL
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz

# SciSpacy biomedical models (optional - enhanced medical NLP)
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_core_sci_sm-0.2.4.tar.gz
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_ner_bc5cdr_md-0.2.4.tar.gz
```

### Graceful Degradation

The application is designed to work without these models:
- If models are unavailable, it falls back to regex-based extraction
- Core functionality (FHIR conversion) remains operational
- Only advanced NLP features are affected

### CI/CD Integration

The GitHub Actions workflow automatically attempts to install these models but continues even if installation fails, ensuring builds don't break due to model availability issues.