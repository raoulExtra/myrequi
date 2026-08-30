#!/usr/bin/env python3
import argparse
import html as html_lib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'continuity.db'
OUTPUT_DIR = ROOT / 'scientist_reports'
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
        search_results = duckduckgo_search(topic, max_results=max_results)
        for result in search_results:
            summary = ''
            page_text = ''
            try:
                page_text = fetch_url_text(result['url'])
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
                'summary': summary,
                'text_sample': page_text[:600],
            })
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


if __name__ == '__main__':
    main()
