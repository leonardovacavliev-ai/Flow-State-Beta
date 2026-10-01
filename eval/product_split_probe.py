#!/usr/bin/env python3
"""
Read-only measurements behind PRODUCT_LINE_SPLIT_SCOPE.md.

Every number in that document should be reproducible by running this against
the live index. Nothing here writes to Pinecone or Postgres.

    python3 eval/product_split_probe.py audit      # per-ESP chunk/product table
    python3 eval/product_split_probe.py headers    # Yotpo product-header coverage (reads Postgres)
    python3 eval/product_split_probe.py contam     # loyalty questions pulling Reviews context
    python3 eval/product_split_probe.py reviewq    # Reviews questions: what they retrieve, incl. global
    python3 eval/product_split_probe.py names      # share of chunks naming their own product
    python3 eval/product_split_probe.py console    # the wrong-admin-console case
    python3 eval/product_split_probe.py queryb     # Query B (mechanics) per ESP
    python3 eval/product_split_probe.py filters    # $in / $nin semantics on absent keys
    python3 eval/product_split_probe.py traffic    # saved-conversation counts (aggregate only)

Labels are assigned from source_url because no `product` field exists yet.
That rule is known to be wrong for some documents -- see the scope, section 5.
Listrak's articles_2283752 is a Reviews guide with a URL that names no product.
"""
import os
import re
import sys
import random
import warnings
from collections import Counter, defaultdict

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE, ".env"))  # explicit path; a bare load_dotenv() misses it

# Mirrors app.py: filter_by_relevance default for Pinecone, Query A/B sizes, MECHANICS_QUERY.
MIN_SCORE = 0.35
TOP_K_A = 10
TOP_K_B = 5
MECHANICS_QUERY = (
    "How triggers and profile filters qualify subscribers: trigger filters are "
    "not checked again at send time, profile filters are re-checked before each "
    "component. Flow trigger types: list, segment, metric event, price drop, "
    "date property. Understanding time delays between flow components."
)

# (question, names_a_product). The unnamed ones are ambiguous, not contaminated:
# under a both-products goal a Reviews chunk is a legitimate answer to them.
LOYALTY_QUESTIONS = [
    ("How do I connect my Yotpo loyalty program to my ESP?", True),
    ("How do I set up the Yotpo Loyalty and Referrals integration?", True),
    ("Which loyalty events sync to my ESP?", True),
    ("What loyalty customer properties are available for segmentation?", True),
    ("How do I build a segment of VIP tier members?", True),
    ("How do I trigger a flow when a customer earns points?", True),
    ("How do I send a points expiration reminder?", True),
    ("How do I enable the integration from the Yotpo admin?", False),
    ("How do I segment customers by their loyalty activity?", True),
    ("How do I show a customer's point balance in an email?", True),
]

REVIEW_QUESTIONS = [
    "How do I connect Yotpo Reviews to my ESP?",
    "How do I trigger a flow when a customer leaves a review?",
    "How do I segment customers by star rating?",
    "How do I add review content to an email?",
    "Which review events does Yotpo send to my ESP?",
    "How do I send a review request email?",
]

PROPERTY_KEYWORDS = ['property', 'properties', 'field', 'fields', 'variable',
                     'variables', 'data', 'attribute']  # app.py chat()

SELECTABLE_ESPS = ["klaviyo", "attentive", "dotdigital", "omnisend",
                   "listrak", "ometria", "postscript", "emarsys", "other_webhook"]


def url_label(url):
    u = (url or "").lower()
    if "review" in u:
        return "reviews"
    if "loyalty" in u or "referral" in u:
        return "loyalty"
    return "url-silent"


_index = None
_model = None


def index():
    global _index
    if _index is None:
        from pinecone import Pinecone
        _index = Pinecone(api_key=os.environ["PINECONE_API_KEY"]).Index(
            os.environ["PINECONE_INDEX_NAME"])
    return _index


