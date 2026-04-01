// Metrics component for displaying dilution metrics
class MetricsComponent {
  constructor(containerElement) {
    this.container = containerElement;
  }

  // Render metrics cards
  render(data) {
    if (!data) return;

    // Clear existing content
    this.container.innerHTML = '';

    // Create metrics grid
    const metricsGrid = document.createElement('div');
    metricsGrid.className = 'metrics-grid';
    
    // Create metric cards
    const metrics = [
      { label: 'Offering Risk', value: data.offeringRisk, risk: this.getRiskLevel(data.offeringRisk) },
      { label: 'Offering Ability', value: data.offeringAbility, risk: 'N/A' },
      { label: 'Dilution Risk', value: data.dilutionRisk, risk: this.getRiskLevel(data.dilutionRisk) },
      { label: 'Cash Need', value: data.cashNeed, risk: 'N/A' },
      { label: 'Cash Runway', value: data.cashRunway, risk: 'N/A' },
      { label: 'Warrant Exercise', value: data.warrantExercise, risk: this.getRiskLevel(data.warrantExercise) }
    ];

    // Add metric cards to the grid
    metrics.forEach(metric => {
      const card = this.createMetricCard(metric.label, metric.value, metric.risk);
      metricsGrid.appendChild(card);
    });

    // Append the metrics grid to the container
    this.container.appendChild(metricsGrid);
  }

  // Create a single metric card
  createMetricCard(label, value, risk) {
    const card = document.createElement('div');
    card.className = 'metric-card';
    
    // Handle null/undefined values
    const displayValue = (value === null || value === undefined) ? 'N/A' : value;
    
    // Add CSS class based on risk level
    const riskLevel = risk.toLowerCase().replace('risk-badge-', '');
    if (riskLevel === 'high' || riskLevel === 'medium' || riskLevel === 'low') {
      card.classList.add('risk-' + riskLevel);
    }
    
    // Set card content
    card.innerHTML = `
      <h3>${label}</h3>
      <div class="metric-value">${displayValue}</div>
      <div class="risk-badge ${risk}">${risk}</div>
    `;
    
    return card;
  }

  // Get risk level based on value (handles string values from API)
  getRiskLevel(value) {
    if (!value) return 'unknown';
    const v = value.toLowerCase();
    if (v === 'high') return 'high';
    if (v === 'medium') return 'medium';
    if (v === 'low') return 'low';
    return 'unknown';
  }
}