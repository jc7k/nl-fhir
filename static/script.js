/**
 * NL-FHIR Clinical Form JavaScript
 * HIPAA Compliant: No PHI in console logs
 * Medical Safety: Client-side validation and error handling
 */

class ClinicalForm {
    constructor() {
        this.form = document.getElementById('clinicalForm');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.buttonText = this.submitButton.querySelector('.btn-text');
        this.loadingSpinner = this.submitButton.querySelector('.loading-spinner');
        this.resultContainer = document.getElementById('result');
        this.errorContainer = document.getElementById('error');
        this.resultContent = document.getElementById('result-content');
        this.errorContent = document.getElementById('error-content');
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.form.addEventListener('reset', () => this.handleReset());
        
        // Real-time validation
        const textArea = document.getElementById('clinical_text');
        textArea.addEventListener('input', () => this.validateInput());
    }

    validateInput() {
        const clinicalText = document.getElementById('clinical_text').value.trim();
        const isValid = clinicalText.length >= 5;
        
        // Enable/disable submit button
        this.submitButton.disabled = !isValid;
        
        return isValid;
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        // Validate form before submission
        if (!this.validateInput()) {
            this.showError('Clinical text must be at least 5 characters long.');
            return;
        }

        // Show loading state
        this.setLoadingState(true);
        this.hideMessages();

        try {
            // Collect form data
            const formData = {
                clinical_text: document.getElementById('clinical_text').value.trim(),
                patient_ref: document.getElementById('patient_ref').value.trim() || null
            };

            // Submit to API
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess(result);
            } else {
                this.showError(result.detail || 'An error occurred while processing your request.');
            }

        } catch (error) {
            console.error('Form submission error:', error.message);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.setLoadingState(false);
        }
    }

    handleReset() {
        this.hideMessages();
        this.submitButton.disabled = true;
        setTimeout(() => this.validateInput(), 100);
    }

    setLoadingState(loading) {
        if (loading) {
            this.submitButton.disabled = true;
            this.buttonText.style.display = 'none';
            this.loadingSpinner.style.display = 'inline-block';
        } else {
            this.buttonText.style.display = 'inline';
            this.loadingSpinner.style.display = 'none';
            this.validateInput(); // Re-enable button if valid
        }
    }

    showSuccess(data) {
        this.hideMessages();
        
        // Build FHIR bundle display if available
        let fhirBundleHtml = '';
        if (data.fhir_bundle) {
            fhirBundleHtml = `
                <div class="fhir-bundle-section">
                    <h4>Generated FHIR Bundle (Visual Validation)</h4>
                    <div class="fhir-bundle-summary">
                        <p><strong>Bundle Type:</strong> ${data.fhir_bundle.type || 'transaction'}</p>
                        <p><strong>Resources:</strong> ${data.fhir_bundle.entry ? data.fhir_bundle.entry.length : 0}</p>
                        <p><strong>Bundle ID:</strong> ${data.fhir_bundle.id || 'N/A'}</p>
                    </div>
                    <details class="fhir-bundle-details">
                        <summary>View Full FHIR Bundle JSON</summary>
                        <pre class="fhir-json"><code>${this.escapeHtml(JSON.stringify(data.fhir_bundle, null, 2))}</code></pre>
                    </details>
                </div>
            `;
        }
        
        this.resultContent.innerHTML = `
            <div class="result-details">
                <p><strong>Request ID:</strong> ${this.escapeHtml(data.request_id)}</p>
                <p><strong>Status:</strong> ${this.escapeHtml(data.status)}</p>
                <p><strong>Message:</strong> ${this.escapeHtml(data.message)}</p>
                <p><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
            </div>
            ${fhirBundleHtml}
        `;
        
        this.resultContainer.style.display = 'block';
        this.resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    showError(message) {
        this.hideMessages();
        
        this.errorContent.innerHTML = `
            <div class="error-details">
                <p>${this.escapeHtml(message)}</p>
                <p class="error-help">Please check your input and try again. If the problem persists, contact support.</p>
            </div>
        `;
        
        this.errorContainer.style.display = 'block';
        this.errorContainer.scrollIntoView({ behavior: 'smooth' });
    }

    hideMessages() {
        this.resultContainer.style.display = 'none';
        this.errorContainer.style.display = 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize form when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ClinicalForm();
});