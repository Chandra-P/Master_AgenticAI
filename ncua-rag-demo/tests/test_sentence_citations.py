import pytest
from pipeline.graph import validate_answer

EVIDENCE = [{'id': 'E1', 'text': '2025: 100 USD'}]


def test_citation_after_sentence_punctuation_supports_that_sentence():
    answer = 'Assets were 100 USD in 2025. [E1]'
    assert validate_answer(answer, EVIDENCE) == answer


def test_trailing_citation_does_not_support_the_next_numeric_sentence():
    with pytest.raises(ValueError, match='own source citation'):
        validate_answer('Assets were 100 USD in 2025. [E1] Loans were 100 USD.', EVIDENCE)


def test_trailing_citation_still_rejects_invented_numbers():
    with pytest.raises(ValueError, match='absent'):
        validate_answer('Assets were 999 USD in 2025. [E1]', EVIDENCE)
