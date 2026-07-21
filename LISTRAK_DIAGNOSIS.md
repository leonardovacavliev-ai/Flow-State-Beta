# Listrak Crawl Issue - Root Cause Analysis

## Problem
User added 4 Listrak URLs in the Railway production app. The app showed "Successfully crawled NaN links" and the links were not checked as crawled.

## Investigation Results

### 1. Database Check
All 4 Listrak documents exist in PostgreSQL with `status: failed`:
```
Document 1: 2283752-integration-guide-yotpo - FAILED
Document 2: 6909272-loyalty-automations-in-listrak-conductor - FAILED  
Document 3: 2465793-listrak-conductor-steps - FAILED
Document 4: integrating-yotpo-loyalty-referrals-with-listrak - FAILED
```

### 2. Pinecone Check
No Listrak namespace found in Pinecone (only default namespace with 249 vectors exists).

### 3. Root Cause
**CRITICAL BUG**: The `app_admin_esp_routes.py` was calling a non-existent function!

**Incorrect code (line 151)**:
```python
filename = crawl_and_save(url, esp_name, BASE_PATH)
```

**Problem**: `crawl_and_save()` signature is:
```python
def crawl_and_save(csv_path, base_docs_path):
```

This function was designed for the old CSV-based system and expects:
1. `csv_path` - path to a CSV file
2. `base_docs_path` - base docs folder

But the ESP routes were calling it with:
1. `url` - a URL string
2. `esp_name` - ESP name
3. `BASE_PATH` - app base path

**Result**: The function failed silently (likely threw an exception trying to open a URL as a CSV file), returned `None`, and the ESP route marked all crawls as failed.

### 4. Local Testing
Created `crawl_single_url()` function and tested all 4 Listrak URLs locally:
- ✓ All 4 URLs crawl successfully
- ✓ Content extracted properly (2KB-7KB per document)
- ✓ Files saved to `docs/listrak/` folder

## Fix Applied

### 1. Created `crawl_single_url()` function in `crawler.py`:
```python
def crawl_single_url(url, esp_name, base_path):
    """
    Crawl a single URL and save to ESP folder.
    
    Args:
        url: URL to crawl
        esp_name: ESP name (e.g., 'klaviyo', 'listrak')
        base_path: Base path of the application
        
    Returns:
        filename if successful, None if failed
    """
```

### 2. Updated `app_admin_esp_routes.py`:
- Changed import from `crawl_and_save` to `crawl_single_url`
- Updated function call at line 151

## Next Steps

1. ✓ Push fix to GitHub
2. Test in production:
   - Try crawling one of the failed Listrak URLs again
   - Check database for `status: completed`
   - Check Pinecone for `listrak` namespace
   - Verify frontend updates checkboxes correctly

## Why the NaN?
The frontend likely received `results.success.length = 0` and `results.failed.length = 0` (empty arrays), and calculated `0/0 = NaN` when displaying the count.

## Prevention
- Add unit tests for crawler functions
- Add integration tests for ESP routes
- Add better error logging in production
- Consider adding request tracing/correlation IDs  
