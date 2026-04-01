// Timeframe selector component for chart timeframe selection
class TimeframeSelector {
  constructor(containerElement, onTimeframeChange) {
    this.container = containerElement;
    this.onTimeframeChange = onTimeframeChange;
    this.timeframes = ['1D', '1W', '1M', '3M', 'YTD', '1Y'];
    this.activeTimeframe = '3M';
  }

  render() {
    // Create timeframe buttons
    const buttonsHtml = this.timeframes.map(tf => {
      const activeClass = tf === this.activeTimeframe ? 'active' : '';
      return `<button class="timeframe-button ${activeClass}" data-timeframe="${tf}">${tf}</button>`;
    }).join('');

    this.container.innerHTML = buttonsHtml;

    // Add event listeners to buttons
    const buttons = this.container.querySelectorAll('.timeframe-button');
    buttons.forEach(button => {
      button.addEventListener('click', (e) => {
        const timeframe = e.target.dataset.timeframe;
        this.setTimeframe(timeframe);
      });
    });
  }

  setTimeframe(timeframe) {
    this.activeTimeframe = timeframe;
    
    // Update button states
    const buttons = this.container.querySelectorAll('.timeframe-button');
    buttons.forEach(button => {
      if (button.dataset.timeframe === timeframe) {
        button.classList.add('active');
      } else {
        button.classList.remove('active');
      }
    });

    // Notify callback
    if (this.onTimeframeChange) {
      this.onTimeframeChange(timeframe);
    }
  }

  getActiveTimeframe() {
    return this.activeTimeframe;
  }

  updateTimeframeDisplay(activeTimeframe) {
    this.activeTimeframe = activeTimeframe;
    const buttons = this.container.querySelectorAll('.timeframe-button');
    buttons.forEach(button => {
      if (button.dataset.timeframe === activeTimeframe) {
        button.classList.add('active');
      } else {
        button.classList.remove('active');
      }
    });
  }
}