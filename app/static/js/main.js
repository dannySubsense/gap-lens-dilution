// Main application entry point
function initializeApp() {
  console.log('initializeApp called');
  try {
    // Initialize API service
    const apiService = new ApiService();
    console.log('ApiService created');
  
  // Initialize components
  const appState = new State();
  
  // Get DOM elements
  const tickerInputSection = document.getElementById('tickerInputSection');
  
  // Initialize header component
  const headerElement = document.getElementById('companyHeader');
  let headerComponent = null;
  if (headerElement) {
    headerComponent = new HeaderComponent(headerElement, appState);
    headerComponent.renderEmpty();
  }
  
  // Initialize chart and timeframe components
  let chartComponent = null;
  let timeframeSelector = null;
  let metricsComponent = null;
  let shareStructureComponent = null;
  
  // Initialize timeframe selector if container exists
  const timeframeContainer = document.querySelector('.timeframe-buttons');
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
  const metricsContainer = document.querySelector('.metrics-grid');
  if (metricsContainer) {
    metricsComponent = new MetricsComponent(metricsContainer);
  }
  
  // Initialize share structure component
  const shareStructureContainer = document.querySelector('.share-structure');
  if (shareStructureContainer) {
    shareStructureComponent = new ShareStructureSection(shareStructureContainer);
  }
  
  // Initialize chart component
  const chartContainer = document.querySelector('.chart-container');
  if (chartContainer) {
    chartComponent = new ChartComponent(chartContainer);
    chartComponent.render();
  }
  
  // Initialize JMT415 section
  const jmt415Container = document.getElementById('jmt415Section');
  let jmt415Section = null;
  if (jmt415Container) {
    jmt415Section = new JMT415Section('jmt415Section');
  }

  // Initialize Risk Assessment section
  const riskAssessmentContainer = document.getElementById('riskAssessmentSection');
  let riskSection = null;
  if (riskAssessmentContainer) {
    riskSection = new RiskAssessmentSection('riskAssessmentSection');
  }

  // Initialize Offering Ability section
  const offeringAbilityContainer = document.getElementById('offeringAbilitySection');
  let offeringSection = null;
  if (offeringAbilityContainer) {
    offeringSection = new OfferingAbilitySection('offeringAbilitySection');
  }

  // Initialize In-Play Dilution section
  const inPlayDilutionContainer = document.getElementById('inPlayDilutionSection');
  let inPlaySection = null;
  if (inPlayDilutionContainer) {
    inPlaySection = new InPlayDilutionSection('inPlayDilutionSection');
  }
  
  // Initialize headlines section FIRST (before ticker input that uses it)
  const headlinesContainer = document.getElementById('headlinesSection');
  let headlinesSection = null;
  if (headlinesContainer) {
    headlinesSection = new HeadlinesSection('headlinesSection');
  }
  console.log('headlinesSection initialized');

  // Initialize the ticker input section component
  console.log('tickerInputSection check:', !!tickerInputSection);
  if (tickerInputSection) {
    console.log('Creating TickerInputSection...');
    const tickerInputComponent = new TickerInputSection(tickerInputSection, async (ticker) => {
      try {
        // Fetch dilution data from API
        const data = await apiService.getDilutionData(ticker);

        // Update header with ticker info
        if (headerComponent) {
          headerComponent.render(data);
        }

        // Update components with data
        if (metricsComponent) {
          metricsComponent.render(data);
        }

        if (shareStructureComponent) {
          shareStructureComponent.render(data);
        }

        if (chartComponent) {
          chartComponent.updateChart(ticker, appState.getCurrentState().selectedTimeframe || '3M');
        }

        if (riskSection) {
          riskSection.render(data);
        }

        if (offeringSection) {
          offeringSection.render(data);
        }

        if (inPlaySection) {
          inPlaySection.render(data);
        }

        if (headlinesSection) {
          headlinesSection.render(data);
        }

        if (jmt415Section) {
          jmt415Section.render(data);
        }

        appState.setLoading(false);
      } catch (error) {
        console.error('Error fetching dilution data:', error);
        throw error;
      }
    });
    console.log('TickerInputSection created');
  }
  console.log('initializeApp complete');
  } catch (e) {
    console.error('initializeApp error:', e);
  }
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  // DOM is already loaded (scripts loaded after DOM)
  initializeApp();
}