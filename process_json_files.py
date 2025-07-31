#!/usr/bin/env python3
"""
Script to read and process JSON summary files from ~/Desktop/summary-api/summaries
"""
import os
import json
import glob
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='/Users/minthukhant/Desktop/summary-api/processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_json_files():
    """Process all JSON files in the summaries directory"""
    
    # Define the summaries directory
    summaries_dir = os.path.expanduser('~/Desktop/summary-api/summaries')
    
    # Check if directory exists
    if not os.path.exists(summaries_dir):
        logging.error(f"Directory {summaries_dir} does not exist")
        print(f"Error: Directory {summaries_dir} does not exist")
        return
    
    # Find all JSON files
    json_pattern = os.path.join(summaries_dir, '*.json')
    json_files = glob.glob(json_pattern)
    
    # Filter out any log files or other non-summary files
    json_files = [f for f in json_files if not f.endswith('processing.log')]
    
    if not json_files:
        logging.info("No JSON files found to process")
        print("No JSON files found to process")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    logging.info(f"Found {len(json_files)} JSON files to process")
    
    processed_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            # Read the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract data
            document_id = data.get('documentID', 'Unknown')
            summary = data.get('summary', 'No summary')
            api_function = data.get('apiFunction', 'Unknown')
            data_search_field = data.get('DataSearchField', '')
            data_field = data.get('DataField', '')
            
            print(f"Processing: {document_id}")
            logging.info(f"Processing document: {document_id}")
            
            # Send to external API if specified
            if api_function and api_function != 'Unknown':
                try:
                    # Prepare data for API
                    api_data = {
                        "documentID": document_id,
                        "DataSearchField": data_search_field,
                        "DataField": data_field,
                        "summary": summary,
                        "processed_at": datetime.now().isoformat()
                    }
                    
                    # Send to API
                    response = requests.post(
                        api_function,
                        json=api_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"  ✓ Sent {document_id} to {api_function}")
                        logging.info(f"Successfully sent {document_id} to {api_function}")
                    else:
                        print(f"  ✗ API returned status {response.status_code} for {document_id}")
                        logging.warning(f"API returned status {response.status_code} for {document_id}")
                        
                except Exception as e:
                    print(f"  ✗ Failed to send {document_id} to API: {e}")
                    logging.error(f"Failed to send {document_id} to API: {e}")
            
            # Log processing completion
            log_file = os.path.join(summaries_dir, 'processing_log.txt')
            with open(log_file, 'a') as log:
                log.write(f"[{datetime.now()}] Processed {document_id}\n")
            
            processed_count += 1
            
        except json.JSONDecodeError as e:
            print(f"Error reading JSON file {json_file}: {e}")
            logging.error(f"Error reading JSON file {json_file}: {e}")
            error_count += 1
        except Exception as e:
            print(f"Error processing file {json_file}: {e}")
            logging.error(f"Error processing file {json_file}: {e}")
            error_count += 1
    
    # Summary report
    summary_message = f"Processing complete: {processed_count} successful, {error_count} errors"
    print(f"\n{summary_message}")
    logging.info(summary_message)

def archive_processed_files():
    """Move processed files to archive directory"""
    
    summaries_dir = os.path.expanduser('~/Desktop/summary-api/summaries')
    archive_dir = os.path.join(summaries_dir, 'archive')
    
    # Create archive directory if it doesn't exist
    os.makedirs(archive_dir, exist_ok=True)
    
    # Find JSON files (excluding archive and log files)
    json_files = glob.glob(os.path.join(summaries_dir, '*.json'))
    json_files = [f for f in json_files if 'archive' not in f and not f.endswith('processing.log')]
    
    archived_count = 0
    for json_file in json_files:
        if os.path.isfile(json_file):
            filename = os.path.basename(json_file)
            destination = os.path.join(archive_dir, filename)
            
            # Move file
            try:
                os.rename(json_file, destination)
                print(f"Archived: {filename}")
                archived_count += 1
            except Exception as e:
                print(f"Failed to archive {filename}: {e}")
                logging.error(f"Failed to archive {filename}: {e}")
    
    if archived_count > 0:
        print(f"Archived {archived_count} files to {archive_dir}")
        logging.info(f"Archived {archived_count} files to {archive_dir}")

if __name__ == "__main__":
    print(f"Starting JSON file processing at {datetime.now()}")
    logging.info("Starting JSON file processing")
    
    try:
        process_json_files()
        # Uncomment the line below if you want to archive files after processing
        # archive_processed_files()
        print("Processing completed successfully")
        logging.info("Processing completed successfully")
    except Exception as e:
        print(f"Fatal error in processing: {e}")
        logging.error(f"Fatal error in processing: {e}")