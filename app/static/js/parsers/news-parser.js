// Example of how the component would work
class NewsParser {
  parse(newsData) {
    return newsData.map(item => {
      return {
        source: item.source,
        title: item.title,
        url: item.url,
        timestamp: item.timestamp
      };
    });
  }
}

r;