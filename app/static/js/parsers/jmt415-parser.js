// JMT415 Parser - Parse SEC filing data into dilution alerts
class JMT415Parser {
    // Parse SEC filing data and extract dilution alerts
    static parseSECData(data) {
        const alerts = [];
        
        // Sample data structure - in a real implementation, this would parse actual SEC data
        if (data && data.filings) {
            data.filings.forEach(filing => {
                // Check if this is a dilution-related filing (S-1, S-3, etc.)
                if (this.isDilutionFiling(filing.formType)) {
                    const alert = this.createDilutionAlert(filing);
                    if (alert) {
                        alerts.push(alert);
                    }
                }
            });
        }
        
        return alerts;
    }
    
    // Determine if a filing is dilution-related
    static isDilutionFiling(formType) {
        // Common dilution-related SEC forms
        const dilutionForms = ['S-1', 'S-3', 'S-4', 'S-8', 'F-3', 'F-10', 'F-6'];
        return dilutionForms.includes(formType);
    }
    
    // Create a dilution alert from filing data
    static createDilutionAlert(filing) {
        // In a real implementation, this would extract data from the actual filing
        // For now, we'll create sample alerts
        return {
            symbol: filing.ticker || 'TICK',
            description: this.generateAlertDescription(filing),
            time: filing.filingDate || new Date(),
            isNew: this.isNewFiling(filing.filingDate),
            isSignificant: this.isSignificantDilution(filing)
        };
    }
    
    // Generate alert description based on filing details
    static generateAlertDescription(filing) {
        const formType = filing.formType || 'S-1';
        const shares = filing.shares || 'unknown';
        return `DILUTION ALERT: ${formType} filing detected with ${shares} shares`;
    }
    
    // Check if filing is new (within last 7 days)
    static isNewFiling(filingDate) {
        if (!filingDate) return false;
        const now = new Date();
        const filing = new Date(filingDate);
        const diffTime = Math.abs(now - filing);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 7;
    }
    
    // Check if this is significant dilution
    static isSignificantDilution(filing) {
        // In a real implementation, this would check the actual dilution metrics
        // For now, we'll use a simple heuristic
        return filing.formType === 'S-1' || filing.formType === 'S-3';
    }
    
    // Sample data for testing
    static getSampleAlerts() {
        return [
            {
                symbol: 'AAPL',
                description: 'DILUTION ALERT: S-1 Filing - 50M Shares',
                time: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
                isNew: true,
                isSignificant: false
            },
            {
                symbol: 'GOOGL',
                description: 'DILUTION ALERT: S-3 Filing - 25M Shares',
                time: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
                isNew: false,
                isSignificant: true
            },
            {
                symbol: 'MSFT',
                description: 'DILUTION ALERT: S-4 Filing - 100M Shares',
                time: new Date(Date.now() - 48 * 60 * 60 * 1000), // 2 days ago
                isNew: false,
                isSignificant: false
            },
            {
                symbol: 'TSLA',
                description: 'DILUTION ALERT: S-8 Filing - 15M Shares',
                time: new Date(Date.now() - 72 * 60 * 60 * 1000), // 3 days ago
                isNew: false,
                isSignificant: true
            },
            {
                symbol: 'AMZN',
                description: 'DILUTION ALERT: S-3 Filing - 75M Shares',
                time: new Date(Date.now() - 96 * 60 * 60 * 1000), // 4 days ago
                isNew: false,
                isSignificant: false
            },
            {
                symbol: 'NVDA',
                description: 'DILUTION ALERT: F-3 Filing - 200M Shares',
                time: new Date(Date.now() - 120 * 60 * 60 * 1000), // 5 days ago
                isNew: false,
                isSignificant: true
            }
        ];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JMT415Parser;
}