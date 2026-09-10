#!/usr/bin/env python3
import argparse
import html as html_lib
import json
import re
import os
import sqlite3
import sys
import warnings
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[5]
DB_PATH = ROOT / 'continuity.db'
OUTPUT_DIR = ROOT / 'scientist_reports'
SOURCE_POLICY_PATH = ROOT / 'source_policy.json'
MIN_RESEARCH_SOURCES = 1
__version__ = '0.0.0-placeholder'


def get_version():
    return __version__


TRUSTED_DOMAIN_SUFFIXES = ('.gov', '.edu')
TRUSTED_EUROPEAN_SUFFIXES = ('.eu', '.europa.eu', '.gov.uk', '.ac.uk')
TRUSTED_DOMAIN_MARKERS = {
    'wikipedia.org', 'britannica.com', 'nih.gov', 'ncbi.nlm.nih.gov',
    'nist.gov', 'cisa.gov', 'cdc.gov', 'who.int', 'nasa.gov',
    'ietf.org', 'rfc-editor.org', 'w3.org', 'python.org', 'sqlite.org',
    'kernel.org', 'royalsociety.org',
    'europa.eu', 'europarl.europa.eu', 'ecb.europa.eu', 'ema.europa.eu',
    'esa.int', 'edps.europa.eu', 'echa.europa.eu', 'cordis.europa.eu',
    'bund.de', 'gouv.fr', 'service-public.fr', 'gov.ie', 'gov.pl',
    'government.nl', 'regeringen.se', 'regjeringen.no', 'admin.ch',
}
BLOCKED_DOMAIN_SUFFIXES = (
    '.cn', '.中国', '.香港', '.台湾',
)
BLOCKED_DOMAIN_MARKERS = {
    'baidu.com', 'qq.com', 'sohu.com', 'sina.com.cn', '163.com',
    'wechat.com', 'hackernews.com', 'ycombinator.com', 'hackerone.com',
    'hackforums.net', 'exploit-db.com', 'pastebin.com', 'breachforums.is',
}
BLOCKED_SOURCE_MARKERS = {
    'hacker', 'hacking', 'exploit', 'exploit-db', '0day', 'zero-day',
    'darkweb', 'dark-web', 'ransomware', 'breachforum', 'pastebin',
}
AD_MARKERS = {
    'advertisement', 'advertising', 'sponsored', 'sponsor', 'promoted',
    'buy now', 'shop now', 'limited time', 'special offer',
    'discount', 'coupon', 'sale', 'subscribe now', 'get started today',
    'affiliate', 'adchoices', 'utm_source', 'utm_campaign',
}
UNWANTED_CONTENT_PATTERNS = {
    'erotic': (
        r'\bporn(?:ography)?\b', r'\bhentai\b', r'\bsexually explicit\b',
        r'\berotic content\b', r'\bescort service\b', r'\bnude photo\b',
    ),
    'spam': (
        r'\bspam\b', r'\bclick here now\b', r'\bfree money\b',
        r'\bmake money fast\b', r'\bwork from home guaranteed\b',
        r'\bnigerian prince\b', r'\blink farm\b', r'\bseo spam\b',
    ),
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



def load_source_policy(path=SOURCE_POLICY_PATH):
    """Load domain policy from JSON, retaining safe code defaults on failure."""
    try:
        with Path(path).open(encoding='utf-8') as handle:
            policy = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return
    globals()['MIN_RESEARCH_SOURCES'] = int(policy.get('minimum_sources', MIN_RESEARCH_SOURCES))
    globals()['TRUSTED_DOMAIN_SUFFIXES'] = tuple(policy.get('trusted_domain_suffixes', TRUSTED_DOMAIN_SUFFIXES))
    globals()['TRUSTED_EUROPEAN_SUFFIXES'] = tuple(policy.get('trusted_european_suffixes', TRUSTED_EUROPEAN_SUFFIXES))
    globals()['TRUSTED_DOMAIN_MARKERS'] = set(policy.get('trusted_domain_markers', TRUSTED_DOMAIN_MARKERS))
    globals()['BLOCKED_DOMAIN_SUFFIXES'] = tuple(policy.get('blocked_domain_suffixes', BLOCKED_DOMAIN_SUFFIXES))
    globals()['BLOCKED_DOMAIN_MARKERS'] = set(policy.get('blocked_domain_markers', BLOCKED_DOMAIN_MARKERS))
    globals()['BLOCKED_SOURCE_MARKERS'] = set(policy.get('blocked_source_markers', BLOCKED_SOURCE_MARKERS))


load_source_policy()


STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'has', 'was', 'were', 'are', 'is', 'be', 'been',
    'not', 'but', 'you', 'your', 'their', 'they', 'them', 'into', 'about', 'what', 'when', 'where', 'why', 'how',
    'can', 'could', 'would', 'should', 'may', 'might', 'will', 'shall', 'analysis', 'scientist', 'mode', 'file',
    'topic', 'research', 'report', 'markdown', 'notes', 'note', 'more', 'less', 'than', 'then', 'also', 'such',
}


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text or 'analysis'


