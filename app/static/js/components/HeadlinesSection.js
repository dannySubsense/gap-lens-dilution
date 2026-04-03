class HeadlinesSection {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.headlinesData = [];
  }

  render(data) {
    if (!this.container || !data || !data.news) return;

    // Get first 3 news items
    const newsItems = data.news.slice(0, 3);

    if (newsItems.length === 0) {
      this.container.innerHTML = '<p style="color: #666;">No recent news available.</p>';
      return;
    }

    this.container.innerHTML = `
      <div class="news-feed">
        ${newsItems.map(item => this.renderNewsItem(item)).join('')}
      </div>
    `;
  }

  renderNewsItem(item) {
    const formType = item.form_type || 'news';
    const sourceTag = this.getSourceTag(formType);
    const sourceClass = this.getSourceClass(formType);
    const timestamp = this.formatTimestamp(item.filed_at);
    const title = item.title || item.summary || 'Untitled';

    return `
      <div class="news-item">
        <div class="news-source ${sourceClass}">${sourceTag}</div>
        <div class="news-content">
          <div class="news-timestamp">${timestamp}</div>
          <div class="news-title">${title}</div>
        </div>
      </div>
    `;
  }

  getSourceTag(formType) {
    if (!formType) return 'NEWS';
    const ft = formType.toLowerCase();
    if (ft === 'grok') return 'GROK';
    if (ft === 'jmt415') return 'JMT415';
    if (ft === 'news') return 'NEWS';
    if (ft.includes('8-k')) return '8-K';
    if (ft.includes('10-')) return formType.toUpperCase();
    return formType.toUpperCase();
  }

  getSourceClass(formType) {
    if (!formType) return 'source-news';
    const ft = formType.toLowerCase();
    if (ft === 'grok') return 'source-grok';
    if (ft === 'jmt415') return 'source-jmt';
    if (ft.includes('8-k')) return 'source-filing';
    return 'source-news';
  }

  formatTimestamp(dateStr) {
    if (!dateStr) return '';

    try {
      const date = new Date(dateStr);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');

      return `${year}-${month}-${day} ${hours}:${minutes}`;
    } catch (e) {
      return dateStr;
    }
  }
}

