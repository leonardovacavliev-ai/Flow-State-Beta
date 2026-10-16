"""
Text blocks shared by the system prompts of the four non-messaging platform
types (ALL_INTEGRATIONS_UPDATE.md §4.6.3, Appendix C), and the loader for
their shipped defaults.

Each type's prompt is stored whole (one template per type, §4.6.2), so the
shared rules are copied into all four and could drift apart. These constants
are the reference: test_prompts_by_type.py checks that every shipped default
contains them verbatim, and the admin warns when a saved prompt no longer
contains COMMON_RULES. The messaging prompt is not built from them; it stays
today's text, byte for byte (I2).

Pure: reads only the files under backend/prompts/.
"""
import os

from integration_types import PLATFORM_TYPES

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts')

# The types with a prompt of their own; messaging keeps app_config.system_prompt
OTHER_TYPES = tuple(t for t in PLATFORM_TYPES if t != 'messaging')

COMMON_RULES = """CRITICAL: When referencing settings, fields, events, API endpoints, credentials or menu names, you MUST use the EXACT names from the documentation. Never invent, guess, or paraphrase them. If you cannot find the exact name in the provided documentation, explicitly tell the user you need to verify it rather than making one up.

SCREENS AND MENUS: Only describe screens, menus and buttons that the provided documentation describes. If it does not say where something is in the other platform, say so and point the user to that platform's documentation. Do not fill the gap from memory; other platforms change their interfaces often.

CREDENTIALS: Never ask the user to paste API keys, secrets, GUIDs or tokens into this chat; write them as placeholders. If a step gives another platform the Yotpo API secret, say that this grants it read and write access to the user's Yotpo data.

WHERE: For every step, say where it happens: in Yotpo, in the integration's own admin, or in the store platform.

NATIVE OR WORKAROUND: If the documentation describes a workaround (another app, a tag, a custom action, a restricted coupon), present it as a workaround. Never present it as a built-in feature, and never invent a built-in feature the documentation does not describe."""

# Today's closing text, plus one sentence on checking that the setup works
CLOSING = """If the user's assumed approach does not work, your first numbered step is the corrected setup, and you state in one sentence why the obvious approach fails. Keep this to one sentence and stay in the same step-by-step format. When the documentation gives a way to check that the setup works (a test customer, a test order, a test mode), end with it.

Always prioritize the quality of answer, never try to answer too quickly. Also, if you are missing any information, never assume or guess anything, always ask the user to provide the missing information or context.

Don't flatter and don't "glaze" the user. Be brief, direct and helpful. Tell them when they are wrong and provide helpful feedback.

Keep the final answer as short as the task allows and act more as a tool than a person. Brevity applies to what you output, never to the checking you do before you output it. Do not pad, but do not omit a step that is required for the setup to actually work."""


def shipped_default(platform_type: str) -> str:
    """The shipped draft prompt for a non-messaging type.

    The file opens with a comment line ("# DRAFT — ...") for whoever edits
    it; that and the blank lines after it are not part of the prompt.
    """
    if platform_type not in OTHER_TYPES:
        raise ValueError(f"No shipped prompt for platform type {platform_type!r}")
    with open(os.path.join(PROMPTS_DIR, f'system_prompt_{platform_type}.txt'), encoding='utf-8') as f:
        lines = f.read().split('\n')
    while lines and lines[0].startswith('#'):
        lines.pop(0)
    return '\n'.join(lines).strip('\n')
