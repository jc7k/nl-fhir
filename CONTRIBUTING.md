# Contributing to NL-FHIR

Thank you for your interest in contributing to NL-FHIR! We welcome contributions from healthcare professionals, medical AI researchers, software developers, and the broader healthcare technology community.

## ⚠️ Medical Software Development Notice

This is medical AI software for research and development purposes. All contributors should understand:

- **Not for clinical use** without proper validation and regulatory approval
- **Medical accuracy is critical** - errors can impact patient safety
- **HIPAA compliance required** - no real patient data in contributions
- **Clinical validation needed** for all medical logic changes
- **Regulatory considerations** apply to healthcare software

## 🎯 Project Overview

NL-FHIR converts natural language clinical orders into structured FHIR R4 bundles. We welcome contributions that improve:

### 🩺 From Medical Professionals
- **Clinical accuracy** and medical terminology validation
- **Medical specialty patterns** for specific healthcare domains
- **Safety checks** and clinical decision support features
- **Real-world use case** validation and testing

### 🔬 From Researchers
- **NLP model improvements** and medical entity recognition
- **Clinical language processing** algorithms
- **Medical AI evaluation** methods and benchmarks
- **Academic papers** and research collaboration

### 💻 From Developers
- **FHIR compliance** and healthcare interoperability
- **Performance optimization** and scalability improvements
- **Security enhancements** and HIPAA compliance features
- **API design** and integration patterns

### 📚 From Technical Writers
- **Medical documentation** and clinical integration guides
- **Developer tutorials** and API examples
- **Healthcare compliance** documentation
- **Community onboarding** materials

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- uv (Python package manager)
- Git
- Docker (for HAPI FHIR server)

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/nl-fhir.git
   cd nl-fhir
   ```

2. **Set up development environment:**
   ```bash
   # Install dependencies with uv
   uv sync

   # Copy environment template
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start local HAPI FHIR server:**
   ```bash
   docker-compose up hapi-fhir
   ```

4. **Run the application:**
   ```bash
   uv run uvicorn src.nl_fhir.main:app --host 0.0.0.0 --port 8001 --reload
   ```

5. **Run tests (modernized architecture):**
   ```bash
   # Run all tests (456+ modernized test cases)
   uv run pytest

   # Factory architecture tests (208 tests, <2s execution)
   uv run pytest tests/services/fhir/factories/ -v

   # Performance monitoring
   ./scripts/test_performance_monitor.sh
   ```

## 📋 Contribution Workflow

### 1. Before You Start

- Check existing issues and discussions
- For major changes, create an issue to discuss the approach
- Ensure your contribution aligns with project goals

### 2. Development Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure HIPAA compliance considerations

3. **Test your changes:**
   ```bash
   # Run all tests (modernized architecture)
   uv run pytest

   # Run specific test files
   uv run pytest tests/test_your_feature.py -v

   # Factory architecture tests
   uv run pytest tests/services/fhir/factories/ -v

   # Performance validation
   ./scripts/test_performance_monitor.sh

   # Check code quality
   uv run ruff check && uv run ruff format
   uv run mypy src/
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: descriptive commit message following conventional commits"
   ```

### 3. Submitting Changes

1. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request:**
   - Use the provided PR template
   - Include a clear description of changes
   - Reference any related issues
   - Ensure all checks pass

## 🎨 Code Style Guidelines

### Python Code Style

- **Follow PEP 8** with some project-specific conventions
- **Use type hints** for all function signatures
- **Format with Ruff:** `uv run ruff format`
- **Lint with Ruff:** `uv run ruff check`
- **Type check with mypy:** `uv run mypy src/`

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat: add new entity extraction pattern
fix: resolve FHIR validation error
docs: update API documentation
test: add comprehensive bundle validation tests
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation updates
- `test`: Test additions/improvements
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `security`: Security fixes

## 🧪 Testing Guidelines

### Test Categories

1. **Unit Tests** (`tests/unit/`): Test individual components
2. **Integration Tests** (`tests/integration/`): Test component interactions
3. **Epic Tests** (`tests/epic/`): Test complete epic functionality
4. **Validation Tests** (`tests/validation/`): Test FHIR compliance

### Writing Tests

- **Test file naming:** `test_*.py`
- **Test function naming:** `test_descriptive_name`
- **Use fixtures** for common test data
- **Include edge cases** and error conditions
- **Maintain test coverage** above 80%

### Medical Test Data

- **Use synthetic data only** - No real patient information
- **Follow HIPAA guidelines** - No PHI in tests
- **Include diverse medical specialties** when relevant
- **Test various clinical scenarios**

### 🏭 Factory Testing Patterns

The modernized factory architecture requires specific testing patterns:

