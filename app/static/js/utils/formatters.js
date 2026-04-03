// Number formatting utilities
const Formatters = {
  // Format large numbers with K, M, B suffixes
  formatLargeNumber: function(num) {
    if (num >= 1000000000) {
      return '$' + (num / 1000000000).toFixed(2) + 'B';
    } else if (num >= 1000000) {
      return '$' + (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
      return '$' + (num / 1000).toFixed(2) + 'K';
    } else {
      return '$' + num.toString();
    }
  },

  // Format percentage values
  formatPercentage: function(value) {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(2) + '%';
  },

  // Format currency values
  formatCurrency: function(value) {
    if (value === null || value === undefined) return 'N/A';
    return '$' + value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  },

  // Format share counts with K, M, B suffixes
  formatShares: function(shares) {
    if (shares >= 1000000000) {
      return (shares / 1000000000).toFixed(2) + 'B';
    } else if (shares >= 1000000) {
      return (shares / 1000000).toFixed(2) + 'M';
    } else if (shares >= 1000) {
      return (shares / 1000).toFixed(2) + 'K';
    } else {
      return shares.toString();
    }
  },

  // Format numbers with M, K, B notation
  fmt_millions: function(num) {
    if (num < 1000) {
      return num.toString();
    } else if (num < 1000000) {
      return (num/1000).toFixed(1) + 'K';
    } else if (num < 1000000000) {
      return (num/1000000).toFixed(1) + 'M';
    } else {
      return (num/1000000000).toFixed(1) + 'B';
    }
  }
};

// Make it available globally
if (typeof window !== 'undefined') {
  window.Formatters = Formatters;
} else {
  module.exports = Formatters;
}