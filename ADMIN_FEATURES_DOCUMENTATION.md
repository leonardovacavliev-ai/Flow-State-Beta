# Admin Features Documentation

## Overview
This document describes the new administrative features added to the AI ESP Loyalty Helper app. These features provide comprehensive control over the AI model configuration, knowledge sources, and change tracking.

## Features Added

### 1. General Settings Tab
A new admin tab that provides centralized control over AI configuration and system behavior.

#### 1.1 AI Model Configuration
- **Location**: Admin Panel → General Settings → AI Model Configuration
- **Purpose**: Switch between different AI providers and models
- **Supported Providers**:
  - Google Gemini (gemini-flash-latest, gemini-1.5-flash, gemini-1.5-pro, gemini-pro)
  - Anthropic Claude (claude-3-5-sonnet, claude-3-opus, claude-3-sonnet, claude-3-haiku)

**Features**:
- View current AI provider and model
- Check API status (working/error)
- Switch between providers and models
- Changes apply immediately to all users

**How to Use**:
1. Navigate to Admin Panel → General Settings
2. Select desired AI provider from dropdown
3. Select model from available options
4. Enter your email address (for audit trail)
5. Click "Update AI Model"
6. Confirm the change

#### 1.2 API Key Management
- **Location**: Admin Panel → General Settings → API Key Management
- **Purpose**: Update API keys for AI providers without restarting the server

**Features**:
- Update Gemini API key (GEMINI_API_KEY)
- Update Claude API key (ANTHROPIC_API_KEY)
- Secure input (password field)
- Immediate effect on current provider

**How to Use**:
1. Select provider (Gemini or Claude)
2. Enter new API key
3. Enter your email address (for audit trail)
4. Click "Update API Key"
5. Confirm the change

**Note**: API keys are stored in environment variables and logged changes don't expose the actual keys.

#### 1.3 System Prompt Configuration
- **Location**: Admin Panel → General Settings → System Prompt
- **Purpose**: Customize the AI assistant's behavior, tone, and personality

**Features**:
- Edit the system prompt in a text area
- View current prompt
- Changes apply immediately to new conversations
- Full backup of previous prompts in audit log

**How to Use**:
1. Edit the system prompt text
2. Enter your email address (for audit trail)
3. Click "Update System Prompt"
4. Confirm the change

#### 1.4 Change History / Audit Log
- **Location**: Admin Panel → General Settings → Change History
- **Purpose**: Track all configuration changes and restore from backups

**Features**:
- View last 20 configuration changes
- See who made each change and when
- View backup details for each change
- One-click restore from any backup
- Automatic backup of old values before any change

**Logged Changes**:
- AI model provider/model changes
- API key updates (without exposing the key)
- System prompt modifications
- Configuration restorations

**How to Use (Restore)**:
1. Click "Restore" button on any change entry
2. Enter your email address
3. Confirm restoration
4. Configuration is restored to that point in time

**Backup Storage**: All backups are stored in `backend/config_audit_log.json`

### 2. Global Knowledge Base
A new section in ESP Management for managing global knowledge sources.

#### 2.1 Global Knowledge Sources
- **Location**: Admin Panel → ESP Management → Global Knowledge Base
- **Purpose**: Manage knowledge that applies across all ESPs (loyalty best practices, general email marketing, etc.)

**Features**:
- Add global knowledge URLs
- View crawl status (pending/crawled)
- Crawl selected links
- Delete selected links
- Integrates with existing bulk actions (checkboxes work with ESP links)

**How to Use**:
1. Add URL in the "Add new global knowledge URL" field
2. Click "Add Link"
3. Link appears with "pending" status
4. Check the box and use "Crawl Selected" button
5. Once crawled, global knowledge is available in all chat sessions

**RAG Integration**: Global knowledge is automatically searched alongside ESP-specific documentation:
- 3 results from ESP-specific docs
- 2 results from global knowledge
- Combined context sent to AI for better responses

### 3. Configuration Management System

#### 3.1 Config Manager (`backend/config_manager.py`)
Central configuration management with change tracking.

**Storage Files**:
- `backend/app_config.json`: Current configuration
- `backend/config_audit_log.json`: Change history with backups

**Configuration Structure**:
```json
{
  "ai_model": {
    "provider": "gemini",
    "model_name": "gemini-flash-latest",
    "api_key_set": true,
    "claude_api_key_set": false
  },
  "system_prompt": "...",
  "last_updated": "2026-07-16T...",
  "updated_by": "user@example.com"
}
```

#### 3.2 AI Client Manager (`backend/ai_client.py`)
Unified interface for multiple AI providers.

**Features**:
- Single interface for Gemini and Claude
- Automatic provider switching
- Status checking
- Error handling
- Conversation history management

### 4. API Endpoints Added

#### General Settings Endpoints
- `GET /api/admin/settings/ai-model` - Get current AI model configuration
- `POST /api/admin/settings/ai-model` - Update AI model
- `POST /api/admin/settings/api-key` - Update API key
- `GET /api/admin/settings/api-status` - Check API status
- `GET /api/admin/settings/system-prompt` - Get system prompt
- `POST /api/admin/settings/system-prompt` - Update system prompt
- `GET /api/admin/settings/audit-log` - Get change history
- `POST /api/admin/settings/restore` - Restore from backup

