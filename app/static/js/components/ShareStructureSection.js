// Share Structure Section Component
class ShareStructureSection {
  constructor(containerElement) {
    this.container = containerElement;
  }

  // Render the share structure section with the enhanced layout
  render(data) {
    if (!data) return;

    // Clear existing content
    this.container.innerHTML = '';

    // Create the container for the share structure
    const shareStructureContainer = document.createElement('div');
    shareStructureContainer.className = 'share-structure-container';

    // Create the authorized shares row
    const authorizedRow = this.createShareStructureRow('Authorized', data.authorized);
    
    // Create the outstanding shares row
    const outstandingRow = this.createShareStructureRow('Outstanding', data.outstanding);
    
    // Create the float shares row
    const floatRow = this.createShareStructureRow('Float', data.float);

    // Append the rows to the container
    shareStructureContainer.appendChild(authorizedRow);
    shareStructureContainer.appendChild(outstandingRow);
    shareStructureContainer.appendChild(floatRow);

    // Add the container to the main container
    this.container.appendChild(shareStructureContainer);
  }

  // Create a share structure row with label and value
  createShareStructureRow(label, value) {
    const row = document.createElement('div');
    row.className = 'share-structure-row';
    
    const labelElement = document.createElement('span');
    labelElement.className = 'share-structure-label';
    labelElement.textContent = label;
    
    const valueElement = document.createElement('span');
    valueElement.className = 'share-structure-value';
    valueElement.textContent = Formatters.fmt_millions(value);
    
    const sectionElement = document.createElement('div');
    sectionElement.className = `share-structure-${label.toLowerCase()}`;
    sectionElement.appendChild(labelElement);
    sectionElement.appendChild(valueElement);
    
    return sectionElement;
  }
}