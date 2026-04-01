// State management for the Gap Lens Dilution Dashboard
class State {
  constructor() {
    this.ticker = '';
    this.loading = false;
    this.error = null;
    this.data = null;
    this.selectedTimeframe = '3M';
    this.observers = [];
  }

  // Subscribe to state changes
  subscribe(callback) {
    this.observers.push(callback);
  }

  // Notify all observers of state changes
  notifyObservers() {
    this.observers.forEach(callback => callback(this));
  }

  // Set ticker symbol
  setTicker(ticker) {
    this.ticker = ticker;
    this.notifyObservers();
  }

  // Set loading state
  setLoading(loading) {
    this.loading = loading;
    this.notifyObservers();
  }

  // Set error state
  setError(error) {
    this.error = error;
    this.notifyObservers();
  }

  // Set data
  setData(data) {
    this.data = data;
    this.loading = false;
    this.notifyObservers();
  }

  // Set timeframe
  setTimeframe(timeframe) {
    this.selectedTimeframe = timeframe;
    this.notifyObservers();
  }

  // Reset state
  reset() {
    this.ticker = '';
    this.loading = false;
    this.error = null;
    this.data = null;
    this.notifyObservers();
  }

  // Get current state
  getCurrentState() {
    return {
      ticker: this.ticker,
      loading: this.loading,
      error: this.error,
      data: this.data,
      selectedTimeframe: this.selectedTimeframe
    };
  }
}

// Make it available globally
if (typeof window !== 'undefined') {
  window.State = State;
} else {
  module.exports = State;
}