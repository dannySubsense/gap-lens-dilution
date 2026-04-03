class TickerInputSection {
  constructor(containerElement, onSearch) {
    this.container = containerElement;
    this.onSearch = onSearch;
    this.isLoading = false;
    this.render();
  }

  render() {
    this.container.innerHTML = `
      <div class="ticker-input-container">
        <div class="input-group">
          <input 
            type="text" 
            id="tickerInput" 
            class="input-field ticker-input" 
            placeholder="Enter ticker symbol (e.g. AAPL)" 
            aria-label="Ticker symbol"
          >
          <button id="searchButton" class="btn-primary search-button" aria-label="Search">
            <span class="search-button-text">Search</span>
            <span class="search-button-spinner" style="display: none;">
              <svg class="spinner" width="20" height="20" viewBox="0 0 24 24">
                <circle class="spinner-circle" cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"></circle>
              </svg>
            </span>
          </button>
        </div>
        <div class="error-alert" role="alert" style="display: none;">
          <span class="error-message"></span>
        </div>
      </div>
    `;

    // Add event listeners
    const tickerInput = this.container.querySelector('#tickerInput');
    const searchButton = this.container.querySelector('#searchButton');
    
    // Auto-convert to uppercase
    tickerInput.addEventListener('input', (e) => {
      const value = e.target.value;
      if (value) {
        e.target.value = value.toUpperCase();
      }
    });
    
    // Enter key support
    tickerInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.handleSearch();
      }
    });
    
    // Search button click
    searchButton.addEventListener('click', () => {
      this.handleSearch();
    });
  }

  async handleSearch() {
    const tickerInput = this.container.querySelector('#tickerInput');
    const ticker = tickerInput.value.trim();
    
    // Validate ticker format
    if (!Validators.validateTicker(ticker)) {
      this.showError('Please enter a valid ticker symbol (1-5 characters)');
      return;
    }
    
    this.hideError();
    this.setLoading(true);
    
    try {
      await this.onSearch(ticker);
    } catch (error) {
      this.showError(error.message || 'Failed to fetch dilution data');
    } finally {
      this.setLoading(false);
    }
  }

  showError(message) {
    const errorAlert = this.container.querySelector('.error-alert');
    const errorMessage = this.container.querySelector('.error-message');
    
    if (errorAlert && errorMessage) {
      errorMessage.textContent = message;
      errorAlert.style.display = 'block';
    }
  }

  hideError() {
    const errorAlert = this.container.querySelector('.error-alert');
    if (errorAlert) {
      errorAlert.style.display = 'none';
    }
  }

  setLoading(loading) {
    this.isLoading = loading;
    const tickerInput = this.container.querySelector('#tickerInput');
    const searchButton = this.container.querySelector('#searchButton');
    const searchText = searchButton.querySelector('.search-button-text');
    const searchSpinner = searchButton.querySelector('.search-button-spinner');
    
    if (loading) {
      tickerInput.disabled = true;
      searchButton.disabled = true;
      searchText.style.display = 'none';
      searchSpinner.style.display = 'inline';
    } else {
      tickerInput.disabled = false;
      searchButton.disabled = false;
      searchText.style.display = 'inline';
      searchSpinner.style.display = 'none';
    }
  }
}