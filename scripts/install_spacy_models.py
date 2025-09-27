#!/usr/bin/env python
"""
Install spaCy and scispaCy models for NL-FHIR
This script should be run after installing the main dependencies
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_model(model_name: str, url: str = None):
    """Install a spaCy model either by name or URL"""
    try:
        if url:
            logger.info(f"Installing {model_name} from URL: {url}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", url])
        else:
            logger.info(f"Installing {model_name} via spacy download")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        logger.info(f"✅ Successfully installed {model_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️ Failed to install {model_name}: {e}")
        return False


def main():
    """Install all required spaCy models for NL-FHIR"""
    logger.info("Installing spaCy models for NL-FHIR...")

    models = [
        # Standard spaCy model (for MedSpaCy base)
        {
            "name": "en_core_web_sm",
            "url": "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz"
        },
        # SciSpacy models for biomedical NLP
        {
            "name": "en_core_sci_sm",
            "url": "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_core_sci_sm-0.2.4.tar.gz"
        },
        {
            "name": "en_ner_bc5cdr_md",
            "url": "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_ner_bc5cdr_md-0.2.4.tar.gz"
        }
    ]

    success_count = 0
    failed_models = []

    for model in models:
        if install_model(model["name"], model["url"]):
            success_count += 1
        else:
            failed_models.append(model["name"])

    logger.info(f"\n{'='*50}")
    logger.info(f"Installation complete: {success_count}/{len(models)} models installed")

    if failed_models:
        logger.warning(f"Failed models: {', '.join(failed_models)}")
        logger.warning("The application may work with reduced NLP functionality")
        # Don't exit with error - allow graceful degradation
        return 0
    else:
        logger.info("✅ All models installed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())