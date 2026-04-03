// API service for backend communication
class ApiService {
  // Get dilution data for a ticker
  async getDilutionData(ticker) {
    const response = await fetch(`/api/v1/dilution/${ticker}`);
    if (!response.ok) {
      const error = await response.json();
      // Handle specific error types with user-friendly messages
      if (response.status === 404) {
        throw new Error(`Ticker '${ticker}' not found. Please verify the symbol.`);
      } else if (response.status === 429) {
        throw new Error('Rate limit reached (50 tickers/day). Try again tomorrow.');
      } else if (response.status >= 500) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      } else {
        throw new Error(error.detail || 'API error');
      }
    }
    return response.json();
  }
}