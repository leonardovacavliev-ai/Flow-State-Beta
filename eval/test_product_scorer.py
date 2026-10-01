"""Tests for eval/product_scorer.py. Run: python3 eval/test_product_scorer.py (or pytest)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from product_scorer import Vocabulary, decide, property_tokens, score_answer  # noqa: E402

VOCAB = Vocabulary.from_chunks([
    ('loyalty', "Use {{ person.swell_point_balance }} and swell_vip_tier_name in the email."),
    ('reviews', "Segment on yotpo_review_star_rating or review_count_last_30d."),
    ('shared', "Klaviyo profile properties like first_name and email_consent."),
])


def test_vocabulary_keeps_only_exclusive_properties():
    assert 'swell_vip_tier_name' in VOCAB.exclusive['loyalty']
    assert 'yotpo_review_star_rating' in VOCAB.exclusive['reviews']
    assert 'first_name' not in VOCAB.exclusive['loyalty'] | VOCAB.exclusive['reviews']


def test_template_variables_are_property_tokens():
    assert 'person.swell_point_balance' in property_tokens("Hi {{ person.swell_point_balance }}")


def test_attentive_wrong_console_is_wrong_product():
    answer = "1. In your Yotpo Reviews admin, go to Integrations.\n2. Click Connect on the Attentive tile."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'wrong_product'


def test_right_console_is_correct():
    answer = "From your Yotpo Loyalty admin, go to Integrations Center and connect Attentive."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'correct'


def test_other_products_property_is_wrong_product():
    answer = "Build a segment where yotpo_review_star_rating is at least 4."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'wrong_product'


def test_generic_answer_with_no_product_signal_is_correct():
    answer = "Create a flow triggered by the metric, then add a time delay of 3 days."
    assert score_answer(answer, 'reviews', VOCAB).outcome == 'correct'


def test_both_products_named_is_hedged():
    answer = "In Yotpo Loyalty & Referrals use Integrations Center; in Yotpo Reviews use the Reviews admin."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'hedged'


def test_asking_which_product_is_hedged_for_a_named_question():
    answer = "Are you asking about Yotpo Loyalty or Yotpo Reviews? The steps differ."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'hedged'


def test_declining_is_no_answer_where_docs_exist():
    answer = "I don't have documentation on that for Klaviyo."
    assert score_answer(answer, 'loyalty', VOCAB).outcome == 'no_answer'


def test_guard_working_is_correct_on_uncovered_esp():
    answer = "Flow State has no Yotpo Reviews documentation for Ometria yet, so I can't give setup steps."
    assert score_answer(answer, 'reviews', VOCAB, reviews_coverage=False).outcome == 'correct'


def test_real_decline_phrasings_are_recognised():
    # Taken from the first live run (gemini-flash-latest, coverage note in context)
    for answer in (
        "Flow State does not have documentation for connecting Yotpo Reviews to Emarsys.",
        "I do not have Yotpo Reviews documentation for Postscript, so I cannot provide the steps.",
        "Flow State doesn't have Yotpo Reviews documentation for Emarsys yet.",
    ):
        assert score_answer(answer, 'reviews', VOCAB, reviews_coverage=False).outcome == 'correct', answer


def test_answering_anyway_on_uncovered_esp_is_wrong():
    answer = "In Ometria, create a journey triggered by the review event and add an email."
    assert score_answer(answer, 'reviews', VOCAB, reviews_coverage=False).outcome == 'answered_without_docs'


def test_no_product_question_asking_is_correct():
    answer = "Which Yotpo product do you mean, Loyalty or Reviews? The admin is different for each."
    assert score_answer(answer, None, VOCAB).outcome == 'correct'


def test_no_product_question_picking_one_is_flagged():
    answer = "Open your Yotpo Loyalty admin and go to Integrations Center."
    assert score_answer(answer, None, VOCAB).outcome == 'picked_one'


def test_ungrounded_property_is_flagged():
    s = score_answer("Use swell_made_up_field.", 'loyalty', VOCAB, context="Use swell_vip_tier_name.")
    assert s.ungrounded_properties == ['swell_made_up_field']


def test_decide_low_baseline_ships_labels():
    counts = {'A': {'correct': 19, 'wrong_product': 1}, 'C2': {'correct': 20}}
    assert decide(counts, 20)['ship'] == 'C2'


def test_decide_picks_cheapest_arm_that_halves():
    counts = {'A': {'wrong_product': 8, 'correct': 12},
              'C1': {'wrong_product': 6, 'correct': 14},
              'C2': {'wrong_product': 4, 'correct': 16},
              'D': {'wrong_product': 1, 'correct': 19},
              'B': {'wrong_product': 0, 'correct': 20}}
    assert decide(counts, 20)['ship'] == 'C2'


def test_decide_rejects_an_arm_that_buys_accuracy_with_refusals():
    counts = {'A': {'wrong_product': 8, 'correct': 12},
              'C1': {'wrong_product': 2, 'no_answer': 6, 'correct': 12},
              'D': {'wrong_product': 3, 'correct': 17}}
    assert decide(counts, 20)['ship'] == 'D'


def test_decide_inconclusive_defaults_to_labels():
    counts = {'A': {'wrong_product': 8, 'correct': 12}, 'C2': {'wrong_product': 7, 'correct': 13}}
    result = decide(counts, 20)
    assert result['ship'] == 'C2' and result.get('inconclusive')


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
