"""Fixed DOM inspection; agents never supply JavaScript or arbitrary selectors."""

import re

# We omit all input values, hidden controls, scripts, storage and HTML source.
# References are random, ephemeral IDs, scoped to the latest provider inspection.
SNAPSHOT_JS = r"""({prefix, limit, offset}) => {
  const styles = new WeakMap();
  const styleOf = el => {
    let s = styles.get(el);
    if (!s) { s = getComputedStyle(el); styles.set(el, s); }
    return s;
  };
  const visibility = new WeakMap();
  const visible = el => {
    if (visibility.has(el)) return visibility.get(el);
    const s = styleOf(el);
    const result = s.visibility !== 'hidden' && s.display !== 'none' &&
      [...el.getClientRects()].some(r => r.width > 0 && r.height > 0);
    visibility.set(el, result);
    return result;
  };
  const clean = s => (s || '').replace(/\s+/g, ' ').trim().slice(0, 220);
  const textCache = new WeakMap();
  const textWithin = (root, limit = 700) => {
    const cached = textCache.get(root);
    if (cached && cached.limit === limit) return cached.result;
    const chunks = [];
    let length = 0;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode()) && length < limit) {
      const el = node.parentElement;
      if (!el || el.closest('script,style,noscript,input,textarea,[contenteditable="true"]') ||
          !visible(el)) continue;
      const value = clean(node.textContent);
      if (value) { chunks.push(value); length += value.length + 1; }
    }
    const result = {text: chunks.join('\n').slice(0, limit), truncated: length >= limit};
    textCache.set(root, {limit, result});
    return result;
  };
  const actionSelector =
    'a,button,input,select,textarea,[role="button"],[role="tab"],'+
    '[role="textbox"],[role="combobox"],[role="checkbox"],[contenteditable="true"],'+
    '[role="menuitem"],[role="treeitem"],[role="option"],[role="radio"],'+
    '[role="link"],[onclick],summary,label';
  const selector = actionSelector + ',[tabindex]';
  const semantic = [...document.querySelectorAll(selector)].filter(el => visible(el) &&
    !el.matches('dialog,[role="dialog"],[role="alertdialog"]') &&
    !(el.getAttribute('tabindex') === '-1' && !el.matches(actionSelector)) &&
    (el.tagName !== 'LABEL' || (!el.htmlFor && !el.querySelector('input,select,textarea'))));
  // Dialog focus containers are not actions and must not hide their inner icons.
  // Framework listeners and CSS-only icons often have no text or inline handler.
  const semanticSet = new Set(semantic);
  const actionSet = new Set(semantic.filter(el => el.matches(actionSelector)));
  const covered = new WeakMap();
  const hasActionAncestor = el => {
    if (!el) return false;
    if (covered.has(el)) return covered.get(el);
    const value = actionSet.has(el) || hasActionAncestor(el.parentElement);
    covered.set(el, value);
    return value;
  };
  const pointers = [...document.querySelectorAll('body *')].filter(el =>
    (el instanceof HTMLElement || el instanceof SVGSVGElement) &&
    !semanticSet.has(el) && !hasActionAncestor(el.parentElement) && visible(el) &&
    styleOf(el).cursor === 'pointer');
  const pointerSet = new Set(pointers);
  const nonLeaves = new Set();
  const visited = new Set();
  for (const el of pointers) {
    for (let parent = el.parentElement; parent && !visited.has(parent);
         parent = parent.parentElement) {
      visited.add(parent);
      if (pointerSet.has(parent)) nonLeaves.add(parent);
    }
  }
  const pointerLeaves = pointers.filter(el => !nonLeaves.has(el));
  const candidates = [...semantic, ...pointerLeaves]
    .filter(el => visible(el) && el.type !== 'hidden');
  const controls = candidates.slice(offset, offset + limit).map((el, i) => {
    const ref = prefix + '-' + i;
    el.setAttribute('data-campus-ref', ref);
    const labels = el.labels ? [...el.labels].map(x => x.innerText).join(' ') : '';
    const labelled = (el.getAttribute('aria-labelledby') || '').split(/\s+/)
      .map(id => document.getElementById(id)?.innerText || '').join(' ');
    const label = clean(el.getAttribute('aria-label') || labelled || labels ||
      (el.matches('input,textarea,[contenteditable="true"]') ? '' : el.innerText) ||
      el.getAttribute('title') || el.getAttribute('alt') ||
      el.querySelector('img[alt]')?.getAttribute('alt') || el.getAttribute('placeholder'));
    const row = el.closest('tr,[role="row"]');
    let context = row ? textWithin(row).text : '';
    if (!row && !label) {
      let parent = el.parentElement;
      for (let depth = 0; parent && depth < 4 && !parent.matches('body,html');
           depth++, parent = parent.parentElement) {
        const nearby = textWithin(parent).text;
        if (nearby) { context = nearby; break; }
      }
    }
    const dialog = el.closest('dialog,[role="dialog"],[role="alertdialog"],.modal,.el-dialog');
    const heading = dialog && [...dialog.querySelectorAll('h1,h2,h3,h4,h5,h6,[role="heading"]')]
      .find(visible);
    return {ref, tag: el.tagName.toLowerCase(), type: el.type || '',
      role: el.getAttribute('role') || '', label,
      unlabeled: !label,
      icon_hint: clean(el.getAttribute('class')),
      context,
      dialog: dialog ? clean(dialog.getAttribute('aria-label') ||
        (heading ? textWithin(heading, 220).text : textWithin(dialog, 220).text)) : '',
      placeholder: clean(el.getAttribute('placeholder')),
      name: clean((el.getAttribute('name') || el.id) + ' ' +
        (el.getAttribute('autocomplete') || '')),
      disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
      checked: el.matches('input[type="checkbox"],input[type="radio"]') ? el.checked : null,
      options: el.tagName === 'SELECT' ? [...el.options].slice(0, 100)
        .map(o => ({label: clean(o.text), value: clean(o.value)})) : undefined};
  });
  const body = textWithin(document.body || document.documentElement, 16000);
  return {text: body.text, controls,
    controls_total: candidates.length, control_offset: offset,
    controls_truncated: candidates.length > offset + limit, text_truncated: body.truncated};
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


SCHOOL_LOGIN = re.compile(
    r"(?:学校登录|机构登录|IP登录|IP直接登录|校园网登录|机构IP登录|"
    r"CARSI(?:平台)?\s*登录|CARSI\s+login|School Login|Institutional Login|Campus Login)",
    re.I,
)


def is_school_login(control: dict) -> bool:
    return not control.get("disabled") and bool(SCHOOL_LOGIN.fullmatch(control["label"].strip()))


def access_observation(text: str, controls: list[dict]) -> dict:
    """Report hints, never infer subscription entitlement from a rendered page."""
    if re.search(r"访问过于频繁|请求过于频繁|too many requests|rate.?limit", text, re.I):
        hint = "rate_limited"
    elif re.search(
        r"安全拦截|访问被拦截|您的访问存在异常|HWWAF|418\s+I'm a teapot|bot.*blocked",
        text,
        re.I,
    ):
        hint = "waf_or_bot_blocked"
    elif re.search(r"IP.*(不在|超出|未授权)|not.*authorized.*IP|IP.*out of range", text, re.I):
        hint = "ip_not_authorized"
    elif re.search(r"验证码|captcha|验证身份|verify your identity", text, re.I):
        hint = "manual_verification_may_be_required"
    elif any(is_school_login(control) for control in controls):
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
