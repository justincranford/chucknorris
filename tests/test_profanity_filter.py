
import pytest
from scraper.profanity_filter import ProfanityFilterType, filter_profanity

# Table of phrases and expected outputs for each filter
TEST_CASES = [
    {
        "text": "You p1ec3 of sHit.",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("You p1ec3 of ****.", True),
            ProfanityFilterType.PROFANITYFILTER: ("You p1ec3 of ****.", True),
            ProfanityFilterType.PROFANE_DETECTOR: ("You p1ec3 of sHit.", False),
        },
    },
    {
        "text": "...sh1t...hello_cat_fuck,,,,123",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("...****...hello_cat_****,,,,123", True),
            ProfanityFilterType.PROFANITYFILTER: ("...****...hello_cat_fuck,,,,123", True),  # 'fuck' not censored
            ProfanityFilterType.PROFANE_DETECTOR: ("...sh1t...hello_cat_fuck,,,,123", False),
        },
    },
    {
        "text": "That l3sbi4n did a very good H4ndjob.",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("That l3sbi4n did a very good ****.", True),
            ProfanityFilterType.PROFANITYFILTER: ("That l3sbi4n did a very good H4ndjob.", False),  # not censored
            ProfanityFilterType.PROFANE_DETECTOR: ("That l3sbi4n did a very good H4ndjob.", False),
        },
    },
    {
        "text": "That's bullshit!",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("That's ****!", True),
            ProfanityFilterType.PROFANITYFILTER: ("That's ********!", True),
            ProfanityFilterType.PROFANE_DETECTOR: ("That's bullshit!", False),
        },
    },
    {
        "text": "That's awesome!",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("That's awesome!", False),
            ProfanityFilterType.PROFANITYFILTER: ("That's awesome!", False),
            ProfanityFilterType.PROFANE_DETECTOR: ("That's awesome!", False),
        },
    },
    {
        "text": "Profane shit is not good",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("Profane **** is not good", True),
            ProfanityFilterType.PROFANITYFILTER: ("Profane **** is not good", True),
            ProfanityFilterType.PROFANE_DETECTOR: ("Profane shit is not good", False),
        },
    },
    {
        "text": "You are a bitch",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("You are a ****", True),
            ProfanityFilterType.PROFANITYFILTER: ("You are a *****", True),  # censored as '*****'
            ProfanityFilterType.PROFANE_DETECTOR: ("You are a bitch", False),
        },
    },
    {
        "text": "You are a nice person",
        "expected": {
            ProfanityFilterType.BETTER_PROFANITY: ("You are a nice person", False),
            ProfanityFilterType.PROFANITYFILTER: ("You are a nice person", False),
            ProfanityFilterType.PROFANE_DETECTOR: ("You are a nice person", False),
        },
    },
]

@pytest.mark.parametrize("filter_type", [
    ProfanityFilterType.BETTER_PROFANITY,
    ProfanityFilterType.PROFANITYFILTER,
    ProfanityFilterType.PROFANE_DETECTOR,
])
@pytest.mark.parametrize("case", TEST_CASES)
def test_filter_profanity_table(case, filter_type):
    text = case["text"]
    expected_censored, expected_is_profane = case["expected"][filter_type]
    censored = filter_profanity(text, filter_type)
    assert censored == expected_censored
    is_profane = censored != text
    assert is_profane == expected_is_profane
