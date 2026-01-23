"""Profanity filtering utility for Chuck Norris Scraper.

Supports three libraries:
  - better-profanity
  - profanityfilter
  - profane-detector
Select via ProfanityFilterType enum.
"""

from enum import Enum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from better_profanity import profanity
    from profanityfilter import ProfanityFilter
    from profane_detector import ProfaneDetector

class ProfanityFilterType(Enum):
    """Enum for selecting profanity filter implementation."""
    BETTER_PROFANITY = "better_profanity"
    PROFANITYFILTER = "profanityfilter"
    PROFANE_DETECTOR = "profane_detector"

def filter_quotes(quotes: List[str], filter_type: ProfanityFilterType) -> List[str]:
    """
    Filter and normalize quotes using the selected profanity filter.

    Args:
        quotes: List of quote strings.
        filter_type: Enum value for filter selection.

    Returns:
        List of filtered/normalized quote strings.
    """
    import logging
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return [q for q in quotes if not profanity.contains_profanity(q)]
        except ImportError:
            logging.warning("better_profanity not installed; skipping profanity filtering.")
            return quotes
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return [q for q in quotes if not profanity.contains_profanity(q)]
        except ImportError:
            logging.warning("better_profanity not installed; skipping profanity filtering.")
            return quotes
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return [q for q in quotes if not pf.is_clean(q)]
        except ImportError:
            logging.warning("profanityfilter not installed; skipping profanity filtering.")
            return quotes
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            # English only for now
            return [q for q in quotes if not detector.detect_api("en", q)]
        except ImportError:
            logging.warning("profane_detector not installed; skipping profanity filtering.")
            return quotes
    # ...existing code...

# Clean retyped function at module level
def filter_profanity(text: str, filter_type: ProfanityFilterType) -> str:
    """
    Censor a single string using the selected profanity filter.

    Args:
        text: Input string to censor.
        filter_type: Enum value for filter selection.

    Returns:
        Censored string (if profane), or original string (if clean).
    """
    import logging
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return profanity.censor(text)
        except ImportError:
            logging.warning("better_profanity not installed; returning original text.")
            return text
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return pf.censor(text)
        except ImportError:
            logging.warning("profanityfilter not installed; returning original text.")
            return text
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            return detector.censor(text)
        except ImportError:
            logging.warning("profane_detector not installed; returning original text.")
            return text
    else:
        raise ValueError(f"Unknown profanity filter type: {filter_type}")
        raise ValueError(f"Unknown profanity filter type: {filter_type}")

def get_filtered_quotes(quotes: List[str], filter_type: ProfanityFilterType) -> List[str]:
    """
    Return quotes detected as profane by the selected filter.

    Args:
        quotes: List of quote strings.
        filter_type: Enum value for filter selection.

    Returns:
        List of quotes detected as profane.
    """
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return [q for q in quotes if profanity.contains_profanity(q)]
        except ImportError:
            return []
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return [q for q in quotes if not pf.is_clean(q)]
        except ImportError:
            return []
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            return [q for q in quotes if detector.detect_api("en", q)]
        except ImportError:
            return []
    else:
        return []
def get_filtered_quotes(quotes: List[str], filter_type: ProfanityFilterType) -> List[str]:
    """Return quotes detected as profane by the selected filter."""
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return [q for q in quotes if profanity.contains_profanity(q)]
        except ImportError:
            return []
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return [q for q in quotes if not pf.is_clean(q)]
        except ImportError:
            return []
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            return [q for q in quotes if detector.detect_api("en", q)]
        except ImportError:
            return []
    else:
        return []
"""Profanity filtering utility for Chuck Norris Scraper.

Supports three libraries:
  - better-profanity
  - profanityfilter
  - profane-detector
Select via ProfanityFilterType enum.
"""

from enum import Enum
from typing import List

class ProfanityFilterType(Enum):
    BETTER_PROFANITY = "better_profanity"
    PROFANITYFILTER = "profanityfilter"
    PROFANE_DETECTOR = "profane_detector"

def filter_quotes(quotes: List[str], filter_type: ProfanityFilterType) -> List[str]:
    """Filter and normalize quotes using the selected profanity filter.

    Args:
        quotes: List of quote strings.
        filter_type: Enum value for filter selection.

    Returns:
        List of filtered/normalized quote strings.
    """
    import logging
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return [q for q in quotes if not profanity.contains_profanity(q)]
        except ImportError:
            logging.warning("better_profanity not installed; skipping profanity filtering.")
            return quotes
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return [q for q in quotes if not pf.is_clean(q)]
        except ImportError:
            logging.warning("profanityfilter not installed; skipping profanity filtering.")
            return quotes
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            # English only for now
            return [q for q in quotes if not detector.detect_api("en", q)]
        except ImportError:
            logging.warning("profane_detector not installed; skipping profanity filtering.")
            return quotes
    else:
        raise ValueError(f"Unknown profanity filter type: {filter_type}")

def filter_profanity(text: str, filter_type: ProfanityFilterType) -> str:
    """
    Censor a single string using the selected profanity filter.

    Args:
        text: Input string to censor.
        filter_type: Enum value for filter selection.

    Returns:
        Censored string (if profane), or original string (if clean).
    """
    import logging
    if filter_type == ProfanityFilterType.BETTER_PROFANITY:
        try:
            from better_profanity import profanity
            profanity.load_censor_words()
            return profanity.censor(text)
        except ImportError:
            logging.warning("better_profanity not installed; returning original text.")
            return text
    elif filter_type == ProfanityFilterType.PROFANITYFILTER:
        try:
            from profanityfilter import ProfanityFilter
            pf = ProfanityFilter()
            return pf.censor(text)
        except ImportError:
            logging.warning("profanityfilter not installed; returning original text.")
            return text
    elif filter_type == ProfanityFilterType.PROFANE_DETECTOR:
        try:
            from profane_detector import ProfaneDetector
            detector = ProfaneDetector()
            return detector.censor(text)
        except ImportError:
            logging.warning("profane_detector not installed; returning original text.")
            return text
    else:
        raise ValueError(f"Unknown profanity filter type: {filter_type}")
