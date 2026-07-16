# Crawler Limitations & Known Issues

## Help Center URLs Cannot Be Crawled (Cloudflare Protection)

### Attentive Help Center

**URL**: `https://help.attentivemobile.com/hc/en-us/articles/41480509454740-Yotpo-Loyalty-Referrals#h_01K5T1K8JKGD6GK6H9E1XA868S`

**Status**: ✅ Manually added (content provided by user)

### Ometria Support Center

**URLs**: All 3 pending URLs are blocked:
1. `https://support.ometria.com/hc/en-gb/articles/4800701859997-Setting-up-Yotpo-Loyalty-Referrals`
2. `https://support.ometria.com/hc/en-gb/articles/30378613995933-Yotpo-Loyalty-Referrals-Supported-events`
3. `https://support.ometria.com/hc/en-gb/articles/360015855818-How-entry-triggers-work`

**Status**: ⚠️ Cannot be crawled automatically

**Issue**: Returns "Successfully crawled 0 links"

**Root Cause**: Cloudflare Bot Protection
- The Attentive help center uses Cloudflare's anti-bot protection
- Returns a "Just a moment..." challenge page instead of content
- HTTP Status: 403 Forbidden
- The crawler cannot bypass this protection

**Why This Happens**:
Cloudflare detects automated requests and challenges them with JavaScript-based verification. Our simple crawler cannot:
- Execute JavaScript
- Pass CAPTCHA challenges
- Maintain browser fingerprints
- Handle Cloudflare's TurnStyle protection

## Recommendations

### Option 1: Remove the URL (Recommended)
Since the URL cannot be crawled automatically, remove it from the CSV to avoid confusion:
1. Go to Admin Panel → ESP Management → Attentive
2. Select the pending `help.attentivemobile.com` URL
3. Click "Delete Selected"

### Option 2: Manual Content Addition
If this content is critical:

1. **Manually visit the URL** in your browser
2. **Copy the article content**
3. **Create a text file** in `docs/attentive/`
   - Filename: `articles_41480509454740-Yotpo-Loyalty-Referrals.txt`
   - Format:
     ```
     Source URL: https://help.attentivemobile.com/hc/en-us/articles/41480509454740-Yotpo-Loyalty-Referrals#h_01K5T1K8JKGD6GK6H9E1XA868S

     [paste article content here]
     ```

4. **Update metadata** in `docs/crawl_metadata.json`:
   ```json
   "attentive": [
     ...existing entries...,
     {
       "url": "https://help.attentivemobile.com/hc/en-us/articles/41480509454740-Yotpo-Loyalty-Referrals#h_01K5T1K8JKGD6GK6H9E1XA868S",
       "filename": "articles_41480509454740-Yotpo-Loyalty-Referrals.txt",
       "filepath": "/Users/leonardo.vacavliev/Downloads/AI ESP Loyalty Helper APP/docs/attentive/articles_41480509454740-Yotpo-Loyalty-Referrals.txt"
     }
   ]
   ```

5. **Refresh vector database**:
   ```bash
   cd backend
   python3 << 'EOF'
   from vectorize import DocumentVectorizer
   import os
   BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   DB_PATH = os.path.join(BASE_PATH, "backend/chroma_db")
   DOCS_PATH = os.path.join(BASE_PATH, "docs")
   vectorizer = DocumentVectorizer(persist_directory=DB_PATH)
   
   # Delete old attentive entries
   old = vectorizer.collection.get(where={"esp": "attentive"})
   if old['ids']:
       vectorizer.collection.delete(ids=old['ids'])
   
   # Re-add with new file
   vectorizer.refresh_esp('attentive', DOCS_PATH)
   print(f"Attentive re-indexed: {vectorizer.collection.count()} total chunks")
   EOF
   ```

### Option 3: Leave as Pending
- Keep the URL in the CSV as a reference
- Accept that it shows as "pending" 
- The existing 2 Yotpo support docs provide Attentive integration guidance

## Other Sites That May Have Bot Protection

Common help centers with Cloudflare/bot protection:
- ❌ `help.attentivemobile.com` (confirmed - Cloudflare)
- ❌ `support.ometria.com` (confirmed - Cloudflare)
- ❌ Some Zendesk instances (varies by configuration)
- ✅ `support.yotpo.com` (works fine)
- ✅ `loyaltyapi.yotpo.com` (works fine)
- ✅ `help.klaviyo.com` (works fine)
- ✅ `marketing.help.dotdigital.com` (works fine)

## General Crawler Limitations

The current crawler:
- ✅ Can crawl: Standard websites, help centers without protection
- ✅ Follows redirects
- ✅ Removes navigation/footer/scripts
- ✅ Extracts main content
- ❌ Cannot: Execute JavaScript
- ❌ Cannot: Bypass Cloudflare/bot challenges
- ❌ Cannot: Handle CAPTCHAs
- ❌ Cannot: Crawl authenticated content
- ❌ Cannot: Crawl rate-limited APIs

## Best Practices

1. **Test URLs first**: Before adding many URLs from a new domain, add one and test crawling
2. **Check for bot protection**: If you see "Successfully crawled 0 links", the site likely has protection
3. **Use official documentation**: Prefer vendor documentation sites over third-party help centers
4. **Manual fallback**: For critical protected content, use manual content addition (Option 2 above)

---

**Date**: January 16, 2025  
**Status**: Documented known limitation