def read_text(path):
    return Path(path).read_text(encoding='utf-8')


def detect_title_from_text(text, fallback):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('#'):
            return line.lstrip('#').strip() or fallback
    return fallback


def summarize_file_text(text, source_name):
    lines = text.splitlines()
    nonempty = [ln.strip() for ln in lines if ln.strip()]
    headings = [ln.lstrip('#').strip() for ln in nonempty if ln.startswith('#')]
    bullets = [ln.strip('-* ').strip() for ln in nonempty if ln.startswith(('-', '*'))]
    words = re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
    keywords = [w for w, _ in counts.most_common(8)]
    summary = (
        f"The file '{source_name}' has {len(lines)} lines and {len(words)} words. "
        f"It contains {len(headings)} headings and {len(bullets)} bullet-style lines."
    )
    if headings:
        summary += f" Primary headings suggest the main themes are: {', '.join(headings[:4])}."
    elif nonempty:
        summary += f" The opening content begins with: {nonempty[0][:120]}."
    return summary, headings, bullets, keywords


def summarize_topic(topic):
    words = re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", topic.lower())
    counts = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
    keywords = [w for w, _ in counts.most_common(6)] or [topic.lower()]
    summary = (
        f"This is a scientist-style analysis brief for the topic '{topic}'. "
        f"It frames the question, identifies evidence to seek, and highlights uncertainty."
    )
    return summary, keywords


def strip_html(text):
    text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', text)
    text = re.sub(r'(?s)<[^>]+>', ' ', text)
    text = html_lib.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def fetch_url_raw(url, timeout=20, max_chars=50000):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (scientist-command)'})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read(max_chars)
        charset = resp.headers.get_content_charset() or 'utf-8'
    return raw.decode(charset, errors='ignore')


def fetch_url_text(url, timeout=20, max_chars=12000):
    return strip_html(fetch_url_raw(url, timeout=timeout, max_chars=max_chars * 4))[:max_chars]


def detect_unwanted_content(text):
    """Return labels for erotic or spam content that research must exclude."""
    haystack = str(text or '').lower()
    return [
        category for category, patterns in UNWANTED_CONTENT_PATTERNS.items()
        if any(re.search(pattern, haystack) for pattern in patterns)
    ]


def detect_attack_vectors(text):
    """Return defensive labels for common attack-vector content indicators."""
    haystack = str(text or '').lower()
    return [
        category for category, patterns in ATTACK_VECTOR_PATTERNS.items()
        if any(re.search(pattern, haystack) for pattern in patterns)
    ]


def is_recognizable_ad(url, title='', text=''):
    """Detect obvious advertising/affiliate pages, not ordinary editorial mentions."""
    haystack = f'{url} {title} {text}'.lower()
    marker_hits = sum(marker in haystack for marker in AD_MARKERS)
    path = urlparse(url).path.lower()
    return (
        'utm_' in url.lower()
        or '/ads/' in path
        or '/advert' in path
        or marker_hits >= 2
        or ('sponsored' in title.lower() and marker_hits >= 1)
    )


