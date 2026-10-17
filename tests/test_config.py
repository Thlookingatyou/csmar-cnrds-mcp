import pytest

from campus_data_mcp.config import CampusError, allowed_url, safe_url, spec_for
from campus_data_mcp.snapshot import access_observation, is_sensitive, redact


@pytest.mark.parametrize(
    "url",
    [
        "https://data.csmar.com/",
        "https://file.csmar.com/export.zip",
        "https://csmar.com/",
        "https://data.csmar.com:443/",
    ],
)
def test_provider_scope_accepts_https_subdomains(url):
    assert allowed_url("csmar", url)


@pytest.mark.parametrize(
    "url",
    [
        "https://csmar.com.evil.invalid/",
        "https://evilcsmar.com/",
        "http://data.csmar.com/",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://user:pass@data.csmar.com/",
        "https://data.csmar.com:444/",
        "https://127.0.0.1/",
        "https://www.cnrds.com/",
        "https://data.csmar.com:bad/",
    ],
)
def test_provider_scope_denies_other_urls(url):
    assert not allowed_url("csmar", url)


def test_extra_hosts_are_exact():
    assert allowed_url("cnrds", "https://sso.university.edu/", ("sso.university.edu",))
    assert not allowed_url("cnrds", "https://x.sso.university.edu/", ("sso.university.edu",))


def test_cnrds_export_host_is_exact_and_provider_specific():
    host = "cnrds-file.oss-cn-shanghai.aliyuncs.com"
    assert allowed_url("cnrds", f"https://{host}/export.7z")
    assert not allowed_url("csmar", f"https://{host}/export.7z")
    assert not allowed_url("cnrds", f"https://x.{host}/export.7z")
    assert not allowed_url("cnrds", "https://other.oss-cn-shanghai.aliyuncs.com/export.7z")
    assert not allowed_url("cnrds", f"http://{host}/export.7z")


def test_safe_url_strips_auth_query_and_fragment():
    assert safe_url("https://u:p@www.cnrds.com/data?token=secret#secret") == (
        "https://www.cnrds.com/data"
    )
    assert safe_url("blob:https://www.cnrds.com/private") == "blob:"


def test_bad_provider():
    with pytest.raises(CampusError):
        spec_for("crnds")


@pytest.mark.parametrize(
    "control",
    [
        {"type": "password"},
        {"placeholder": "用户名"},
        {"name": "username"},
        {"label": "请输入验证码"},
        {"label": "Email"},
        {"name": "access_token"},
    ],
)
def test_authentication_controls_manual_only(control):
    assert is_sensitive(control)


def test_stock_code_is_not_otp():
    assert not is_sensitive({"label": "Stock code", "name": "stock_code"})
    assert not is_sensitive({"label": "学校登录"})


def test_redacts_common_session_secrets():
    assert "secret123" not in redact("token=secret123 sessionId:secret123")
    assert "eyJ" not in redact("eyJhbGciOiJub25lIn0.abc.signature")


def test_access_observations_never_certify_entitlement():
    observed = access_observation("Synthetic University Log out", [])
    assert observed["hint"] == "signed_in_observed"
    assert observed["entitlement"] == "unverified"
    assert access_observation("IP超出限定范围", [])["hint"] == "ip_not_authorized"
