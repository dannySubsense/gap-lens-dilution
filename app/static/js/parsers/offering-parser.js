/**
 * Offering Ability Parser
 * Parses offering_ability_desc into structured data
 */

function parseOfferingAbility(description) {
    if (!description) return { items: [] };
    
    const items = [];
    const lines = description.split('\n');
    
    lines.forEach(line => {
        // Parse format like "Shelf: $50M available" or "ATM: $0 remaining"
        const match = line.match(/^(.+?):\s*\$(\d+(?:\.\d+)?)([KM]?)\s*(.+)$/i);
        if (match) {
            const [, label, amount, unit, status] = match;
            const value = `$${amount}${unit} ${status}`;
            const capacity = parseFloat(amount) * (unit === 'M' ? 1000000 : unit === 'K' ? 1000 : 1);
            
            items.push({
                label: label.trim(),
                value: value.trim(),
                capacity: capacity
            });
        }
    });
    
    return { items };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { parseOfferingAbility };
}