def classify_source(url, title='', text=''):
    """Return a source policy decision before/after fetching untrusted content."""
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower().rstrip('.')
    haystack = f'{host} {parsed.path.lower()} {title.lower()}'
    unwanted_content = detect_unwanted_content(f'{title} {text}')
    if unwanted_content:
        return {
            'allowed': False,
            'class': 'blocked_unwanted_content',
            'reason': 'unwanted content: ' + ', '.join(unwanted_content),
        }
    attack_vectors = detect_attack_vectors(text)
    if attack_vectors:
        return {
            'allowed': False,
            'class': 'blocked_attack_content',
            'reason': 'attack-vector content: ' + ', '.join(attack_vectors),
        }
    if is_recognizable_ad(url, title, text):
        return {'allowed': False, 'class': 'blocked_ad', 'reason': 'recognizable advertising policy'}
    if host.endswith(BLOCKED_DOMAIN_SUFFIXES) or any(
        host == marker or host.endswith('.' + marker)
        for marker in BLOCKED_DOMAIN_MARKERS
    ):
        return {'allowed': False, 'class': 'blocked', 'reason': 'blocked domain policy'}
    if any(marker in haystack for marker in BLOCKED_SOURCE_MARKERS):
        return {'allowed': False, 'class': 'blocked', 'reason': 'blocked source marker policy'}
    cjk_count = len(re.findall(r'[\u3400-\u9fff]', title))
    if cjk_count >= 3 and cjk_count / max(len(title), 1) > 0.2:
        return {'allowed': False, 'class': 'blocked', 'reason': 'non-target language policy'}
    trusted = (
        host.endswith(TRUSTED_DOMAIN_SUFFIXES)
        or host.endswith(TRUSTED_EUROPEAN_SUFFIXES)
        or any(
        host == marker or host.endswith('.' + marker)
        for marker in TRUSTED_DOMAIN_MARKERS
        )
    )
    if not trusted:
        return {'allowed': False, 'class': 'blocked_untrusted', 'reason': 'not on trusted-domain allowlist'}
    region = 'european' if (
        host.endswith(TRUSTED_EUROPEAN_SUFFIXES)
        or any(host == marker or host.endswith('.' + marker) for marker in (
            'europa.eu', 'europarl.europa.eu', 'ecb.europa.eu', 'ema.europa.eu',
            'esa.int', 'edps.europa.eu', 'echa.europa.eu', 'cordis.europa.eu',
            'bund.de', 'gouv.fr', 'service-public.fr', 'gov.ie', 'gov.pl',
            'government.nl', 'regeringen.se', 'regjeringen.no', 'admin.ch',
            'royalsociety.org',
        ))
    ) else 'general'
    return {'allowed': True, 'class': 'trusted_' + region, 'reason': ''}

def filter_research_results(results):
    accepted = []
    for result in results:
        policy = classify_source(result.get('url', ''), result.get('title', ''))
        if policy['allowed']:
            accepted.append({**result, 'source_class': policy['class']})
    return accepted


def normalize_result_url(href):
    href = html_lib.unescape(href)
    if href.startswith('//'):
        href = 'https:' + href
    parsed = urlparse(href)
    if parsed.path.startswith('/l/'):
        query = parse_qs(parsed.query)
        if 'uddg' in query and query['uddg']:
            return unquote(query['uddg'][0])
    return href


def duckduckgo_search(query, max_results=5):
    search_url = 'https://html.duckduckgo.com/html/?q=' + quote_plus(query)
    html_text = fetch_url_raw(search_url, timeout=25, max_chars=50000)
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="(.*?)"[^>]*>(.*?)</a>', re.S)
    results = []
    for href, title_html in pattern.findall(html_text):
        url = normalize_result_url(href)
        if not url.startswith('http'):
            continue
        title = strip_html(title_html)
        results.append({'title': title, 'url': url})
        if len(results) >= max_results:
            break
    return results


def wikipedia_search(query, max_results=5):
    """Use Wikipedia as a resilient fallback when DuckDuckGo has no results."""
    search_url = (
        'https://en.wikipedia.org/w/api.php?action=query&list=search&format=json'
        '&utf8=1&srlimit=' + str(max_results) + '&srsearch=' + quote_plus(query)
    )
    payload = json.loads(fetch_url_raw(search_url, timeout=20, max_chars=50000))
    results = []
    for item in payload.get('query', {}).get('search', []):
        title = str(item.get('title') or '').strip()
        if not title:
            continue
        results.append({
            'title': title,
            'url': 'https://en.wikipedia.org/wiki/' + quote_plus(title.replace(' ', '_')),
        })
    return results[:max_results]


def sentence_score(sentence, keywords):
    s = sentence.lower()
    score = 0
    for kw in keywords:
        if kw in s:
            score += 1
    return score


def summarize_text_for_query(text, query, max_sentences=3):
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text)
    keywords = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9_'-]+", query.lower()) if w not in STOPWORDS and len(w) > 3]
    scored = [(sentence_score(sentence, keywords), sentence.strip()) for sentence in sentences if sentence.strip()]
    scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    picks = [s for score, s in scored if score > 0][:max_sentences]
    if not picks:
        picks = [s for s in sentences if s.strip()][:max_sentences]
    return ' '.join(picks)[:1200]


