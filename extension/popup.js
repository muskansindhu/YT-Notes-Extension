document.addEventListener('DOMContentLoaded', function () {
  getCurrentTabUrl(function (url) {
    getVideoTitle(url, function (videoTitle) {
      fetchTimeStampAndConvertTime(function (formattedTime) {
        populateInputFields(videoTitle, formattedTime, url);
      });
    });
  });

  document.getElementById('submitButton').addEventListener('click', function () {
    var videoTitle = document.getElementById('videoTitle').value;
    var currentTimeStamp = document.getElementById('currentTimeStamp').value;
    var videoUrl = document.getElementById('videoUrl').value;

    var data = {
      videoUrl: videoUrl,
      videoTitle: videoTitle,
      currentTimeStamp: currentTimeStamp,
      noteTitle: document.getElementById('noteTitle').value,
      largeText: document.getElementById('largeText').value
    };

    fetch('http://127.0.0.1:5000/add_notes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Success:', data);
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  });

    function getCurrentTabUrl(callback) {
      chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        var currentTab = tabs[0];
        var url = currentTab.url;
        callback(url);
      });
    }
  
    function getVideoTitle(url, callback) {
      chrome.tabs.executeScript(
        { code: 'document.querySelector("#title > h1 > yt-formatted-string").innerText' },
        function (result) {
          var videoTitle = result[0];
          callback(videoTitle);
        }
      );
    }
  
    function fetchTimeStampAndConvertTime(callback) {
      chrome.tabs.executeScript(
        {
          code: 'document.querySelector("#movie_player > div.ytp-chrome-bottom > div.ytp-chrome-controls > div.ytp-left-controls > div.ytp-time-display.notranslate > span:nth-child(2) > span.ytp-time-current").innerText'
        },
        function (result) {
          var formattedTime = result[0];
          console.log('Formatted Time:', formattedTime);
          callback(formattedTime);
        }
      );
    }
  
    function populateInputFields(videoTitle, formattedTime, videoUrl) {
      document.getElementById('videoTitle').value = videoTitle;
      document.getElementById('currentTimeStamp').value = formattedTime;
      document.getElementById('videoUrl').value = videoUrl;
    }
  });
  