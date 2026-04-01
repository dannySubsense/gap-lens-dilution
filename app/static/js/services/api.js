// API service for backend communication
class ApiService {
  // Get dilution data for a ticker
  async getDilutionData(ticker) {
    const response = await fetch(`/api/v1/dilution/${ticker}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API error');
    }
    return response.json();
  }
}