def journal_analysis(conn, target, kind, output_path, research_job_id=None):
    cur = conn.cursor()
    note = f"Scientist analysis created for {kind} target '{target}' at {output_path}"
    if research_job_id is not None:
        note += f" (research_job_id={research_job_id})"
    cur.execute(
        'INSERT INTO journal(category, summary, status) VALUES (?,?,?)',
        ('scientist_analysis', note, 'active'),
    )
    conn.commit()


def ensure_output_dir(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)


def write_report(output_dir, slug, content):
    ensure_output_dir(output_dir)
    output_path = output_dir / f'{slug}.scientist-analysis.md'
    output_path.write_text(content, encoding='utf-8')
    return output_path


def build_markdown(title, source_label, kind, summary, key_points, keywords, questions, next_steps, research_sources=None):
    lines = [
        f'# Scientist Analysis: {title}',
        '',
        f'- Mode: {kind}',
        f'- Source: {source_label}',
        '',
        '## Summary',
        summary,
        '',
        '## Key points',
    ]
    if key_points:
        lines.extend([f'- {point}' for point in key_points])
    else:
        lines.append('- None extracted.')
    lines.extend([
        '',
        '## Keywords',
        ', '.join(keywords) if keywords else 'None',
        '',
        '## Open questions',
    ])
    if questions:
        lines.extend([f'- {q}' for q in questions])
    else:
        lines.append('- What evidence would change the conclusion?')

    if research_sources is not None:
        lines.extend(['', '## Web research'])
        if research_sources:
            for source in research_sources:
                bullet = f"- [{source['title']}]({source['url']})"
                if source.get('summary'):
                    bullet += f": {source['summary']}"
                lines.append(bullet)
        else:
            lines.append('- No live web sources were retrieved.')

    lines.extend([
        '',
        '## Next steps',
    ])
    lines.extend([f'- {step}' for step in next_steps])
    lines.extend([
        '',
        '## Confidence note',
        'This report is a structured scientist-style analysis, not a claim of final truth.',
    ])
    return '\n'.join(lines) + '\n'


def analyze_file_target(target_path, output_dir):
    text = read_text(target_path)
    title = detect_title_from_text(text, Path(target_path).stem)
    summary, headings, bullets, keywords = summarize_file_text(text, Path(target_path).name)
    key_points = []
    key_points.extend(headings[:5])
    key_points.extend(bullets[:5])
    if not key_points:
        key_points.append('No headings or bullets detected; use the text body as the primary source.')
    questions = [
        'Which claims are directly supported by the text?',
        'What evidence is missing or implied?',
        'What would a reviewer challenge first?',
    ]
    next_steps = [
        'Extract the strongest claims into a claims/evidence table.',
        'Check for missing citations, definitions, and assumptions.',
        'Identify one falsifiable hypothesis from the document.',
    ]
    content = build_markdown(title, str(target_path), 'file', summary, key_points, keywords, questions, next_steps)
    slug = slugify(Path(target_path).stem)
    output_path = write_report(output_dir, slug, content)
    return title, output_path, content, None


def perform_web_research(conn, topic, max_results=5):
    cur = conn.cursor()
    cur.execute('INSERT INTO research_jobs(query, status) VALUES (?, ?)', (topic, 'running'))
    job_id = cur.lastrowid
    conn.commit()
    sources = []
    try:
        search_results = filter_research_results(duckduckgo_search(topic, max_results=max_results))
        if not search_results:
            try:
                search_results = filter_research_results(wikipedia_search(topic, max_results=max_results))
            except Exception:
                search_results = []
        for result in search_results:
            summary = ''
            page_text = ''
            try:
                page_text = fetch_url_text(result['url'])
                if not classify_source(result['url'], result['title'], page_text)['allowed']:
                    continue
                summary = summarize_text_for_query(page_text, topic)
            except Exception as exc:
                summary = f'Unavailable ({exc.__class__.__name__})'
            publisher = urlparse(result['url']).netloc
            cur.execute(
                'INSERT INTO research_sources(job_id, title, url, publisher, notes) VALUES (?,?,?,?,?)',
                (job_id, result['title'], result['url'], publisher, summary[:4000]),
            )
            sources.append({
                'title': result['title'],
                'url': result['url'],
                'publisher': publisher,
                'source_class': result.get('source_class', 'general'),
                'summary': summary,
                'text_sample': page_text[:600],
            })
        if len(sources) < MIN_RESEARCH_SOURCES:
            raise RuntimeError(
                f'Only {len(sources)} trusted research sources found; '
                f'{MIN_RESEARCH_SOURCES} required.'
            )
        result_summary = f'Collected {len(sources)} live web sources for topic research.'
        cur.execute(
            'UPDATE research_jobs SET status=?, result_summary=?, completed_at=CURRENT_TIMESTAMP WHERE id=?',
            ('completed', result_summary, job_id),
        )
        conn.commit()
    except Exception as exc:
        cur.execute(
            'UPDATE research_jobs SET status=?, error=?, completed_at=CURRENT_TIMESTAMP WHERE id=?',
            ('failed', str(exc), job_id),
        )
        conn.commit()
        raise
    return {'job_id': job_id, 'sources': sources, 'result_summary': result_summary}


