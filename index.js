const Parser = require('rss-parser');
const sanitize = require('sanitize-filename')
const axios = require('axios');
const https = require('https');
const fs = require('fs');

const parser = new Parser();

const downloadMp3 = function(filename, link, success, errorFunction) {
    console.log(`${filename} -> ${link}`)
    const file = fs.createWriteStream(filename);
    https.get(link, (response) => {
        response.pipe(file)
        response.on('end', function() {
            success(filename)
        })
    }).on('error', errorFunction)
}

const sanitiseFilename = function(filename) {
    const sanitised = filename.replaceAll('/', '-').replaceAll(' ', '_')
    return sanitize(sanitised)
}

const errorHandler = function(error) {
    console.error(error)
}

const handlePodcastItem = async (item) => {
    if (item.enclosure && item.enclosure.url && item.enclosure.type === 'audio/mpeg') {
      const filename = sanitiseFilename(`${item.title}.mp3`)
      const done = (filename) => {
          console.log(`Downloaded ${filename}`)
      }
      downloadMp3(filename, item.enclosure.url, done, errorHandler)
    }
  }

(async () => {
  try {
    const feed = await parser.parseURL('https://feeds.blubrry.com/feeds/the_glass_cannon.xml');
    
    handlePodcastItem(feed.items[0]);
    
  } catch (error) {
    console.error(error);
  }
})();