def model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def all_metadata(with_text=False):
    idx = index()
    ids = [i for page in idx.list() for i in page]
    out = {}
    for i in range(0, len(ids), 100):
        for vid, v in idx.fetch(ids=ids[i:i + 100]).vectors.items():
            md = dict(v.metadata or {})
            if not with_text:
                md.pop("text", None)
            out[vid] = md
    return out


def query(text, esp, top_k, extra_filter=None):
    f = {"esp": {"$eq": esp}}
    if extra_filter:
        f.update(extra_filter)
    res = index().query(vector=model().encode(text).tolist(), top_k=top_k,
                        filter=f, include_metadata=True)
    return [m for m in res["matches"] if m["score"] >= MIN_SCORE]


def production_context(message, esp):
    """Queries A, B and C as app.py chat() builds them for a first-turn message:
    property-keyword boost on A, Query B's ids removed from A, global C with n=2.
    Not modelled: the previous-answer append on later turns."""
    q = message
    if any(k in message.lower() for k in PROPERTY_KEYWORDS):
        q = f"{q} property definition list documentation"
    a = query(q, esp, TOP_K_A)
    b = query(MECHANICS_QUERY, esp, TOP_K_B)
    b_ids = {m["id"] for m in b}
    a = [m for m in a if m["id"] not in b_ids]
    c = query(q, "global", 2)
    return a, b, c


def labels(matches):
    return [url_label(m["metadata"].get("source_url")) for m in matches]


def cmd_audit():
    md = all_metadata()
    per = defaultdict(Counter)
    docs = defaultdict(set)
    has_product = 0
    for m in md.values():
        esp = m.get("esp")
        per[esp][url_label(m.get("source_url"))] += 1
        docs[esp].add(m.get("filename"))
        has_product += "product" in m
    print(f"{len(md)} vectors, {sum(len(d) for d in docs.values())} documents, "
          f"{len(per)} esp values; vectors carrying a `product` key: {has_product}\n")
    print(f"{'esp':<12}{'docs':>5}{'chunks':>8}{'loyalty':>9}{'reviews':>9}{'url-silent':>12}{'rev%':>6}")
    tot = Counter()
    for esp in sorted(per, key=lambda e: -sum(per[e].values())):
        c = per[esp]; n = sum(c.values()); tot.update(c)
        print(f"{esp:<12}{len(docs[esp]):>5}{n:>8}{c['loyalty']:>9}{c['reviews']:>9}"
              f"{c['url-silent']:>12}{100 * c['reviews'] / n:>5.0f}%")
    n = sum(tot.values())
    print(f"{'total':<12}{sum(len(d) for d in docs.values()):>5}{n:>8}{tot['loyalty']:>9}"
          f"{tot['reviews']:>9}{tot['url-silent']:>12}{100 * tot['reviews'] / n:>5.0f}%")
    print("\nurl-silent documents (need a human decision, not assumed platform):")
    silent = defaultdict(Counter)
    for m in md.values():
        if url_label(m.get("source_url")) == "url-silent":
            silent[m["esp"]][m["filename"]] += 1
    for esp in sorted(silent):
        for fn, k in silent[esp].most_common():
            print(f"  {esp:<11}{k:>4}  {fn}")


HEADER = re.compile(r"^\s*(?:Yotpo)?Products?\s*$", re.I | re.M)


def header_label(text):
    m = HEADER.search(text[:1500])
    if not m:
        return None
    for line in [l.strip() for l in text[m.end():m.end() + 120].split("\n") if l.strip()][:2]:
        ll = line.lower()
        if "loyalty" in ll or "referral" in ll:
            return "loyalty"
        if "review" in ll:
            return "reviews"
    return None


