"""
Property validation module to reduce hallucination when citing ESP properties.
Extracts property names from docs and validates AI responses.
"""

import re
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class PropertyValidator:
    def __init__(self, vector_adapter):
        """
        Initialize validator with vector database access.

        Args:
            vector_adapter: VectorAdapter instance for document access
        """
        self.vector_adapter = vector_adapter
        self.property_cache = {}  # Cache: {esp_name: set(property_names)}

    def extract_properties_from_docs(self, esp: str) -> Set[str]:
        """
        Extract all property names from ESP documentation.

        Looks for patterns like:
        - customer.first_name
        - {{ customer_email }}
        - [customer_tags]
        - %customer.loyalty_points%

        Args:
            esp: ESP name

        Returns:
            Set of property names found in docs
        """
        if esp in self.property_cache:
            return self.property_cache[esp]

        try:
            # Fetch all docs for ESP
            results = self.vector_adapter.search("properties variables data fields", esp_filter=esp, n_results=50)

            properties = set()
            if results['documents'] and results['documents'][0]:
                for doc in results['documents'][0]:
                    # Pattern 1: Liquid-style {{ variable }}
                    properties.update(re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}', doc))

                    # Pattern 2: Dot notation object.property
                    properties.update(re.findall(r'\b([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*)\b', doc))

                    # Pattern 3: Jinja-style {% variable %}
                    properties.update(re.findall(r'\{%\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*%\}', doc))

                    # Pattern 4: Percent-style %variable%
                    properties.update(re.findall(r'%([a-zA-Z_][a-zA-Z0-9_.]*)%', doc))

            # Filter out common false positives
            filtered = {
                p for p in properties
                if len(p) > 2 and not p.startswith('http') and '.' in p or '_' in p
            }

            self.property_cache[esp] = filtered
            logger.info(f"Extracted {len(filtered)} properties for {esp}")
            return filtered

        except Exception as e:
            logger.error(f"Failed to extract properties for {esp}: {e}")
            return set()

    def get_relevant_properties(self, query: str, esp: str, top_k: int = 10) -> List[str]:
        """
        Find properties most relevant to user query.

        Args:
            query: User query
            esp: ESP name
            top_k: Number of properties to return

        Returns:
            List of relevant property names
        """
        all_properties = self.extract_properties_from_docs(esp)

        # Simple relevance: check if property name appears in query or semantically related
        query_lower = query.lower()
        scored = []

        for prop in all_properties:
            score = 0
            prop_lower = prop.lower()

            # Exact match in query
            if prop_lower in query_lower:
                score += 10

            # Partial match (e.g., "email" in "customer.email")
            for word in query_lower.split():
                if word in prop_lower or prop_lower in word:
                    score += 5

            # Semantic hints (e.g., query mentions "name" → boost first_name, last_name)
            semantic_map = {
                'name': ['name', 'first', 'last', 'full'],
                'email': ['email', 'mail', 'contact'],
                'points': ['points', 'loyalty', 'rewards', 'balance'],
                'referral': ['referral', 'refer', 'advocate'],
                'tier': ['tier', 'level', 'vip', 'status'],
                'birthday': ['birthday', 'birth', 'dob']
            }

            for keyword, hints in semantic_map.items():
                if keyword in query_lower:
                    if any(hint in prop_lower for hint in hints):
                        score += 3

            if score > 0:
                scored.append((prop, score))

        # Sort by score and return top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [prop for prop, _ in scored[:top_k]]

    def validate_response(self, response: str, esp: str) -> Dict:
        """
        Validate AI response for cited properties.

        Args:
            response: AI-generated response
            esp: ESP name

        Returns:
            Dict with validation results and warnings
        """
        # Extract properties mentioned in response
        mentioned = set()
        mentioned.update(re.findall(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}', response))
        mentioned.update(re.findall(r'\b([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*)\b', response))

        # Get known properties
        known = self.extract_properties_from_docs(esp)

        # Find potentially hallucinated properties
        unknown = mentioned - known

        warnings = []
        if unknown:
            warnings.append(f"⚠️ Unverified properties cited: {', '.join(unknown)}")
            warnings.append("These properties were not found in documentation. Verify before using.")

        return {
            'mentioned_properties': list(mentioned),
            'known_properties': list(known),
            'unknown_properties': list(unknown),
            'warnings': warnings,
            'validation_passed': len(unknown) == 0
        }


# Singleton instance
_validator_instance = None

def get_property_validator(vector_adapter):
    """Get or create property validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PropertyValidator(vector_adapter)
    return _validator_instance
