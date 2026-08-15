/* Interactive JavaScript for Task 1 Web UI */
document.addEventListener('DOMContentLoaded', () => {
  // Dropzone drag-and-drop file upload handler
  const dropzone = document.getElementById('csv-dropzone');
  const fileInput = document.getElementById('csv_file');
  const fileNameDisplay = document.getElementById('selected-file-name');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateFileName();
      }
    });

    fileInput.addEventListener('change', updateFileName);

    function updateFileName() {
      if (fileInput.files && fileInput.files[0]) {
        fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name} (${Math.round(fileInput.files[0].size / 1024)} KB)`;
        fileNameDisplay.style.display = 'block';
      }
    }
  }

  // Quick Sample Loader button
  const loadSampleBtn = document.getElementById('load-sample-csv-btn');
  const rawUrlsTextarea = document.getElementById('raw_urls');
  if (loadSampleBtn && rawUrlsTextarea) {
    loadSampleBtn.addEventListener('click', () => {
      rawUrlsTextarea.value = [
        'https://en.wikipedia.org/wiki/Sundar_Pichai',
        'https://en.wikipedia.org/wiki/Satya_Nadella',
        'https://en.wikipedia.org/wiki/Tim_Cook',
        'https://en.wikipedia.org/wiki/Jensen_Huang',
        'https://en.wikipedia.org/wiki/Sam_Altman'
      ].join('\n');
    });
  }

  // Submit Loading State
  const uploadForm = document.getElementById('upload-form');
  const submitBtn = document.getElementById('upload-submit-btn');
  const loadingIndicator = document.getElementById('upload-loading');

  if (uploadForm && submitBtn && loadingIndicator) {
    uploadForm.addEventListener('submit', () => {
      submitBtn.disabled = true;
      submitBtn.innerText = 'Harvesting URLs & Indexing Vectors...';
      loadingIndicator.style.display = 'block';
    });
  }
});