def cmd_headers():
    """Reads esp_documents.content: the chunker drops the short header section,
    so it never reaches a vector."""
    import psycopg2
    cur = psycopg2.connect(os.environ["DATABASE_URL"]).cursor()
    # Only rows with stored content: failed crawls have nothing to label.
    cur.execute("SELECT e.name, d.filename, d.url, d.content FROM esp_documents d "
                "JOIN esps e ON e.id = d.esp_id WHERE d.content IS NOT NULL "
                "ORDER BY e.name, d.filename")
    rows = cur.fetchall()
    hits = conflicts = 0
    print(f"{'esp':<14}{'header':<9}{'url':<11} document")
    for esp, fn, url, content in rows:
        h = header_label(content or "")
        hits += h is not None
        u = url_label(url)
        clash = h is not None and u != "url-silent" and h != u
        conflicts += clash
        print(f"{esp:<14}{h or '-':<9}{u:<11} {fn}{'  <-- header and URL disagree' if clash else ''}")
    print(f"\nYotpo product header found in {hits}/{len(rows)} documents with content "
          f"({100 * hits / len(rows):.0f}%); disagreements with a product-naming URL: {conflicts}. "
          f"The rest need a human decision.")


def cmd_contam():
    """Loyalty questions. Counts Query A (after B-removal) and the full A+B+C context."""
    per_q = defaultdict(lambda: [0, 0])
    print(f"{'esp':<14}{'A kept':>7}{'A rev':>7}{'A rev%':>8}{'rev@1':>7}{'full ctx':>10}{'full rev':>9}")
    tot = Counter()
    for esp in SELECTABLE_ESPS:
        c = Counter()
        for q, named in LOYALTY_QUESTIONS:
            a, b, g = production_context(q, esp)
            la, lfull = labels(a), labels(a + b + g)
            c["a"] += len(a); c["ar"] += la.count("reviews")
            c["r1"] += bool(la) and la[0] == "reviews"
            c["f"] += len(lfull); c["fr"] += lfull.count("reviews")
            c["named_a"] += len(a) * named; c["named_ar"] += la.count("reviews") * named
            per_q[q][0] += len(a); per_q[q][1] += la.count("reviews")
        tot.update(c)
        if c["ar"]:
            tot["aff_a"] += c["a"]; tot["aff_ar"] += c["ar"]
        print(f"{esp:<14}{c['a']:>7}{c['ar']:>7}{(100 * c['ar'] / c['a'] if c['a'] else 0):>7.1f}%"
              f"{c['r1']:>4}/{len(LOYALTY_QUESTIONS)}{c['f']:>10}{c['fr']:>9}")
    nq = len(SELECTABLE_ESPS) * len(LOYALTY_QUESTIONS)
    print(f"\nQuery A, all ESPs:        {tot['ar']}/{tot['a']} = {100 * tot['ar'] / tot['a']:.1f}%  rank-1 {tot['r1']}/{nq}")
    print(f"Query A, affected ESPs:   {tot['aff_ar']}/{tot['aff_a']} = {100 * tot['aff_ar'] / tot['aff_a']:.1f}%")
    print(f"Query A, product-named questions only: {tot['named_ar']}/{tot['named_a']} = "
          f"{100 * tot['named_ar'] / tot['named_a']:.1f}%")
    print(f"full context (A+B+C):     {tot['fr']}/{tot['f']} = {100 * tot['fr'] / tot['f']:.1f}%")

    qs = list(per_q)
    random.seed(0)
    boots = []
    for _ in range(5000):
        smp = [random.choice(qs) for _ in qs]
        kk = sum(per_q[q][0] for q in smp)
        boots.append(100 * sum(per_q[q][1] for q in smp) / kk if kk else 0)
    boots.sort()
    print(f"cluster bootstrap over {len(qs)} questions (Query A, all ESPs): "
          f"95% interval {boots[125]:.0f}%-{boots[4875]:.0f}%")

    try:
        import psycopg2
        cur = psycopg2.connect(os.environ["DATABASE_URL"]).cursor()
        cur.execute("SELECT esp, COUNT(*) FROM messages WHERE role='user' GROUP BY esp")
        traffic = dict(cur.fetchall())
        rates = {}
        for esp in SELECTABLE_ESPS:
            k = r = 0
            for q, _ in LOYALTY_QUESTIONS:
                la = labels(production_context(q, esp)[0]); k += len(la); r += la.count("reviews")
            rates[esp] = r / k if k else 0
        w = sum(traffic.get(e, 0) for e in rates)
        print(f"weighted by production user messages: "
              f"{100 * sum(rates[e] * traffic.get(e, 0) for e in rates) / w:.0f}%")
    except Exception as e:
        print(f"(traffic weighting skipped: {e})")

    print("\nper question, Query A, all ESPs:")
    for q, named in LOYALTY_QUESTIONS:
        kk, rr = per_q[q]
        print(f"  {rr:>3}/{kk:<4} {'' if named else '[names no product] '}{q}")


