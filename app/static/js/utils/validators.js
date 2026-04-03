// Validation utilities
const Validators = {
  // Validate ticker symbol format (1-5 alphanumeric characters)
  validateTicker: function(symbol) {
    if (!symbol) return false;
    
    // Remove whitespace and convert to uppercase
    const cleaned = symbol.trim().toUpperCase();
    
    // Check if it's 1-5 alphanumeric characters
    const isValid = /^[A-Z0-9]{1,5}$/.test(cleaned);
    
    return isValid;
  },

  // Validate numeric inputs
  validateNumber: function(value) {
    return typeof value === 'number' && !isNaN(value) && isFinite(value);
  },

  // Validate percentage (0-100 range)
  validatePercentage: function(value) {
    return this.validateNumber(value) && value >= 0 && value <= 100;
  },

  // Validate object has required fields
  validateDilutionData: function(data) {
    const requiredFields = [
      'offeringRisk',
      'offeringAbility',
      'dilutionRisk',
      'cashNeed',
      'cashRunway',
      'float',
      'outstanding',
      'marketCap',
      'insiderOwnership',
      'institutionalOwnership'
    ];

    for (let field of requiredFields) {
      if (data[field] === undefined) {
        return false;
      }
    }
    return true;
  }
};

// Make it available globally
if (typeof window !== 'undefined') {
  window.Validators = Validators;
} else {
  module.exports = Validators;
}