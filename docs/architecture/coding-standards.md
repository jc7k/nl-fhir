# NL-FHIR Coding Standards

## General Principles

- **HIPAA First**: No PHI in logs, use surrogate IDs, encrypt all data
- **Medical Safety**: Validate all clinical data, fail safe on errors
- **Performance**: <2s response time, optimize for medical workflow speed
- **Reliability**: ≥99.9% uptime, comprehensive error handling

## Python Standards

### Code Style
- **Formatter**: `black` with 88-character line length
- **Linter**: `ruff` for fast, comprehensive linting
- **Type Checking**: `mypy` with strict mode enabled
- **Import Sorting**: `isort` compatible with black

### Structure
```python
# File header example
"""
NL-FHIR Component: Brief description
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from typing import Optional, List, Dict, Any
import logging

# Configure logger with no PHI
logger = logging.getLogger(__name__)
```

### Error Handling
```python
# Medical-safe error handling
try:
    result = process_clinical_data(input_data)
except ValidationError as e:
    logger.error(f"Validation failed for request {request_id}: {e}")
    raise HTTPException(status_code=422, detail="Invalid clinical input")
except Exception as e:
    logger.error(f"Processing error for request {request_id}: {type(e).__name__}")
    raise HTTPException(status_code=500, detail="Processing failed")
```

### Medical Data Handling
```python
# HIPAA-compliant data structures
from pydantic import BaseModel, Field, validator
from uuid import uuid4

class ClinicalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    clinical_text: str = Field(..., description="Free-text clinical order")
    
    @validator('clinical_text')
    def validate_clinical_text(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Clinical text too short")
        return v.strip()
```

## FastAPI Standards

### API Structure
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("NL-FHIR service starting")
    yield
    # Shutdown
    logger.info("NL-FHIR service shutting down")

app = FastAPI(
    title="NL-FHIR Converter",
    description="Natural Language to FHIR R4 Bundle Converter",
    version="1.0.0",
    lifespan=lifespan
)
```

### Endpoint Patterns
```python
@app.post("/convert", response_model=FHIRBundleResponse)
async def convert_to_fhir(
    request: ClinicalRequest,
    request_id: str = Depends(generate_request_id)
) -> FHIRBundleResponse:
    """Convert natural language to FHIR bundle."""
    logger.info(f"Processing conversion request {request_id}")
    
    try:
        # Process through pipeline
        nlp_result = await nlp_service.extract_entities(request.clinical_text)
        fhir_bundle = await fhir_service.create_bundle(nlp_result)
        validation_result = await fhir_service.validate_bundle(fhir_bundle)
        
        return FHIRBundleResponse(
            bundle=fhir_bundle,
            validation=validation_result,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Conversion failed for {request_id}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Conversion failed")
```

## Testing Standards

### Test Structure
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestConvertEndpoint:
    """Test clinical text conversion endpoint."""
    
    def test_valid_medication_order(self):
        """Test valid medication order conversion."""
        request_data = {
            "clinical_text": "Start patient on lisinopril 10mg daily"
        }
        
        response = client.post("/convert", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "bundle" in data
        assert data["validation"]["is_valid"] is True
        
    def test_invalid_input_handling(self):
        """Test handling of invalid clinical input."""
        request_data = {"clinical_text": ""}
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
```

### Golden Dataset Testing
```python
@pytest.fixture
def golden_dataset():
    """Load golden dataset for regression testing."""
    return load_golden_dataset("tests/data/clinical_orders.json")

def test_regression_medication_orders(golden_dataset):
    """Test against known-good medication orders."""
    for test_case in golden_dataset["medication_orders"]:
        response = client.post("/convert", json={"clinical_text": test_case["input"]})
        
        assert response.status_code == 200
        # Validate against expected FHIR structure
        assert_fhir_bundle_matches(response.json()["bundle"], test_case["expected"])
```

## Security Standards

### Input Validation
```python
from pydantic import validator
import re

class SecureClinicalRequest(BaseModel):
    clinical_text: str
    
    @validator('clinical_text')
    def sanitize_input(cls, v):
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>"\';]', '', v)
        if len(sanitized) != len(v):
            logger.warning("Input sanitization applied")
        return sanitized
```

### Logging Security
```python
import logging
from typing import Dict, Any

def safe_log(level: str, message: str, request_id: str, **kwargs):
    """Log without exposing PHI."""
    safe_kwargs = {
        k: "[REDACTED]" if k in ["patient_name", "ssn", "dob"] else v
        for k, v in kwargs.items()
    }
    
    logger.log(
        getattr(logging, level.upper()),
        f"{message} [request_id={request_id}]",
        extra=safe_kwargs
    )
```

## File Organization

```
src/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── requests.py      # API request models
│   │   ├── responses.py     # API response models
│   │   └── fhir.py         # FHIR resource models
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── nlp.py          # NLP processing
│   │   ├── fhir.py         # FHIR operations
│   │   └── validation.py    # Validation logic
│   ├── utils/               # Utilities
│   │   ├── __init__.py
│   │   ├── logging.py      # HIPAA-compliant logging
│   │   └── security.py     # Security utilities
│   └── api/                 # API routes
│       ├── __init__.py
│       └── endpoints.py     # Route definitions
tests/
├── unit/                    # Unit tests
├── integration/             # Integration tests
├── data/                    # Test data and golden datasets
└── conftest.py             # Pytest configuration
```

## Dependencies Management

### requirements.txt Structure
```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Medical NLP
spacy==3.7.2
medspacy==1.0.2

# FHIR Processing
fhir.resources==7.0.2

# Database & Vector Store
chromadb==0.4.18
psycopg2-binary==2.9.9

# Development
pytest==7.4.3
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

## Performance Standards

- **Response Time**: <2s for all API endpoints
- **Memory Usage**: Monitor and optimize for medical model loading
- **Database**: Connection pooling, query optimization
- **Caching**: Redis for frequent medical terminology lookups

## Medical Safety Requirements

- **Validation**: All clinical data must pass validation before processing
- **Error Handling**: Fail safe - return error rather than incorrect medical data
- **Audit Trail**: Log all processing decisions (without PHI)
- **Terminology**: Use standardized medical codes (RxNorm, LOINC, ICD-10)