def cmd_reviewq():
    """Reviews questions. Shows the top-ranked document so URL-silent Reviews guides are visible."""
    print(f"{'esp':<14}{'A kept':>7}{'rev':>5}{'loy':>5}{'silent':>7}{'global loy':>11}  rank-1 document per question")
    r1 = Counter(); gfiles = Counter(); silent = defaultdict(Counter)
    for esp in SELECTABLE_ESPS:
        c = Counter(); tops = Counter()
        for q in REVIEW_QUESTIONS:
            a, b, g = production_context(q, esp)
            la = labels(a)
            c["a"] += len(a); c.update(la)
            c["gl"] += labels(g).count("loyalty"); c["g"] += len(g)
            tops[a[0]["metadata"]["filename"] if a else "(nothing >= 0.35)"] += 1
            r1[(esp, labels(a[:1])[0] if a else "none")] += 1
            for m in a:
                if url_label(m["metadata"].get("source_url")) == "url-silent":
                    silent[esp][m["metadata"]["filename"]] += 1
            for m in g:
                gfiles[m["metadata"]["filename"]] += 1
        top = "; ".join(f"{n}x {fn[:44]}" for fn, n in tops.most_common(2))
        print(f"{esp:<14}{c['a']:>7}{c['reviews']:>5}{c['loyalty']:>5}{c['url-silent']:>7}"
              f"{c['gl']:>6}/{c['g']:<4}  {top}")
    with_docs = ["klaviyo", "attentive", "dotdigital", "omnisend"]
    n = sum(v for (e, _), v in r1.items() if e in with_docs)
    k = sum(v for (e, l), v in r1.items() if e in with_docs and l == "reviews")
    print(f"\nrank 1 is a Reviews-URL document on {k}/{n} questions across {', '.join(with_docs)}")
    print("global chunks retrieved (same for every ESP; global has no ESP filter):",
          dict(gfiles))
    print("\nURL-silent chunks retrieved, by document:")
    for esp in SELECTABLE_ESPS:
        if silent[esp]:
            print(f"  {esp:<14}" + "; ".join(f"{n}x {fn}" for fn, n in silent[esp].most_common()))


def cmd_names():
    LOYM = re.compile(r"loyalty|referral|\bpoints?\b|\bvip\b|\btiers?\b|redeem|reward", re.I)
    REVM = re.compile(r"\breviews?\b|reviewer|star rating|\bratings?\b|\bugc\b", re.I)
    n = k = 0
    for m in all_metadata(with_text=True).values():
        lab = url_label(m.get("source_url"))
        if lab == "url-silent":
            continue
        n += 1
        k += bool((LOYM if lab == "loyalty" else REVM).search(m.get("text", "")))
    print(f"{k}/{n} product-labelled chunks contain a term for their own product ({100 * k / n:.0f}%)")
    print("terms: loyalty|referral|points|vip|tier|redeem|reward ; reviews|reviewer|star rating|ratings|ugc")


def cmd_console():
    q = "Where in the Yotpo admin do I start the integration?"
    for esp in ("attentive", "klaviyo"):
        print(f"\n{esp}: {q!r}")
        res = index().query(vector=model().encode(q).tolist(), top_k=5,
                            filter={"esp": {"$eq": esp}}, include_metadata=True)
        for rank, m in enumerate(res["matches"], 1):
            t = m["metadata"].get("text", "")
            line = next((l.strip() for l in t.split("\n") if re.search(r"admin", l, re.I)), "")
            print(f"  {rank}. {m['score']:.3f} [{url_label(m['metadata'].get('source_url')):<10}] "
                  f"chunk {m['metadata'].get('chunk_index')}: {line[:110]}")


    v = model().encode(["In your Yotpo Reviews admin, go to Integrations.",
                        "From your Yotpo Loyalty admin, go to Integrations Center."],
                       normalize_embeddings=True)
    print(f"\ncosine of the two admin sentences: {float(v[0] @ v[1]):.2f}")


