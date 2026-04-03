/**
 * Offering Ability Section Component
 * Displays offering ability: Shelf Capacity, ATM, Equity Line, S-1 Offering
 */

class OfferingAbilitySection {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    render(data) {
        if (!this.container || !data) return;

        const registrations = data.registrations || [];

        // Parse registrations to find specific types
        const shelfReg = registrations.find(r => r.type === 'SHELF' && r.effective_status);
        const atmReg = registrations.find(r => r.is_atm && r.effective_status);
        const equityLineReg = registrations.find(r => r.type === 'SPA' && r.effective_status);
        const s1Offering = registrations.find(r => r.type === 'OFFERING' && r.effective_status);

        const shelfCapacity = shelfReg ? shelfReg.offering_amount : 0;
        const hasATM = !!atmReg;
        const hasEquityLine = !!equityLineReg;
        const hasS1 = !!s1Offering;

        this.container.innerHTML = `
            <div class="offering-ability">
                <h2 class="offering-title">Offering Ability</h2>
                <div class="offering-items">
                    ${this.renderShelfCapacity(shelfCapacity)}
                    ${this.renderATMStatus(hasATM)}
                    ${this.renderEquityLine(hasEquityLine)}
                    ${this.renderS1Offering(hasS1)}
                </div>
            </div>
        `;
    }

    renderShelfCapacity(capacity) {
        const formattedCapacity = capacity ? `$${(capacity / 1000000).toFixed(2)}M` : '$0.00M';
        const textClass = capacity > 0 ? 'text-red' : 'text-white';

        return `
            <div class="offering-item">
                <span class="offering-label">Shelf Capacity:</span>
                <span class="offering-value ${textClass}">${formattedCapacity}</span>
            </div>
        `;
    }

    renderATMStatus(hasATM) {
        const status = hasATM ? 'Active ATM' : 'No ATM';
        const textClass = hasATM ? 'text-red' : 'text-white';

        return `
            <div class="offering-item">
                <span class="offering-value ${textClass}">${status}</span>
            </div>
        `;
    }

    renderEquityLine(hasEquityLine) {
        const status = hasEquityLine ? 'Active Equity Line' : 'No Equity Line';
        const textClass = hasEquityLine ? 'text-red' : 'text-white';

        return `
            <div class="offering-item">
                <span class="offering-value ${textClass}">${status}</span>
            </div>
        `;
    }

    renderS1Offering(hasS1) {
        const status = hasS1 ? 'Active S-1 Offering' : 'No S-1 Offering';
        const textClass = hasS1 ? 'text-red' : 'text-white';

        return `
            <div class="offering-item">
                <span class="offering-value ${textClass}">${status}</span>
            </div>
        `;
    }

    update(data) {
        this.render(data);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfferingAbilitySection;
}
