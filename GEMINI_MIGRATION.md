# Gemini API Migration - Complete ✅

## What Changed

The app now uses **Google Gemini API** instead of Anthropic Claude API.

### Why Gemini?

- **Free tier available**: 15 requests per minute, 1 million tokens per day
- **Much cheaper**: Even on paid tier, significantly lower cost than Claude
- **Great performance**: Gemini 1.5 Flash is fast and capable
- **Easy access**: No waitlist, instant API key

## Migration Details

### Model Used
- **Gemini 1.5 Flash** - Fast, efficient, great for chat applications
- Supports conversation history
- Handles long context windows
- System instructions for personality/behavior

### Code Changes

**Before (Claude):**
```python
import anthropic
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    system=SYSTEM_PROMPT,
    messages=messages
)
```

**After (Gemini):**
```python
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)
chat = model.start_chat(history=conversation_history)
response = chat.send_message(message)
```

## How to Get Your Gemini API Key

1. **Go to**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Copy the key** (starts with `AI...`)
5. **Set it**:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```

## Updated Setup Instructions

```bash
# 1. Install new dependency
pip3 install google-generativeai

# 2. Set your Gemini API key
export GEMINI_API_KEY="your-gemini-api-key"

# 3. Start the app
./start.sh

# 4. Open browser
open http://localhost:8000
```

## Features Maintained

✅ RAG-powered chat with vectorized documentation  
✅ Conversation history support  
✅ ESP-specific filtering  
✅ System prompt personality  
✅ Source citations  
✅ All admin features  
✅ Feedback system  

## Cost Comparison

### Gemini (New)
- **Free tier**: 15 RPM, 1M tokens/day
- **Paid**: ~$0.35 per 1M input tokens, ~$1.05 per 1M output tokens
- **Your usage**: Likely stays in free tier

### Claude (Old)
- **No free tier**
- **Cost**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Your usage**: Would cost money immediately

### Estimated Savings
For typical usage (100 conversations/day):
- **With Claude**: ~$5-10/month
- **With Gemini**: $0 (free tier) or ~$0.50/month (paid)

## Testing

Run the verification script:
```bash
python3 test_setup.py
```

Should show:
```
✓ google-generativeai
✓ GEMINI_API_KEY is set
```

## Troubleshooting

**Q: "GEMINI_API_KEY not set"**  
A: Run `export GEMINI_API_KEY="your-key"` before starting the app

**Q: "API key invalid"**  
A: Get a new key at https://makersuite.google.com/app/apikey

**Q: "Rate limit exceeded"**  
A: Free tier: 15 requests/min. Wait a moment or upgrade to paid tier.

**Q: "Response quality different?"**  
A: Gemini 1.5 Flash is optimized for speed. For higher quality, we can switch to Gemini 1.5 Pro (costs more but still cheaper than Claude).

## Rollback (If Needed)

If you need to switch back to Claude:
1. Restore `anthropic` imports in `backend/app.py`
2. Set `ANTHROPIC_API_KEY` instead
3. The old code is preserved in git history

---

**Status**: ✅ Migration complete and tested  
**Model**: Gemini 1.5 Flash  
**Cost**: Free tier available  
**Performance**: Excellent for this use case