#### Global Knowledge Endpoints
- `GET /api/admin/global-knowledge/links` - Get global knowledge links
- `POST /api/admin/global-knowledge/add-link` - Add new global link
- `POST /api/admin/global-knowledge/crawl-selected` - Crawl selected global links
- `POST /api/admin/global-knowledge/delete-links` - Delete global links

## Security Features

### 1. Admin Password Protection
All administrative endpoints require valid admin password (RICHCSM).

### 2. Email-Based Audit Trail
Every configuration change requires:
- Admin password
- User email address
- Confirmation dialog

This ensures accountability and traceability.

### 3. Automatic Backups
Before any change is applied:
- Current configuration is backed up
- Backup includes both AI model config and system prompt
- Stored in audit log for easy restoration

### 4. User Notifications
- All changes show confirmation dialogs
- Warning about immediate effect on all users
- Success/error messages for all operations

## Data Recovery

### If Something Goes Wrong

#### Scenario 1: Wrong AI Model Selected
1. Go to Admin Panel → General Settings
2. View Change History
3. Find the last working configuration
4. Click "Restore" on that entry
5. System reverts to previous model

#### Scenario 2: API Key Not Working
1. Go to Admin Panel → General Settings → API Key Management
2. Update the API key
3. Check API Status to verify it's working
4. If needed, restore from Change History

#### Scenario 3: System Prompt Broken
1. Go to Admin Panel → General Settings → Change History
2. Click on any previous change to view backup
3. Click "Restore" to revert to that prompt
4. Alternatively, manually edit the system prompt back

#### Scenario 4: Complete System Failure
Manual recovery:
1. Locate `backend/app_config.json`
2. View `backend/config_audit_log.json` for backups
3. Copy a working configuration from audit log
4. Paste into `app_config.json`
5. Restart the backend server

## File Locations

### Configuration Files
- `backend/app_config.json` - Current app configuration
- `backend/config_audit_log.json` - Change history with backups
- `backend/config_manager.py` - Configuration management system
- `backend/ai_client.py` - AI provider interface

### Knowledge Base
- `docs/global/` - Global knowledge documents
- `docs/[esp_name]/` - ESP-specific documents
- `docs/crawl_metadata.json` - Crawl metadata for all sources

### Frontend
- `frontend/index.html` - UI for new features
- `frontend/app.js` - JavaScript for General Settings and Global Knowledge

## Usage Tips

### Best Practices
1. **Always enter your email** when making changes
2. **Test API keys** using the status check before updating
3. **Review Change History** regularly to track modifications
4. **Backup important prompts** externally before major changes
5. **Use Global Knowledge** for content that applies across all ESPs

### Common Workflows

#### Switching from Gemini to Claude
1. Get Claude API key from Anthropic
2. Update API key in General Settings
3. Check API status to verify
4. Switch model to Claude in AI Model Configuration
5. Test in chat interface

#### Adding New Global Knowledge
1. Find authoritative source (loyalty best practices, email marketing guides)
2. Add URL to Global Knowledge section
3. Check the box for the new URL
4. Click "Crawl Selected"
5. Knowledge is immediately available in all chats

#### Regular Maintenance
1. Review Change History weekly
2. Check API Status regularly
3. Update system prompt based on user feedback
4. Add new global knowledge sources as needed
5. Clean up old/outdated links

## Troubleshooting

### Issue: API Status shows "Error"
**Solution**:
1. Check if API key is set correctly
2. Verify API key is valid in provider dashboard
3. Check if environment variables are set (for server restarts)
4. Try updating the API key again

### Issue: Changes not taking effect
**Solution**:
1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+F5)
2. Check browser console for errors
3. Verify admin password was correct
4. Check network tab for failed requests

### Issue: Can't restore from backup
**Solution**:
1. Verify you have admin password
2. Check if audit log file exists (`backend/config_audit_log.json`)
3. Try manual restoration from JSON file
4. Contact technical support if file is corrupted

### Issue: Global Knowledge not appearing in search
**Solution**:
1. Verify links were crawled successfully
2. Check `docs/global/` folder for .txt files
3. Check `docs/crawl_metadata.json` for 'global' entries
4. Re-crawl the links if needed
5. Check backend logs for vectorization errors

## Technical Details

### Configuration Schema
```json
{
  "ai_model": {
    "provider": "gemini|claude",
    "model_name": "string",
    "api_key_set": boolean,
    "claude_api_key_set": boolean
  },
  "system_prompt": "string",
  "last_updated": "ISO8601 timestamp",
  "updated_by": "email@example.com"
}
```

### Audit Log Entry Schema
```json
{
  "timestamp": "ISO8601 timestamp",
  "user_email": "email@example.com",
  "description": "string",
  "backup": {
    "ai_model": { /* previous config */ },
    "system_prompt": "previous prompt"
  },
  "changes": { /* what was changed */ }
}
```

### RAG Search Strategy
1. User sends message
2. Search ESP-specific docs (3 results)
3. Search global knowledge (2 results)
4. Combine contexts
5. Send to AI with full context
6. Return response with sources

## Support

For issues or questions:
1. Check this documentation first
2. Review Change History for recent modifications
3. Check backend logs (`python backend/app.py`)
4. Restore from a known good configuration
5. Contact the development team

---

**Last Updated**: 2026-07-16
**Version**: 1.0
**Author**: Development Team
