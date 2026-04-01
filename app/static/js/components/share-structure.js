// Share structure component for displaying share structure data
class ShareStructureComponent {
  constructor(containerElement) {
    this.container = containerElement;
  }

  // Render share structure data
  render(data) {
    if (!data) return;

    // Clear existing content
    this.container.innerHTML = '';

    // Create share structure rows
    const rows = [
      { label: 'Float', value: data.float, formatter: 'formatShares' },
      { label: 'Outstanding Shares', value: data.outstanding, formatter: 'formatShares' },
      { label: 'Market Cap', value: data.marketCap, formatter: 'formatMarketCap' },
      { label: 'Insider Ownership', value: data.insiderOwnership, formatter: 'formatPercentage' },
      { label: 'Institutional Ownership', value: data.institutionalOwnership, formatter: 'formatPercentage' }
    ];

    // Add rows to the container
    rows.forEach(row => {
      const dataRow = this.createDataRow(row.label, row.value, row.formatter);
      this.container.appendChild(dataRow);
    });
  }

  // Create a single data row
  createDataRow(label, value, formatter) {
    const row = document.createElement('div');
    row.className = 'data-row';
    
    // Format value if formatter is provided
    let formattedValue = value;
    if (formatter && Formatters[formatter]) {
      formattedValue = Formatters[formatter](value);
    }
    
    row.innerHTML = `
      <span class="label">${label}</span>
      <span class="value">${formattedValue}</span>
    `;
    
    return row;
  }
}