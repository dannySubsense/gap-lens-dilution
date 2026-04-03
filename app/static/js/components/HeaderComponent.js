// Header component for the Gap Lens Dilution Dashboard
class HeaderComponent {
  constructor(headerElement, state) {
    this.headerElement = headerElement;
    this.state = state;
    this.data = null;
  }

  render(data) {
    if (!data) {
      this.renderEmpty();
      return;
    }

    this.data = data;

    const riskClass = this.getRiskClass(data.offeringRisk);
    const riskLabel = data.offeringRisk || 'N/A';

    const float = data.float ? formatNumber(data.float) : 'N/A';
    const outstanding = data.outstanding ? formatNumber(data.outstanding) : 'N/A';
    const marketCap = data.marketCap ? formatCurrency(data.marketCap) : 'N/A';
    const industry = data.industry || 'N/A';
    const country = data.country || 'N/A';

    this.headerElement.innerHTML = `
      <div class="company-header">
        <div class="company-header-top">
          <h1 class="company-ticker">${data.ticker || ''}</h1>
          <div class="risk-badge risk-badge-${riskClass}">RISK: ${riskLabel}</div>
        </div>
        <div class="company-details">
          <span>Float/OS: ${float}/${outstanding}</span>
          <span class="detail-separator">|</span>
          <span>MC: ${marketCap}</span>
          <span class="detail-separator">|</span>
          <span>${industry}</span>
          <span class="detail-separator">|</span>
          <span>${country}</span>
        </div>
      </div>
    `;
  }

  renderEmpty() {
    this.headerElement.innerHTML = `
      <div class="company-header">
        <div class="company-header-top">
          <h1 class="company-ticker">Enter a ticker to begin</h1>
        </div>
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