def analyze_topic_target(conn, topic, output_dir):
    title = topic.strip()
    summary, keywords = summarize_topic(topic)
    research = perform_web_research(conn, topic)
    sources = research['sources']
    if sources:
        summary = (
            f"Live web research on '{topic}' found {len(sources)} sources. "
            f"The strongest theme across the retrieved material is that the topic should be treated as a research question, not a settled fact."
        )
    key_points = [
        'Define the central question clearly.',
        'List the strongest existing evidence and the weakest assumptions.',
        'Separate observations, inferences, and open questions.',
    ]
    if sources:
        key_points.append(f"Live sources retrieved: {', '.join(src['title'] for src in sources[:3])}")
    questions = [
        f'What would count as direct evidence about {topic}?',
        f'What alternative explanations could also account for {topic}?',
        'What result would most change the current view?',
    ]
    next_steps = [
        'Read the live sources and extract claims into a claims/evidence table.',
        'Write down competing hypotheses before making a conclusion.',
        'Record uncertainties explicitly in the report.',
    ]
    if sources:
        next_steps.append('Cite the live web sources directly in follow-up notes or experiments.')
    content = build_markdown(title, topic, 'topic', summary, key_points, keywords, questions, next_steps, research_sources=sources)
    output_path = write_report(output_dir, slugify(topic), content)
    return title, output_path, content, research['job_id']


def run_scientist_analyse(target, db_path=DB_PATH, output_dir=OUTPUT_DIR):
    conn = connect(db_path)
    try:
        target_path = Path(target)
        if target_path.exists() and target_path.is_file():
            title, output_path, content, research_job_id = analyze_file_target(target_path, output_dir)
            kind = 'file'
        else:
            title, output_path, content, research_job_id = analyze_topic_target(conn, target, output_dir)
            kind = 'topic'
        journal_analysis(conn, target, kind, output_path, research_job_id=research_job_id)
    finally:
        conn.close()

    return json.dumps(
        {
            'kind': kind,
            'target': target,
            'title': title,
            'output_path': str(output_path),
            'bytes_written': len(content.encode('utf-8')),
            'research_job_id': research_job_id,
        }
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['analyse'])
    parser.add_argument('target')
    parser.add_argument('--db', default=str(DB_PATH))
    parser.add_argument('--outdir', default=str(OUTPUT_DIR))
    args = parser.parse_args()
    print(run_scientist_analyse(args.target, db_path=Path(args.db), output_dir=Path(args.outdir)))




def activate_content_guard():
    """Load the optional content guard without making it a core dependency."""
    if os.environ.get('CONTENT_GUARD_ENABLED', '1').lower() in {'0', 'false', 'off', 'no'}:
        warnings.warn('content-guard extension is disabled; using reduced source checks', RuntimeWarning)
        return False
    extension_dir = Path(__file__).resolve().parents[1] / 'extension' / 'content-guard'
    if not extension_dir.is_dir():
        warnings.warn('content-guard extension is unavailable; using reduced source checks', RuntimeWarning)
        return False
    sys.path.insert(0, str(extension_dir))
    try:
        import content_guard as guard
    except Exception as exc:
        warnings.warn(f'content-guard extension failed to load: {exc}; using reduced source checks', RuntimeWarning)
        return False
    globals()['classify_source'] = guard.classify_source
    globals()['filter_research_results'] = guard.filter_research_results
    globals()['detect_unwanted_content'] = guard.detect_unwanted_content
    globals()['detect_attack_vectors'] = guard.detect_attack_vectors
    globals()['is_recognizable_ad'] = guard.is_recognizable_ad
    globals()['MIN_RESEARCH_SOURCES'] = int(guard.POLICY.get('minimum_sources', MIN_RESEARCH_SOURCES))
    globals()['CONTENT_GUARD_ACTIVE'] = True
    return True


CONTENT_GUARD_ACTIVE = activate_content_guard()


if __name__ == '__main__':
    main()
