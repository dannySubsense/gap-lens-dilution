/**
 * Dilution Parser
 * Parses warrant and convertible data
 */

function parseInPlayDilution(data) {
    if (!data) return { warrants: [], convertibles: [] };
    
    return {
        warrants: data.warrants || [],
        convertibles: data.convertibles || []
    };
}

function isInTheMoney(instrument, currentPrice) {
    if (!instrument || !currentPrice) return false;
    
    const strike = parseFloat(instrument.strike_price || instrument.conversion_price);
    if (isNaN(strike)) return false;
    
    // For warrants/convertibles, in-the-money means current price > strike
    return currentPrice > strike;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { parseInPlayDilution, isInTheMoney };
}
