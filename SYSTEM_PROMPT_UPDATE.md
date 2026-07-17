# System Prompt Update Guide

## What Changed

**Key Addition**: Added "and in-platform navigation" to guide users through actual ESP UI steps, not just conceptual workflows.

**Old**:
> Answer in a step by step manner, and walk through the process.

**New**:
> Answer in a step by step manner, and walk through the process and in-platform navigation.

## Deploy to Production

### Option 1: Via Railway Dashboard (Recommended)

1. Push to GitHub (already done)
2. Railway auto-deploys from GitHub
3. SSH into Railway container:
   ```bash
   railway shell
   python3 update_system_prompt.py
   exit
   ```

### Option 2: Via API (Remote)

```bash
chmod +x update_production_prompt.sh
./update_production_prompt.sh https://your-railway-url.up.railway.app
```

### Option 3: Local Update (Dev)

```bash
python3 update_system_prompt.py
```

## Verify Update

1. Open admin panel: `https://your-app-url/admin`
2. Password: `RICHCSM`
3. Navigate to **Settings → AI Model & System Prompt**
4. Confirm prompt includes: `"and in-platform navigation"`

## Testing

Ask the assistant:
> "How do I set up a welcome campaign in Klaviyo?"

Expected behavior:
- Should provide specific UI navigation steps (e.g., "Go to Campaigns → Create Campaign")
- Should use exact property names from docs (e.g., `loyalty_nt_points`)
- Should NOT invent/paraphrase property names

## Files Modified

- `backend/app_config.json` - Updated system prompt (gitignored, local only)
- `update_system_prompt.py` - Python script to update config
- `update_production_prompt.sh` - Bash script to update via API

## Rollback

If needed, restore previous prompt via admin UI or run:

```python
import json
config_path = "backend/app_config.json"
config = json.load(open(config_path))
config['system_prompt'] = """<paste old prompt here>"""
json.dump(config, open(config_path, 'w'), indent=4)
```
