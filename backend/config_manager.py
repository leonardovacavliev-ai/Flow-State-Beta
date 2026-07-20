"""
Configuration and Change Management System
Handles AI model configuration, system prompts, and change tracking
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

class ConfigManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.config_file = os.path.join(base_path, 'backend', 'app_config.json')
        self.audit_log_file = os.path.join(base_path, 'backend', 'config_audit_log.json')
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Ensure config and audit log files exist with defaults"""
        if not os.path.exists(self.config_file):
            default_config = {
                'ai_model': {
                    'provider': 'openai',  # 'gemini', 'claude', or 'openai'
                    'model_name': 'gpt-4o',  # or 'gemini-flash-latest' or 'claude-3-5-sonnet-20241022'
                    'api_key_set': bool(os.environ.get('GEMINI_API_KEY')),
                    'claude_api_key_set': bool(os.environ.get('ANTHROPIC_API_KEY')),
                    'openai_api_key_set': bool(os.environ.get('OPENAI_API_KEY'))
                },
                'system_prompt': """You are an email marketing specialist and a loyalty retention specialist at once.

Your goal is to recommend flows and campaigns to setup in the user's ESP using loyalty data.
You will provide helpful feedback on how to create the flow, how to setup the right triggers, filters, audiences and email content, following industry best practices. In the handbook you will find some templates, but you will also help create more unique and outside the box flows and campaigns.

Answer in a step by step manner, and walk through the process and in-platform navigation. Answer like you are talking to a person who knows how to work with the ESP, but isn't super in-depth. Make sure you double check your answers across your knowledgebase.

CRITICAL: When referencing customer properties, field names, or API endpoints, you MUST use the EXACT names from the documentation. Never invent, guess, or paraphrase property names. If you cannot find the exact property name in the provided documentation, explicitly tell the user you need to verify the correct property name rather than making one up.

EMAIL TEMPLATES: When providing email templates, use PLAIN TEXT format with property placeholders clearly marked (e.g., {{ property_name }}). Do NOT provide full HTML/CSS code unless the user explicitly asks for production-ready HTML. Keep templates readable and focused on content structure and property usage. Users will add their own styling in their ESP editor.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Aim to answer as short as possible. Act more as a tool than a person.""",
                'last_updated': datetime.now().isoformat(),
                'updated_by': 'system'
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

        if not os.path.exists(self.audit_log_file):
            with open(self.audit_log_file, 'w') as f:
                json.dump([], f, indent=2)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def update_config(self, updates: Dict[str, Any], user_email: str, change_description: str) -> Dict[str, Any]:
        """
        Update configuration and log the change

        Args:
            updates: Dictionary of configuration updates
            user_email: Email of user making the change
            change_description: Description of what changed

        Returns:
            Updated configuration
        """
        current_config = self.get_config()

        # Create audit log entry with backup
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_email': user_email,
            'description': change_description,
            'backup': {
                'ai_model': current_config.get('ai_model', {}),
                'system_prompt': current_config.get('system_prompt', '')
            },
            'changes': updates
        }

        # Update config
        for key, value in updates.items():
            if key in current_config:
                current_config[key] = value

        current_config['last_updated'] = datetime.now().isoformat()
        current_config['updated_by'] = user_email

        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(current_config, f, indent=2)

        # Append to audit log
        self._add_audit_entry(audit_entry)

        return current_config

    def _add_audit_entry(self, entry: Dict[str, Any]):
        """Add entry to audit log"""
        audit_log = self.get_audit_log()
        audit_log.append(entry)

        with open(self.audit_log_file, 'w') as f:
            json.dump(audit_log, f, indent=2)

    def get_audit_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        with open(self.audit_log_file, 'r') as f:
            log = json.load(f)

        if limit:
            return log[-limit:]
        return log

    def restore_from_backup(self, audit_entry_index: int, user_email: str) -> Dict[str, Any]:
        """
        Restore configuration from a backup in audit log

        Args:
            audit_entry_index: Index of audit entry to restore from (negative for recent)
            user_email: Email of user performing restore

        Returns:
            Restored configuration
        """
        audit_log = self.get_audit_log()

        if not audit_log or abs(audit_entry_index) > len(audit_log):
            raise ValueError("Invalid audit entry index")

        backup_entry = audit_log[audit_entry_index]
        backup = backup_entry['backup']

        # Restore configuration
        updates = {
            'ai_model': backup.get('ai_model', {}),
            'system_prompt': backup.get('system_prompt', '')
        }

        return self.update_config(
            updates,
            user_email,
            f"Restored from backup (change made at {backup_entry['timestamp']})"
        )

    def update_api_key(self, provider: str, api_key: str, user_email: str) -> bool:
        """
        Update API key for a provider
        Persists to .env file and updates current environment
        """
        current_config = self.get_config()

        # Determine environment variable name
        if provider == 'gemini':
            env_var_name = 'GEMINI_API_KEY'
            current_config['ai_model']['api_key_set'] = True
        elif provider == 'claude':
            env_var_name = 'ANTHROPIC_API_KEY'
            current_config['ai_model']['claude_api_key_set'] = True
        elif provider == 'openai':
            env_var_name = 'OPENAI_API_KEY'
            current_config['ai_model']['openai_api_key_set'] = True
        else:
            return False

        # Update current process environment
        os.environ[env_var_name] = api_key

        # Persist to .env file
        self._update_env_file(env_var_name, api_key)

        # Log the change (without storing the actual key)
        self.update_config(
            current_config,
            user_email,
            f"Updated {provider} API key"
        )

        return True

    def _update_env_file(self, key: str, value: str):
        """
        Update or add a key-value pair in .env file
        Creates the file if it doesn't exist
        """
        env_file_path = os.path.join(self.base_path, '.env')

        # Read existing .env file
        env_vars = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        var_name, var_value = line.split('=', 1)
                        env_vars[var_name.strip()] = var_value.strip()

        # Update the key
        env_vars[key] = value

        # Write back to .env file
        with open(env_file_path, 'w') as f:
            f.write("# API Keys - Updated by Admin Panel\n")
            f.write("# SECURITY WARNING: Do not commit this file to version control\n\n")
            for var_name, var_value in env_vars.items():
                f.write(f"{var_name}={var_value}\n")

    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        config = self.get_config()
        return config.get('system_prompt', '')

    def update_system_prompt(self, new_prompt: str, user_email: str) -> str:
        """Update system prompt"""
        self.update_config(
            {'system_prompt': new_prompt},
            user_email,
            "Updated system prompt"
        )
        return new_prompt

    def get_model_config(self) -> Dict[str, Any]:
        """Get current AI model configuration"""
        config = self.get_config()
        return config.get('ai_model', {})

    def update_model_config(self, provider: str, model_name: str, user_email: str) -> Dict[str, Any]:
        """Update AI model configuration"""
        current_config = self.get_config()

        # Update model config
        current_config['ai_model']['provider'] = provider
        current_config['ai_model']['model_name'] = model_name

        self.update_config(
            {'ai_model': current_config['ai_model']},
            user_email,
            f"Changed AI model to {provider}/{model_name}"
        )

        return current_config['ai_model']
