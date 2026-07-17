# Gemini API 401 Error - Quick Fix Guide

## The Error You're Seeing

```
401 Request had invalid authentication credentials. 
ACCESS_TOKEN_TYPE_UNSUPPORTED
```

## Root Cause

This error happens when there's a **version mismatch** in the Google Generative AI library, OR when the API key type doesn't match the authentication method.

## Quick Fixes (Try in Order)

### Fix 1: Update Model Name ✅ ALREADY DONE

Changed `gemini-flash-latest` → `gemini-1.5-flash` in [backend/app_config.json](backend/app_config.json)

### Fix 2: Update Google Generative AI Package

**In Railway:**

1. Go to your Railway project
2. Click on your service
3. Go to **"Settings"** tab
4. Scroll to **"Environment Variables"**
5. Click **"+ New Variable"**
6. Add:
   - **Variable name**: `GOOGLE_GENERATIVEAI_VERSION`
   - **Value**: `0.8.3`
7. Click **"Deploy"**

This forces Railway to use the correct package version.

### Fix 3: Verify API Key Type

Your API key might be for **Vertex AI** instead of **Google AI Studio**.

**Check which type you have:**

1. Go to https://aistudio.google.com/app/apikey
2. Look at your API key format:
   - ✅ **Correct**: Starts with `AIza...` (40 characters)
   - ❌ **Wrong**: JSON file or different format

**If your key is wrong type:**

1. Go to https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Choose **"Create API key in new project"**
4. Copy the key (starts with `AIza...`)
5. In Railway → Variables → Update `GEMINI_API_KEY`
6. Deploy

### Fix 4: Add Region Configuration

Sometimes the API needs an explicit region set.

**In Railway → Variables → Add:**
- Variable: `GOOGLE_API_REGION`
- Value: `us-central1`

### Fix 5: Switch to Claude (Temporary Workaround)

While we debug Gemini, you can use Claude instead:

**In Railway → Variables → Add:**
- Variable: `ANTHROPIC_API_KEY`
- Value: Your Claude API key (get from https://console.anthropic.com/)

**Then in your app:**
1. Go to Admin Panel → General Settings
2. Change "Model Provider" from "Gemini" to "Claude"
3. Select "Claude 3.5 Sonnet"
4. Save

## Testing After Each Fix

1. Make the change in Railway
2. Wait for deployment to complete (~2 minutes)
3. Go to your app URL
4. Select an ESP (e.g., "Klaviyo")
5. Type a test message: "test"
6. Check if you get a response (not an error)

## Most Likely Solution

Based on your error, it's **Fix 3** (wrong API key type). The `ACCESS_TOKEN_TYPE_UNSUPPORTED` error specifically means the authentication token format doesn't match what the API expects.

**Next step**: Can you check your Railway Variables and tell me:
1. Does `GEMINI_API_KEY` start with `AIza`?
2. Is it about 39-40 characters long?

If not, create a new API key from Google AI Studio and replace it.
