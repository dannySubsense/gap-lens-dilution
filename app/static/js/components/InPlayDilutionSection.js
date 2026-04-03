// InPlayDilutionSection.js
class InPlayDilutionSection {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
  }

  render(data) {
    if (!this.container || !data) return;

    const warrants = data.warrants || [];
    const convertibles = data.convertibles || [];

    this.container.innerHTML = `
      <div class="in-play-dilution">
        <h2 class="inplay-title">In Play Dilution</h2>

        <div class="warrants-section">
          <h3 class="subsection-title">WARRANTS</h3>
          ${this.renderWarrants(warrants)}
        </div>

        ${convertibles.length > 0 ? `
          <div class="convertibles-section">
            <h3 class="subsection-title">CONVERTIBLES</h3>
            ${this.renderConvertibles(convertibles)}
          </div>
        ` : ''}
      </div>
    `;
  }

  renderWarrants(warrants) {
    if (!warrants || warrants.length === 0) {
      return '<p style="color: #666;">No warrant data available</p>';
    }

    return warrants.map(w => {
      const details = w.details || 'Warrants to purchase shares';
      const remaining = w.warrants_remaining ? formatNumber(w.warrants_remaining) : 'N/A';
      const strike = w.warrants_exercise_price ? `$${w.warrants_exercise_price.toFixed(2)}` : 'N/A';
      const filedDate = w.filed_at ? this.formatDate(w.filed_at) : 'N/A';

      return `
        <div class="warrant-item">
          <div class="warrant-details">${details}</div>
          <div class="warrant-data">
            <span class="data-label">Remaining:</span>
            <span class="data-value">${remaining}</span>
            <span class="detail-separator">|</span>
            <span class="data-label">Strike:</span>
            <span class="data-value strike-price">${strike}</span>
            <span class="detail-separator">|</span>
            <span class="data-label">Filed:</span>
            <span class="data-value">${filedDate}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  renderConvertibles(convertibles) {
    if (!convertibles || convertibles.length === 0) {
      return '<p style="color: #666;">No convertible data available</p>';
    }

    return convertibles.map(c => {
      const details = c.details || 'Convertible debt';
      const remaining = c.convertible_debt_remaining ? formatCurrency(c.convertible_debt_remaining) : 'N/A';
      const conversionPrice = c.conversion_price ? `$${c.conversion_price.toFixed(2)}` : 'N/A';
      const filedDate = c.filed_at ? this.formatDate(c.filed_at) : 'N/A';

      return `
        <div class="convertible-item">
          <div class="convertible-details">${details}</div>
          <div class="convertible-data">
            <span class="data-label">Remaining:</span>
            <span class="data-value">${remaining}</span>
            <span class="detail-separator">|</span>
            <span class="data-label">Conversion:</span>
            <span class="data-value">${conversionPrice}</span>
            <span class="detail-separator">|</span>
            <span class="data-label">Filed:</span>
            <span class="data-value">${filedDate}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    } catch (e) {
      return dateStr;
    }
  }

  update(data) {
    this.render(data);
  }
}

// Make it available for import
if (typeof module !== 'undefined' && module.exports) {
  module.exports = InPlayDilutionSection;
}