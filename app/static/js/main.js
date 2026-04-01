// Main application entry point
document.addEventListener('DOMContentLoaded', function() {
  // Initialize API service
  const apiService = new ApiService();
  
  // Initialize components
  const appState = new State();
  
  // Get DOM elements
  const tickerInput = document.getElementById('tickerInput');
  const searchButton = document.getElementById('searchButton');
  const errorAlert = document.getElementById('errorAlert');
  const errorMessage = document.getElementById('errorMessage');
  const chartContainer = document.querySelector('.chart-container');
  const timeframeContainer = document.querySelector('.timeframe-buttons');
  const metricsContainer = document.querySelector('.metrics-grid');
  const shareStructureContainer = document.querySelector('.share-structure');
  
  // Initialize chart and timeframe components
  let chartComponent = null;
  let timeframeSelector = null;
  let metricsComponent = null;
  let shareStructureComponent = null;
  
  // Initialize timeframe selector if container exists
  if (timeframeContainer) {
    timeframeSelector = new TimeframeSelector(timeframeContainer, (newTimeframe) => {
      console.log('Timeframe changed to:', newTimeframe);
      if (chartComponent) {
        chartComponent.updateTimeframe(newTimeframe);
      }
    });
    timeframeSelector.render();
  }
  
  // Initialize metrics component
  if (metricsContainer) {
    metricsComponent = new MetricsComponent(metricsContainer);
  }
  
  // Initialize share structure component
  if (shareStructureContainer) {
    shareStructureComponent = new ShareStructureComponent(shareStructureContainer);
  }
  
  // Initialize chart component
  if (chartContainer) {
    chartComponent = new ChartComponent(chartContainer);
    chartComponent.render();
  }
  
  // Hide error alert initially
  if (errorAlert) {
    errorAlert.style.display = 'none';
  }
  
  // Add input validation and formatting as user types
  if (tickerInput) {
    tickerInput.addEventListener('input', function(e) {
      const value = e.target.value;
      if (value) {
        e.target.value = value.toUpperCase();
      }
    });
  }
  
  // Add Enter key support on ticker input
  if (tickerInput) {
    tickerInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') searchButton.click();
    });
  }

  // Add search button event listener
  if (searchButton) {
    searchButton.addEventListener('click', async function() {
      const ticker = tickerInput.value.trim();
      
      // Validate ticker format
      if (!Validators.validateTicker(ticker)) {
        if (errorAlert) {
          errorAlert.style.display = 'block';
        }
        if (errorMessage) {
          errorMessage.textContent = 'Please enter a valid ticker symbol (1-5 letters)';
        }
        return;
      }
      
      // Reset error display
      if (errorAlert) {
        errorAlert.style.display = 'none';
      }
      
      try {
        appState.setLoading(true);
        
        // Fetch dilution data from API
        const data = await apiService.getDilutionData(ticker);
        
        // Debug logging
        console.log('Data received:', data);
        console.log('metricsComponent:', metricsComponent);
        
        // Update metrics component with data
        if (metricsComponent) {
          metricsComponent.render(data);
        }
        
        // Update share structure component with data
        if (shareStructureComponent) {
          shareStructureComponent.render(data);
        }
        
        // Update chart with the searched ticker
        if (chartComponent) {
          chartComponent.updateChart(ticker, appState.getCurrentState().selectedTimeframe || '3M');
        }
        
        appState.setLoading(false);
      } catch (error) {
        console.error('Error fetching dilution data:', error);
        if (errorAlert) {
          errorAlert.style.display = 'block';
        }
        if (errorMessage) {
          errorMessage.textContent = error.message || 'Failed to fetch dilution data';
        }
        appState.setLoading(false);
      }
    });
  }
});
