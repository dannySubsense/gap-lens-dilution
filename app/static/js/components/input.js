// Ticker input component
class TickerInput {
  constructor(inputElement, state) {
    this.inputElement = inputElement;
    this.state = state;
  }

  // Validate ticker input
  validateInput(ticker) {
    return Validators.validateTicker(ticker);
  }

  // Format ticker input
  formatInput(inputElement) {
    const value = inputElement.value;
    if (value) {
      inputElement.value = value.toUpperCase();
    }
  }
}