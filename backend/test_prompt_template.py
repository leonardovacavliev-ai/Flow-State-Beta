"""Tests for prompt_template.py. Run: python3 backend/test_prompt_template.py (or pytest)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_template import product_warning, render, validate  # noqa: E402

TEMPLATE = (
    "You are an email marketing specialist and a [[product]] specialist at once.\n"
    "Use {{ property_name }} placeholders in templates.\n"
    "[[if loyalty]]REFERRAL PROPERTIES: referrer vs referee.\n[[end]]"
    "[[if reviews]]REVIEW EVENTS: submitted vs published.\n[[end]]"
    "Be brief."
)


def test_prompt_without_tokens_is_unchanged():
    plain = "You are a loyalty retention specialist. Use {{ property_name }}."
    for product in ('loyalty', 'reviews', None):
        assert render(plain, product) == plain


def test_loyalty_fill():
    out = render(TEMPLATE, 'loyalty')
    assert "a Yotpo Loyalty & Referrals specialist" in out
    assert "REFERRAL PROPERTIES" in out and "REVIEW EVENTS" not in out
    assert "{{ property_name }}" in out and "[[" not in out


def test_reviews_fill():
    out = render(TEMPLATE, 'reviews')
    assert "a Yotpo Reviews specialist" in out
    assert "REVIEW EVENTS" in out and "REFERRAL PROPERTIES" not in out


def test_unknown_product_keeps_both_blocks():
    out = render(TEMPLATE, None)
    assert "Yotpo Loyalty & Referrals and Yotpo Reviews" in out
    assert "REFERRAL PROPERTIES" in out and "REVIEW EVENTS" in out


def test_unrecognised_product_value_renders_as_unknown():
    assert render(TEMPLATE, 'ugc') == render(TEMPLATE, None)


def test_tokens_are_case_and_space_insensitive():
    assert render("[[ Product ]] [[IF Reviews]]r[[ END ]]", 'reviews') == "Yotpo Reviews r"


def test_valid_template_has_no_errors():
    assert validate(TEMPLATE) == []


def test_typo_is_rejected():
    errors = validate("a [[prodcut]] specialist")
    assert len(errors) == 1 and "prodcut" in errors[0]


def test_unclosed_block_is_rejected():
    assert any("never closed" in e for e in validate("[[if loyalty]] referral rules"))


def test_stray_end_is_rejected():
    assert any("no [[if" in e for e in validate("text [[end]]"))


def test_unknown_block_product_is_rejected():
    assert any("blocks can only be" in e for e in validate("[[if ugc]]x[[end]]"))


def test_nested_blocks_are_rejected():
    assert any("inside" in e for e in validate("[[if loyalty]][[if reviews]]x[[end]][[end]]"))


def test_non_word_brackets_are_literal_text():
    t = "Arrays look like [[1,2]] and [[ ]]. You are a [[product]] specialist."
    assert validate(t) == []
    assert render(t, 'reviews') == "Arrays look like [[1,2]] and [[ ]]. You are a Yotpo Reviews specialist."


def test_stray_open_brackets_do_not_swallow_the_next_token():
    t = "Use [[ for nested lists. You are a [[product]] specialist."
    assert validate(t) == []
    assert render(t, 'loyalty').endswith("a Yotpo Loyalty & Referrals specialist.")


def test_invalid_template_is_sent_as_written_not_truncated():
    t = "A [[if reviews]] reviews only. The rest of the prompt."
    assert validate(t)
    assert render(t, 'loyalty') == t


def test_multiline_token():
    assert render("[[if\nreviews]]r[[end]]", 'reviews') == "r"


def test_liquid_examples_are_not_placeholders():
    assert validate("Use {{ person.first_name }} and {% if x %}.") == []


def test_prompt_without_product_placeholders_is_warned_about():
    assert product_warning("You are a loyalty retention specialist.")
    assert product_warning("[[if loyalty]]REFERRALS[[end]] only")
    assert product_warning(TEMPLATE) is None
    assert product_warning("[[if reviews]]x[[end]]") is None


if __name__ == '__main__':
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
