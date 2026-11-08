import pytest

from phishpipe.urls import PlaceholderConflictError, mask_urls, unmask_urls


def test_two_urls_in_order():
    text = "Go to http://example.com/a and https://example.org/b now."
    masked, urls = mask_urls(text)
    assert masked == "Go to {{URL_1}} and {{URL_2}} now."
    assert urls == ["http://example.com/a", "https://example.org/b"]


def test_repeated_url_gets_own_placeholders():
    masked, urls = mask_urls("http://example.com/x and http://example.com/x")
    assert masked == "{{URL_1}} and {{URL_2}}"
    assert urls == ["http://example.com/x", "http://example.com/x"]


def test_www_url():
    masked, urls = mask_urls("Visit www.example.com/login today")
    assert masked == "Visit {{URL_1}} today"
    assert urls == ["www.example.com/login"]


@pytest.mark.parametrize(
    "text, url",
    [
        ("See http://example.com/a.", "http://example.com/a"),
        ("See (http://example.com/a), ok", "http://example.com/a"),
        ("See <http://example.com/a>", "http://example.com/a"),
        ("Really? http://example.com/a!", "http://example.com/a"),
    ],
)
def test_trailing_punctuation_is_not_part_of_url(text, url):
    masked, urls = mask_urls(text)
    assert urls == [url]
    assert "{{URL_1}}" in masked
    assert unmask_urls(masked, urls) == text


def test_no_url():
    masked, urls = mask_urls("Nothing to see here, mail me at user@www.example.com.")
    assert masked == "Nothing to see here, mail me at user@www.example.com."
    assert urls == []


def test_prefix_alone_is_not_a_url():
    masked, urls = mask_urls("The word http:// alone")
    assert urls == []
    assert masked == "The word http:// alone"


def test_round_trip_is_exact():
    text = "A http://example.com/a?x=1&y=2 B\nC www.example.org. D https://example.net/#frag"
    masked, urls = mask_urls(text)
    assert "example" not in masked
    assert unmask_urls(masked, urls) == text


def test_existing_placeholder_raises():
    with pytest.raises(PlaceholderConflictError):
        mask_urls("This text has {{URL_1}} already")


def test_unknown_placeholder_is_left_alone():
    assert unmask_urls("{{URL_1}} and {{URL_5}}", ["http://example.com"]) == (
        "http://example.com and {{URL_5}}"
    )