```python
# Factory Registry Pattern
from src.nl_fhir.services.fhir.factories import get_factory_registry

def test_factory_functionality():
    registry = get_factory_registry()
    factory = registry.get_factory('MedicationRequest')

    result = factory.create('MedicationRequest', test_data)

    # Verify FHIR structure
    assert result['resourceType'] == 'MedicationRequest'
    assert result['status'] == 'active'

# Legacy Compatibility Pattern
from src.nl_fhir.services.fhir.factory_adapter import get_fhir_resource_factory

def test_legacy_compatibility():
    factory = await get_fhir_resource_factory()
    result = factory.create_medication_administration(
        medication_data, patient_ref, request_id
    )

    # Test expectations should be flexible for optional fields
    if "coding" in result and result["coding"]:
        assert result["coding"][0]["code"] == expected_code
```

### Factory Testing Guidelines

- **Use Factory Registry**: Prefer `get_factory_registry()` over direct instantiation
- **Test Legacy Compatibility**: Ensure FactoryAdapter works for backward compatibility
- **Flexible Assertions**: Make coding arrays optional to handle factory differences
- **Performance Testing**: Target <10ms per factory operation
- **Resource Validation**: Verify FHIR structure and required fields

## 🏥 Medical Domain Guidelines

### Clinical Accuracy

- **Validate medical terminology** using standard codes (RxNorm, LOINC, ICD-10)
- **Test with diverse medical specialties** (cardiology, pediatrics, etc.)
- **Include safety validations** for high-risk medications
- **Ensure dosage and frequency accuracy**

### FHIR Compliance

- **Follow FHIR R4 specification** strictly
- **Validate all bundles** against HAPI FHIR server
- **Use proper resource relationships** and references
- **Include required fields** and proper cardinality

### Security and Privacy

- **No PHI in code or tests** - Use synthetic data only
- **Secure API endpoints** with proper authentication
- **Audit trail compliance** for clinical operations
- **Input sanitization** to prevent injection attacks

## 📚 Documentation

### Code Documentation

- **Docstrings** for all public functions and classes
- **Type hints** for all function parameters and returns
- **Inline comments** for complex logic
- **README updates** for new features

### Medical Documentation

- **Clinical context** for medical entity patterns
- **FHIR resource mappings** documentation
- **Medical terminology** explanations
- **Safety consideration** notes

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Sample input data (synthetic only)
- Error messages and stack traces

### Feature Requests

Include:
- Clear description of the proposed feature
- Medical/clinical justification
- FHIR compliance considerations
- Potential implementation approach
- Impact on existing functionality

### Security Vulnerabilities

- **Do not** create public issues for security vulnerabilities
- Follow the `SECURITY.md` guidelines
- Report privately to maintainers
- Include detailed reproduction steps

## 🏗️ Architecture Contributions

### Epic Structure

The project is organized into epics:
- **Epic 1**: Input Layer & Web Interface
- **Epic 2**: NLP Pipeline & Entity Extraction
- **Epic 3**: FHIR Bundle Assembly & Validation
- **Epic 4**: FHIR Bundle Summarization
- **Epic 5**: Infrastructure & Deployment

### Code Organization

- **Service Layer Pattern**: Business logic in `src/nl_fhir/services/`
- **API Endpoints**: REST endpoints in `src/nl_fhir/api/`
- **Models**: Pydantic models in `src/nl_fhir/models/`
- **Configuration**: Environment-based config in `src/nl_fhir/config.py`
- **Factory Architecture**: Modular factories in `src/nl_fhir/services/fhir/factories/`
- **Factory Registry**: Central factory management with shared components
- **Factory Adapter**: Legacy compatibility layer for seamless migration

## 🤝 Community Guidelines

### Communication

- **Be respectful** and inclusive
- **Ask questions** if anything is unclear
- **Share knowledge** and help other contributors
- **Follow medical ethics** in discussions

### Collaboration

- **Review others' PRs** when possible
- **Provide constructive feedback**
- **Be open to feedback** on your contributions
- **Help with documentation** and testing

## 📊 Performance Considerations

### Performance Targets

- **API Response Time**: <2s for natural language to FHIR conversion
- **FHIR Validation**: <100ms per bundle
- **Memory Usage**: Efficient processing for production deployment
- **Concurrent Users**: Support multiple simultaneous requests

### Optimization Guidelines

- **Profile before optimizing** - Use actual performance data
- **Test with realistic data** - Medical complexity varies significantly
- **Consider memory usage** - Large medical vocabularies can impact RAM
- **Cache appropriately** - Medical terminology and FHIR schemas

## 🚀 Release Process

### Version Management

- **Semantic Versioning** (SemVer): MAJOR.MINOR.PATCH
- **CHANGELOG.md** updates for all releases
- **Git tags** for version releases
- **Epic completion** milestone tracking

### Quality Gates

Before release:
- [ ] All tests passing (unit, integration, epic)
- [ ] 100% FHIR validation success
- [ ] Performance benchmarks met
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Medical accuracy validation completed

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and community discussion
- **Documentation**: Check existing docs first
- **Code Examples**: See `tests/` directory for usage patterns

## 🎉 Recognition

Contributors will be recognized in:
- Project README
- Release notes
- GitHub contributors page
- Documentation acknowledgments

Thank you for contributing to NL-FHIR! Your contributions help improve healthcare interoperability and clinical workflow efficiency.