def cmd_queryb():
    print(f"Query B: top_k={TOP_K_B}, cosine>={MIN_SCORE}\n")
    for esp in SELECTABLE_ESPS:
        kept = query(MECHANICS_QUERY, esp, TOP_K_B)
        desc = ", ".join(f"{x['metadata'].get('filename')}#{x['metadata'].get('chunk_index')}"
                         f"({url_label(x['metadata'].get('source_url'))})" for x in kept)
        print(f"{esp:<12}{len(kept):>2}  {desc}")


def cmd_filters():
    v = model().encode("how do I set up the integration").tolist()
    idx = index()
    base = {"esp": {"$eq": "klaviyo"}}
    def ids(extra):
        f = dict(base); f.update(extra)
        return {m["id"] for m in idx.query(vector=v, top_k=1000, filter=f)["matches"]}
    b = ids({})
    for name, extra in [("$in [loyalty,shared]", {"product": {"$in": ["loyalty", "shared"]}}),
                        ("$eq loyalty", {"product": {"$eq": "loyalty"}}),
                        ("$nin [reviews]", {"product": {"$nin": ["reviews"]}}),
                        ("$ne reviews", {"product": {"$ne": "reviews"}})]:
        got = ids(extra)
        print(f"klaviyo: {name:<24} -> {len(got):>4} of {len(b)}"
              f"  (identical set: {got == b})")


def cmd_traffic():
    """Aggregate counts only. Prints no message text."""
    import psycopg2
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    q = {
        "messages rows (length only, no text stored)": "SELECT COUNT(*) FROM messages",
        "user messages": "SELECT COUNT(*) FROM messages WHERE role='user'",
        "saved conversations": "SELECT COUNT(*) FROM conversations",
        "saved user turns with text": "SELECT COUNT(*) FROM conversation_messages WHERE role='user'",
        "  ...mentioning review vocabulary":
            "SELECT COUNT(*) FROM conversation_messages WHERE role='user' "
            "AND content ~* %s",
        "  ...mentioning loyalty vocabulary":
            "SELECT COUNT(*) FROM conversation_messages WHERE role='user' "
            "AND content ~* %s",
        "esp_documents rows": "SELECT COUNT(*) FROM esp_documents",
        "esp_documents rows with no stored content":
            "SELECT COUNT(*) FROM esp_documents WHERE content IS NULL",
    }
    params = {
        "  ...mentioning review vocabulary": (r"\m(reviews?|star rating|ratings?|ugc|reviewer)\M",),
        "  ...mentioning loyalty vocabulary": (r"\m(points?|loyalty|referrals?|vip|tiers?|rewards?|redeem)\M",),
    }
    for label, sql in q.items():
        cur.execute(sql, params.get(label))
        print(f"{label:<48}{cur.fetchone()[0]:>8}")
    cur.execute("SELECT e.name, d.crawl_status, COUNT(*), MIN(d.created_at)::date, MAX(d.created_at)::date "
                "FROM esp_documents d JOIN esps e ON e.id = d.esp_id WHERE d.content IS NULL "
                "GROUP BY 1, 2 ORDER BY 1")
    print("\nrows with no stored content (esp, status, count, first, last):", cur.fetchall())
    cur.execute("SELECT esp, COUNT(*) FROM messages WHERE role='user' GROUP BY esp ORDER BY 2 DESC")
    print("\nuser messages by esp:", dict(cur.fetchall()))
    conn.close()


if __name__ == "__main__":
    cmds = {n[4:]: f for n, f in globals().items() if n.startswith("cmd_")}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        print(__doc__); sys.exit(2)
    cmds[sys.argv[1]]()
