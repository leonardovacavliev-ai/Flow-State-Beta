"""
Product placeholders in the system prompt.

The stored system prompt is a template. At request time it is filled for the
Yotpo product the user picked in chat (Loyalty or Reviews), or for "unknown"
when no product is known (an old client, an eval arm that withholds it).

    [[product]]                 Yotpo Loyalty & Referrals | Yotpo Reviews |
                                Yotpo Loyalty & Referrals and Yotpo Reviews
    [[if loyalty]] ... [[end]]  kept for Loyalty and for unknown
    [[if reviews]] ... [[end]]  kept for Reviews and for unknown

Square brackets, not braces: the prompt already contains Liquid-style
examples like {{ property_name }} and those must reach the model untouched.
A prompt with no [[...]] tokens renders to itself, byte for byte. Brackets
that don't hold a word, such as [[1,2]], are ordinary text.

validate() runs when an admin saves or restores the prompt, so a typo such
as [[prodcut]] or an unclosed block is rejected instead of reaching the
model. render() refuses to interpret a template that fails validation and
sends it as written: better the model sees a stray [[...]] than loses the
part of the prompt an unclosed block would have hidden.
"""
import re
from typing import List, Optional

PRODUCT_NAMES = {
    'loyalty': 'Yotpo Loyalty & Referrals',
    'reviews': 'Yotpo Reviews',
    None: 'Yotpo Loyalty & Referrals and Yotpo Reviews',
}
BLOCK_PRODUCTS = ('loyalty', 'reviews')

# No brackets inside a token, so a stray "[[" can't swallow the next real one.
_TOKEN = re.compile(r"\[\[([^\[\]]*)\]\]")
# Only word-like contents are placeholders; anything else is literal text.
_WORDY = re.compile(r"^\s*[A-Za-z][\w\s]*$")
_IF = re.compile(r"if\s+(\w+)$", re.I)


def _tokens(template: str):
    for m in _TOKEN.finditer(template):
        if _WORDY.match(m.group(1)):
            yield m, ' '.join(m.group(1).split()).lower()


def validate(template: str) -> List[str]:
    """Problems with the template's placeholders; empty when it is fine."""
    errors = []
    open_block = None
    for m, token in _tokens(template):
        where = f"at character {m.start() + 1}"
        if token == 'product':
            continue
        if token == 'end':
            if open_block is None:
                errors.append(f"[[end]] {where} has no [[if ...]] before it.")
            open_block = None
            continue
        cond = _IF.match(token)
        if cond:
            product = cond.group(1)
            if product not in BLOCK_PRODUCTS:
                errors.append(f"[[{m.group(1).strip()}]] {where}: blocks can only be "
                              f"[[if loyalty]] or [[if reviews]].")
            elif open_block is not None:
                errors.append(f"[[if {product}]] {where} starts inside [[if {open_block}]]; "
                              "close it with [[end]] first.")
            open_block = product
            continue
        errors.append(f"Unknown placeholder [[{m.group(1).strip()}]] {where}. "
                      "Use [[product]], [[if loyalty]], [[if reviews]] or [[end]].")
    if open_block is not None:
        errors.append(f"[[if {open_block}]] is never closed with [[end]].")
    return errors


_warned = set()


def _warn_invalid(template: str, errors: List[str]):
    key = hash(template)
    if key not in _warned:        # once per template, not once per request
        _warned.add(key)
        print(f"[PROMPT] Stored prompt has placeholder problems; sending it as written: {' '.join(errors)}")


def render(template: str, product: Optional[str]) -> str:
    """Fill the template for one product, or for both when product is None.

    An invalid template is returned as written (see the module docstring).
    """
    if '[[' not in template:
        return template
    errors = validate(template)
    if errors:
        _warn_invalid(template, errors)
        return template
    if product not in (None, *BLOCK_PRODUCTS):
        product = None
    out, pos, keep = [], 0, True
    for m, token in _tokens(template):
        if keep:
            out.append(template[pos:m.start()])
        pos = m.end()
        if token == 'product':
            if keep:
                out.append(PRODUCT_NAMES[product])
        elif token == 'end':
            keep = True
        else:
            cond = _IF.match(token)
            if cond and cond.group(1) in BLOCK_PRODUCTS:
                keep = product is None or product == cond.group(1)
            elif keep:
                out.append(m.group(0))
    if keep:
        out.append(template[pos:])
    return ''.join(out)
