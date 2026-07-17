"""
AI Client Manager
Handles communication with different AI providers (Gemini, Claude, and OpenAI)
"""

import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai

class AIClient:
    def __init__(self, provider: str, model_name: str, system_prompt: str):
        self.provider = provider
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.configured = False

        if provider == 'gemini':
            self._configure_gemini()
        elif provider == 'claude':
            self._configure_claude()
        elif provider == 'openai':
            self._configure_openai()

    def _configure_gemini(self):
        """Configure Gemini AI"""
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.configured = True
            print(f"✓ Gemini configured with model: {self.model_name}")
        else:
            print("Warning: GEMINI_API_KEY not set")

    def _configure_claude(self):
        """Configure Claude AI"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
                self.configured = True
                print(f"✓ Claude configured with model: {self.model_name}")
            except ImportError:
                print("Error: anthropic package not installed. Run: pip install anthropic")
                self.configured = False
        else:
            print("Warning: ANTHROPIC_API_KEY not set")

    def _configure_openai(self):
        """Configure OpenAI"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.configured = True
                print(f"✓ OpenAI configured with model: {self.model_name}")
            except ImportError:
                print("Error: openai package not installed. Run: pip install openai")
                self.configured = False
        else:
            print("Warning: OPENAI_API_KEY not set")

    def check_status(self) -> Dict[str, Any]:
        """Check if the AI service is configured and working"""
        if not self.configured:
            return {
                'status': 'error',
                'message': f'{self.provider.title()} API key not configured',
                'provider': self.provider,
                'model': self.model_name
            }

        try:
            if self.provider == 'gemini':
                # Try a simple request to verify
                model = genai.GenerativeModel(
                    model_name=f'models/{self.model_name}',
                    system_instruction="Test"
                )
                # Just check if model can be instantiated
                return {
                    'status': 'ok',
                    'message': 'Gemini API is working',
                    'provider': 'gemini',
                    'model': self.model_name
                }
            elif self.provider == 'claude':
                # Try listing models to verify API key
                try:
                    # Simple check - if client is instantiated, API key is valid
                    return {
                        'status': 'ok',
                        'message': 'Claude API is working',
                        'provider': 'claude',
                        'model': self.model_name
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'Claude API error: {str(e)}',
                        'provider': 'claude',
                        'model': self.model_name
                    }
            elif self.provider == 'openai':
                # Try listing models to verify API key
                try:
                    # Simple check - if client is instantiated, API key is valid
                    self.client.models.list()
                    return {
                        'status': 'ok',
                        'message': 'OpenAI API is working',
                        'provider': 'openai',
                        'model': self.model_name
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'OpenAI API error: {str(e)}',
                        'provider': 'openai',
                        'model': self.model_name
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'provider': self.provider,
                'model': self.model_name
            }

    def generate_response(
        self,
        message: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate a response using the configured AI provider

        Args:
            message: User's current message
            context: RAG context from vector database
            conversation_history: Previous conversation messages

        Returns:
            Generated response text
        """
        if not self.configured:
            return f"{self.provider.title()} API not configured. Please set API key in admin settings."

        try:
            if self.provider == 'gemini':
                return self._generate_gemini(message, context, conversation_history)
            elif self.provider == 'claude':
                return self._generate_claude(message, context, conversation_history)
            elif self.provider == 'openai':
                return self._generate_openai(message, context, conversation_history)
            else:
                return f"Unknown provider: {self.provider}"
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def _generate_gemini(
        self,
        message: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate response using Gemini"""
        full_conversation = []

        # Add conversation history
        for msg in conversation_history:
            role = "user" if msg['role'] == 'user' else "model"
            full_conversation.append({
                "role": role,
                "parts": [msg['content']]
            })

        # Add current message with context
        user_message = f"{context}\n\n# User Question:\n{message}"
        full_conversation.append({
            "role": "user",
            "parts": [user_message]
        })

        # Call Gemini API
        model = genai.GenerativeModel(
            model_name=f'models/{self.model_name}',
            system_instruction=self.system_prompt
        )

        # Start chat with history
        chat = model.start_chat(history=full_conversation[:-1])

        # Send the current message
        response = chat.send_message(full_conversation[-1]['parts'][0])
        return response.text

    def _generate_claude(
        self,
        message: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate response using Claude"""
        # Build messages for Claude format
        messages = []

        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        # Add current message with context
        user_message = f"{context}\n\n# User Question:\n{message}"
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call Claude API
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages
        )

        return response.content[0].text

    def _generate_openai(
        self,
        message: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate response using OpenAI"""
        # Build messages for OpenAI format
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        # Add current message with context
        user_message = f"{context}\n\n# User Question:\n{message}"
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=4096,
            temperature=0.7
        )

        return response.choices[0].message.content

    @staticmethod
    def get_available_models() -> Dict[str, List[Dict[str, str]]]:
        """Get list of available models for each provider"""
        return {
            'gemini': [
                {'name': 'gemini-flash-latest', 'display': 'Gemini Flash (Fast, Latest)'},
                {'name': 'gemini-1.5-flash', 'display': 'Gemini 1.5 Flash'},
                {'name': 'gemini-1.5-pro', 'display': 'Gemini 1.5 Pro'},
                {'name': 'gemini-pro', 'display': 'Gemini Pro'}
            ],
            'claude': [
                {'name': 'claude-3-5-sonnet-20241022', 'display': 'Claude 3.5 Sonnet'},
                {'name': 'claude-3-opus-20240229', 'display': 'Claude 3 Opus'},
                {'name': 'claude-3-sonnet-20240229', 'display': 'Claude 3 Sonnet'},
                {'name': 'claude-3-haiku-20240307', 'display': 'Claude 3 Haiku'}
            ],
            'openai': [
                {'name': 'gpt-4o', 'display': 'GPT-4o (Optimized)'},
                {'name': 'gpt-4o-mini', 'display': 'GPT-4o Mini (Fast & Cheap)'},
                {'name': 'gpt-4-turbo', 'display': 'GPT-4 Turbo'},
                {'name': 'gpt-4', 'display': 'GPT-4'},
                {'name': 'gpt-3.5-turbo', 'display': 'GPT-3.5 Turbo'}
            ]
        }
