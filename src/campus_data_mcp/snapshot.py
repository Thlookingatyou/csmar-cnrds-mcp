"""Fixed DOM inspection; agents never supply JavaScript or arbitrary selectors."""

import re

# We omit all input values, hidden controls, scripts, storage and HTML source.
# References are random, ephemeral IDs, scoped to the latest provider inspection.
SNAPSHOT_JS = r"""({prefix, limit, offset}) => {
  const visible = el => {
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' &&
      el.getClientRects().length > 0;
  };
  const clean = s => (s || '').replace(/\s+/g, ' ').trim().slice(0, 220);
  const selector =
    'a,button,input,select,textarea,[role="button"],[role="tab"],'+
    '[role="textbox"],[role="combobox"],[role="checkbox"],[contenteditable="true"],'+
    '[role="menuitem"],[role="treeitem"],[role="option"],[role="radio"],'+
    '[role="link"],[onclick],[tabindex],summary,label';
  const semantic = [...document.querySelectorAll(selector)].filter(el =>
    el.tagName !== 'LABEL' || (!el.htmlFor && !el.querySelector('input,select,textarea')));
  // Vue/custom widgets often attach listeners without an onclick attribute or
  // accessibility role. Visible pointer leaves can be clicked through bubbling.
  const pointerLeaves = [...document.querySelectorAll('body *')].filter(el =>
    !el.closest(selector) && el.childElementCount === 0 && visible(el) &&
    getComputedStyle(el).cursor === 'pointer' &&
    clean(el.innerText || el.getAttribute('aria-label') || el.getAttribute('title')));
  const candidates = [...semantic, ...pointerLeaves]
    .filter(el => visible(el) && el.type !== 'hidden');
  const controls = candidates.slice(offset, offset + limit).map((el, i) => {
    const ref = prefix + '-' + i;
    el.setAttribute('data-campus-ref', ref);
    const labels = el.labels ? [...el.labels].map(x => x.innerText).join(' ') : '';
    const labelled = (el.getAttribute('aria-labelledby') || '').split(/\s+/)
      .map(id => document.getElementById(id)?.innerText || '').join(' ');
    return {ref, tag: el.tagName.toLowerCase(), type: el.type || '',
      role: el.getAttribute('role') || '',
      label: clean(el.getAttribute('aria-label') || labelled || labels ||
        (el.matches('input,textarea,[contenteditable="true"]') ? '' : el.innerText) ||
        el.getAttribute('title') || el.getAttribute('placeholder')),
      placeholder: clean(el.getAttribute('placeholder')),
      name: clean((el.getAttribute('name') || el.id) + ' ' +
        (el.getAttribute('autocomplete') || '')),
      disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
      checked: el.matches('input[type="checkbox"],input[type="radio"]') ? el.checked : null,
      options: el.tagName === 'SELECT' ? [...el.options].slice(0, 100)
        .map(o => ({label: clean(o.text), value: clean(o.value)})) : undefined};
  });
  const chunks = [];
  let length = 0;
  const walker = document.createTreeWalker(document.body || document.documentElement,
    NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode()) && length < 16000) {
    const el = node.parentElement;
    if (!el || el.closest('script,style,noscript,input,textarea,[contenteditable="true"]') ||
        !visible(el)) continue;
    const value = clean(node.textContent);
    if (value) { chunks.push(value); length += value.length + 1; }
  }
  return {text: chunks.join('\n').slice(0, 16000), controls,
    controls_total: candidates.length, control_offset: offset,
    controls_truncated: candidates.length > offset + limit, text_truncated: length >= 16000};
} """

SENSITIVE_CONTROL = re.compile(
    r"password|passwd|\bpwd\b|用户名|账号|帐户|账户|验证码|手机号|手机号码|邮箱|"
    r"username|user.?name|login.?name|account|captcha|verification|one.?time|"
    r"\botp\b|\bemail\b|\bphone\b|token|secret",
    re.I,
)


def is_sensitive(control: dict) -> bool:
    return control.get("type", "").lower() in {"password", "email", "tel"} or bool(
        SENSITIVE_CONTROL.search(
            " ".join(str(control.get(k, "")) for k in ("label", "placeholder", "name"))
        )
    )


def redact(text: str) -> str:
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[redacted JWT]", text)
    return re.sub(
        r"(?i)\b(token|signcode|sessionid|password|authorization|cookie)\s*[:=]\s*[^\s,;]+",
        r"\1=[redacted]",
        text,
    )


def access_observation(text: str, controls: list[dict]) -> dict:
    """Report hints, never infer subscription entitlement from a rendered page."""
    if re.search(r"访问过于频繁|请求过于频繁|too many requests|rate.?limit", text, re.I):
        hint = "rate_limited"
    elif re.search(r"IP.*(不在|超出|未授权)|not.*authorized.*IP|IP.*out of range", text, re.I):
        hint = "ip_not_authorized"
    elif re.search(r"验证码|captcha|验证身份|verify your identity", text, re.I):
        hint = "manual_verification_may_be_required"
    elif any(re.search(r"学校登录|机构登录|school login", c["label"], re.I) for c in controls):
        hint = "school_login_available"
    elif re.search(r"退出登录|注销|log\s*out|sign\s*out", text, re.I):
        hint = "signed_in_observed"
    elif any(c.get("type") == "password" for c in controls):
        hint = "manual_login_may_be_required"
    else:
        hint = "unknown"
    return {
        "hint": hint,
        "entitlement": "unverified",
        "note": "Only the provider can grant access. A catalogue or sample is not proof "
        "of full-data entitlement. An export receipt does not certify completeness.",
    }
