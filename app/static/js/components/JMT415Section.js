// JMT415Section.js - JMT415 Previous Notes Component
class JMT415Section {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    render(data) {
        if (!this.container || !data || !data.news) return;

        // Filter for JMT415 notes
        const jmt415Notes = data.news.filter(item =>
            item.form_type && item.form_type.toLowerCase() === 'jmt415'
        );

        if (jmt415Notes.length === 0) {
            this.container.innerHTML = '';
            return;
        }

        // Get the most recent JMT415 note
        const latestNote = jmt415Notes[0];

        this.container.innerHTML = `
            <div class="jmt415-previous-notes">
                <h2 class="jmt415-title">JMT415 Previous Notes</h2>
                <div class="jmt415-note">
                    <div class="jmt415-date">${this.formatDate(latestNote.filed_at)}</div>
                    <div class="jmt415-ticker">${data.ticker || ''}</div>
                    <div class="jmt415-text">${this.formatNoteText(latestNote.body || latestNote.summary)}</div>
                </div>
            </div>
        `;
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const date = new Date(dateStr);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        } catch (e) {
            return dateStr;
        }
    }

    formatNoteText(text) {
        if (!text) return '';

        // Split into paragraphs and format
        const paragraphs = text.split('\n').filter(p => p.trim().length > 0);

        return paragraphs.map(p => {
            // Add dash for bullet points if line starts with dash or hyphen
            if (p.trim().startsWith('-')) {
                return `<p class="jmt415-bullet">${p.trim()}</p>`;
            }
            return `<p>${p.trim()}</p>`;
        }).join('');
    }

    update(data) {
        this.render(data);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JMT415Section;
}