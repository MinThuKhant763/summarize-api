# summarize-api
# PDF Summarization API - Test Scripts

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Test Scripts](#test-scripts)
  - [1. Basic Summarization Test](#1-basic-summarization-test)
  - [2. Test Save Endpoint](#2-test-save-endpoint)
  - [3. Error Handling Tests](#3-error-handling-tests)
  - [4. Security Tests](#4-security-tests)
  - [5. Batch Processing Test](#5-batch-processing-test)
- [Monitoring Scripts](#monitoring-scripts)
- [Cron Job Scripts](#cron-job-scripts)
- [Cleanup Scripts](#cleanup-scripts)

## 🛠️ Prerequisites

### Required Software
```bash
# Install required tools
brew install curl jq  # macOS
# OR
sudo apt-get install curl jq  # Ubuntu/Debian

# Install Python dependencies
pip install requests

#!/bin/bash

echo "=== Basic Summarization Test ==="

# Test with a sample PDF
curl -X POST \
  -F "file=@./test-data/test_document.pdf" \
  -F "apiFunction=https://achieversprofile.com/api/save" \
  -F "documentID=test_doc_001" \
  -F "dataSearchField=user_profile" \
  -F "dataField=profile_data" \
  http://localhost:5000/summarize | jq '.'

# Check if file was created
if [ -f "~/Desktop/summary-api/summaries/test_doc_001.json" ]; then
    echo "✓ Summary file created successfully"
    cat ~/Desktop/summary-api/summaries/test_doc_001.json | jq '.'
else
    echo "✗ Summary file not found"
fi

#!/bin/bash

echo "=== Test Save Endpoint ==="

# Test the test-save endpoint
curl -X POST \
  "http://localhost:5000/test-save?apiFunction=https://achieversprofile.com/api/save&documentID=test_save_001&dataSearchField=test_search&dataField=test_data&summary=This%20is%20a%20test%20summary" | jq '.'

# Verify the file was created
if [ -f "~/Desktop/summary-api/summaries/test_save_001.json" ]; then
    echo "✓ Test save file created successfully"
    cat ~/Desktop/summary-api/summaries/test_save_001.json | jq '.'
else
    echo "✗ Test save file not found"
fi

#!/bin/bash

echo "=== Setting up Cron Jobs ==="

# Create the processing script executable
chmod +x /Users/minthukhant/Desktop/summary-api/process_json_files.py

# Add cron job to process JSON files every 10 minutes
(crontab -l 2>/dev/null; echo "*/10 * * * * /usr/bin/python3 /Users/minthukhant/Desktop/summary-api/process_json_files.py") | crontab -

# Add cron job for health check every hour
(crontab -l 2>/dev/null; echo "0 * * * * /Users/minthukhant/Desktop/summary-api/monitor_health.sh") | crontab -

echo "Cron jobs installed:"
crontab -l