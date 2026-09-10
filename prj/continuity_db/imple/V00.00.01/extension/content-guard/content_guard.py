"""Optional content-guard policy for external research sources."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]
POLICY_PATH = Path(__file__).with_name('source_policy.json')

DEFAULTS = {
    'trusted_domain_suffixes': ('.gov', '.edu'),
    'trusted_european_suffixes': ('.eu', '.europa.eu', '.gov.uk', '.ac.uk'),
    'blocked_domain_suffixes': ('.cn', '.中国', '.香港', '.台湾'),
}


def load_policy(path=POLICY_PATH):
    try:
        with Path(path).open(encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


POLICY = load_policy()
try:
    from llm_guard_adapter import scan_with_optional_guard
except ImportError:  # pragma: no cover - direct policy use remains available
    scan_with_optional_guard = None
TRUSTED_DOMAIN_SUFFIXES = tuple(POLICY.get('trusted_domain_suffixes', DEFAULTS['trusted_domain_suffixes']))
TRUSTED_EUROPEAN_SUFFIXES = tuple(POLICY.get('trusted_european_suffixes', DEFAULTS['trusted_european_suffixes']))
TRUSTED_DOMAIN_MARKERS = set(POLICY.get('trusted_domain_markers', []))
BLOCKED_DOMAIN_SUFFIXES = tuple(POLICY.get('blocked_domain_suffixes', DEFAULTS['blocked_domain_suffixes']))
BLOCKED_DOMAIN_MARKERS = set(POLICY.get('blocked_domain_markers', []))
BLOCKED_SOURCE_MARKERS = set(POLICY.get('blocked_source_markers', []))
AD_MARKERS = {
    'advertisement', 'advertising', 'sponsored', 'sponsor', 'promoted',
    'buy now', 'shop now', 'limited time', 'special offer', 'discount',
    'coupon', 'sale', 'subscribe now', 'get started today', 'affiliate',
    'adchoices', 'utm_source', 'utm_campaign',
}
UNWANTED_CONTENT_PATTERNS = {
    'erotic': (r'\bporn(?:ography)?\b', r'\bhentai\b', r'\bsexually explicit\b', r'\berotic content\b', r'\bescort service\b', r'\bnude photo\b'),
    'spam': (r'\bspam\b', r'\bclick here now\b', r'\bfree money\b', r'\bmake money fast\b', r'\bwork from home guaranteed\b', r'\bnigerian prince\b', r'\blink farm\b', r'\bseo spam\b'),
}
ATTACK_VECTOR_PATTERNS = {
    'xss': (r'<script\b', r'javascript:', r'onerror\s*='),
    'sql_injection': (r'\bsql\s+injection\b', r'\bunion\s+select\b', r"['\"]\s*or\s+['\"]?1['\"]?\s*=\s*['\"]?1"),
    'command_injection': (r'\bcommand\s+injection\b', r'\breverse\s+shell\b', r'\bshell\s+payload\b'),
    'path_traversal': (r'\bpath\s+traversal\b', r'(?:\.\./){2,}'),
    'ssrf': (r'\bssrf\b', r'\bserver[- ]side request forgery\b', r'169\.254\.169\.254'),
    'credential_theft': (r'\bcredential\s+theft\b', r'\bphishing\s+kit\b', r'\bkeylogger\b'),
    'malware': (r'\bransomware\b', r'\bmalware\b', r'\bencoded\s+powershell\b'),
}


def detect_unwanted_content(text):
    haystack = str(text or '').lower()
    return [category for category, patterns in UNWANTED_CONTENT_PATTERNS.items() if any(re.search(pattern, haystack) for pattern in patterns)]


def detect_attack_vectors(text):
    haystack = str(text or '').lower()
    return [category for category, patterns in ATTACK_VECTOR_PATTERNS.items() if any(re.search(pattern, haystack) for pattern in patterns)]


def is_recognizable_ad(url, title='', text=''):
    haystack = f'{url} {title} {text}'.lower()
    marker_hits = sum(marker in haystack for marker in AD_MARKERS)
    path = urlparse(url).path.lower()
    return 'utm_' in url.lower() or '/ads/' in path or '/advert' in path or marker_hits >= 2 or ('sponsored' in title.lower() and marker_hits >= 1)


def classify_source(url, title='', text=''):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower().rstrip('.')
    haystack = f'{host} {parsed.path.lower()} {title.lower()}'
    unwanted = detect_unwanted_content(f'{title} {text}')
    if unwanted:
        return {'allowed': False, 'class': 'blocked_unwanted_content', 'reason': 'unwanted content: ' + ', '.join(unwanted)}
    attacks = detect_attack_vectors(text)
    if attacks:
        return {'allowed': False, 'class': 'blocked_attack_content', 'reason': 'attack-vector content: ' + ', '.join(attacks)}
    if is_recognizable_ad(url, title, text):
        return {'allowed': False, 'class': 'blocked_ad', 'reason': 'recognizable advertising policy'}
    if host.endswith(BLOCKED_DOMAIN_SUFFIXES) or any(host == marker or host.endswith('.' + marker) for marker in BLOCKED_DOMAIN_MARKERS):
        return {'allowed': False, 'class': 'blocked', 'reason': 'blocked domain policy'}
    if any(marker in haystack for marker in BLOCKED_SOURCE_MARKERS):
        return {'allowed': False, 'class': 'blocked', 'reason': 'blocked source marker policy'}
    cjk_count = len(re.findall(r'[\u3400-\u9fff]', title))
    if cjk_count >= 3 and cjk_count / max(len(title), 1) > 0.2:
        return {'allowed': False, 'class': 'blocked', 'reason': 'non-target language policy'}
    trusted = host.endswith(TRUSTED_DOMAIN_SUFFIXES) or host.endswith(TRUSTED_EUROPEAN_SUFFIXES) or any(host == marker or host.endswith('.' + marker) for marker in TRUSTED_DOMAIN_MARKERS)
    if not trusted:
        return {'allowed': False, 'class': 'blocked_untrusted', 'reason': 'not on trusted-domain allowlist'}
    european = host.endswith(TRUSTED_EUROPEAN_SUFFIXES) or any(host == marker or host.endswith('.' + marker) for marker in TRUSTED_DOMAIN_MARKERS if marker.endswith(('.eu', '.int', '.uk', '.de', '.fr', '.ie', '.pl', '.nl', '.se', '.no', '.ch', '.org')))
    return {'allowed': True, 'class': 'trusted_european' if european else 'trusted', 'reason': ''}


def filter_research_results(results, *, guard_required=False, scanners=None):
    accepted = []
    for result in results:
        decision = classify_source(
            result.get('url', ''), result.get('title', ''), result.get('text', '')
        )
        if not decision['allowed']:
            continue
        guard_decision = None
        if scan_with_optional_guard is not None:
            guard_decision = scan_with_optional_guard(
                f"{result.get('title', '')}\n{result.get('text', '')}",
                scanners=scanners,
                required=guard_required,
                source_url=result.get('url', ''),
                source_title=result.get('title', ''),
            )
            if not guard_decision['allowed']:
                continue
        accepted_item = {**result, 'source_class': decision['class']}
        if guard_decision is not None:
            accepted_item['guard_provenance'] = guard_decision['provenance']
        accepted.append(accepted_item)
    return accepted
