# Quick Guide: Manual Content Paste

## When to Use

Use the "Paste Content" feature when:
- ✅ A link shows **yellow "PENDING"** badge after crawl attempts
- ✅ The URL requires authentication/login
- ✅ The website blocks automated crawlers
- ✅ You have access to the content but the bot doesn't

## 3-Step Process

### 1️⃣ Find the Protected Link

Navigate to **Admin Panel** → **ESP Management**

Look for links with yellow badges:
```
☐ [PENDING] https://protected-site.com/article
    👆 This means the crawler couldn't access it
```

### 2️⃣ Click "Paste Content" Button

Click the **📋 Paste Content** button next to the pending link.

A modal opens with:
- **URL**: (the link you're documenting) - readonly
- **ESP**: (which ESP this is for) - readonly  
- **Content**: (large text area) - paste here ⬅️

### 3️⃣ Copy & Paste the Content

**In a new browser tab:**
1. Open the protected URL
2. Log in if needed
3. Select the article's main content (copy text, not HTML)
4. Return to the modal
5. Paste into the "Content" field
6. Click **"Save & Vectorize"**

**Result:**
- ✅ Status changes from yellow **PENDING** to green **COMPLETED**
- ✅ Content is saved and vectorized
- ✅ AI assistant can now reference this content

## Tips

### ✅ DO:
- Copy the main article text (paragraphs, headings, lists)
- Include section titles and important formatting
- Paste plain text (the content after rendering)
- Check that you got all important sections

### ❌ DON'T:
- Don't paste HTML source code (`<div>`, `<p>` tags)
- Don't include navigation menus or footers
- Don't paste advertising or unrelated content
- Don't worry about perfect formatting (AI will parse it)

## Example Content to Paste

**Good Example:**
```
How to Set Up Loyalty Campaigns in Klaviyo

Step 1: Create a Segment
First, navigate to the Segments page...

Step 2: Configure the Flow
Open the Flow Builder and select...

Best Practices:
- Use clear segment names
- Test before launching
- Monitor engagement metrics
```

**Bad Example (HTML):**
```
<div class="article">
<h1>How to Set Up...</h1>
<nav class="sidebar">...</nav>
<script>analytics.track();</script>
```

## Validation

The system will warn you if:
- ⚠️ Content is less than 100 characters (probably incomplete)
- ❌ Content field is empty (required)

## After Submission

**Success Message:**
```
✅ Content saved successfully!

File: loyalty-setup-guide.txt

The content has been vectorized and is now 
available for the AI assistant.
```

**What Happens:**
1. Content saved to: `docs/{esp_name}/filename.txt`
2. Metadata updated in `crawl_metadata.json`
3. Vector database updated (ChromaDB/Pinecone)
4. Link status changes to "COMPLETED"
5. "Paste Content" button disappears

## Troubleshooting

**Q: I don't see the "Paste Content" button**
- A: Button only appears for links with "PENDING" status (yellow badge)

**Q: The content is too long to paste**
- A: No problem! The textarea supports large amounts of text. If it's exceptionally large (>100KB), consider breaking it into multiple links/articles.

**Q: Can I edit content I already pasted?**
- A: Currently no - but you can delete the link and re-add it with new content. Feature request: content editing.

**Q: Does this work for Global Knowledge links?**
- A: Yes! The same button appears for pending global knowledge links.

**Q: Will this affect auto-crawled content?**
- A: No - if you later successfully crawl the same URL, the system will update with the crawled version.

## Admin Panel Location

```
Main App
  └─ [Admin] button (top-right)
       └─ Enter password: RICHCSM
            └─ ESP Management tab
                 └─ Find pending links
                      └─ Click "📋 Paste Content"
```
