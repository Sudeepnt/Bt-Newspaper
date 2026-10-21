import pytest

from pipeline.urls import canonicalize_url


def test_strips_tracking_params_and_fragment():
    assert canonicalize_url(
        "https://Example.com/a/b/?utm_source=x&id=7&fbclid=abc&UTM_Campaign=y#top"
    ) == "https://example.com/a/b?id=7"


def test_sorts_query_and_drops_default_port_and_trailing_slash():
    assert canonicalize_url("http://example.com:80/news/?b=2&a=1") == "http://example.com/news?a=1&b=2"
    assert canonicalize_url("https://example.com:8443/x/") == "https://example.com:8443/x"


def test_root_path_kept_and_idempotent():
    once = canonicalize_url("https://example.com?utm_medium=rss")
    assert once == "https://example.com/"
    assert canonicalize_url(once) == once


def test_keeps_blank_meaningful_params():
    assert canonicalize_url("https://example.com/p?id=&page=2") == "https://example.com/p?id=&page=2"


@pytest.mark.parametrize("bad", ["", "ftp://example.com/x", "javascript:alert(1)", "/relative/path"])
def test_rejects_non_http(bad):
    with pytest.raises(ValueError):
        canonicalize_url(bad)
