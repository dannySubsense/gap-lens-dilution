/**
 * Risk Assessment Section Component
 * Displays horizontal risk summary bar with multiple risk categories
 */

class RiskAssessmentSection {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.riskData = null;
    }

    render(data) {
        if (!this.container || !data) return;

        this.riskData = data;

        const riskItems = [
            { label: 'Overall Risk', value: data.offeringRisk },
            { label: 'Offering', value: data.offeringAbility },
            { label: 'Dilution', value: data.dilutionRisk },
            { label: 'Frequency', value: data.offeringFrequency },
            { label: 'Cash Need', value: data.cashNeed },
            { label: 'Warrants', value: data.warrantExercise }
        ];

        this.container.innerHTML = `
            <div class="risk-summary-bar">
                ${riskItems.map(item => this.renderRiskItem(item)).join('')}
            </div>
        `;
    }

    renderRiskItem(item) {
        const riskClass = this.getRiskClass(item.value);
        const displayValue = item.value || 'N/A';

        return `
            <div class="risk-item">
                <div class="risk-label">${item.label}</div>
                <div class="risk-value risk-${riskClass}">${displayValue}</div>
            </div>
        `;
    }

    getRiskClass(risk) {
        if (!risk) return 'unknown';
        const riskLower = risk.toLowerCase();
        if (riskLower === 'low') return 'low';
        if (riskLower === 'medium') return 'medium';
        if (riskLower === 'high') return 'high';
        return 'unknown';
    }

    update(data) {
        this.render(data);
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RiskAssessmentSection;
}
