"""
Customer Service Intelligence
-----------------------------
A simple base project that analyzes customer support tickets:
  1. Sentiment scoring (lexicon based)
  2. Category detection (keyword based)
  3. Priority assignment
  4. Summary report + enriched CSV output

Usage:
    python customer_service_intelligence.py                       # uses sample_tickets.csv
    python customer_service_intelligence.py my_tickets.csv out.csv

Input CSV columns: ticket_id, customer, channel, message, response_minutes, resolved
"""

import csv
import re
import sys
from collections import Counter, defaultdict
from statistics import mean

# ---------------------------------------------------------------- lexicons
POSITIVE_WORDS = {
    "thanks", "thank", "great", "good", "excellent", "happy", "love", "perfect",
    "awesome", "helpful", "resolved", "quick", "fast", "satisfied", "appreciate",
}
NEGATIVE_WORDS = {
    "angry", "bad", "terrible", "worst", "horrible", "awful", "slow", "broken",
    "late", "delay", "delayed", "refund", "cancel", "complaint", "disappointed",
    "frustrated", "unacceptable", "useless", "error", "failed", "failure", "crash",
    "damaged", "wrong", "missing", "charged", "overcharged", "stuck",
}
NEGATIONS = {"not", "no", "never", "isn't", "wasn't", "don't", "doesn't", "didn't"}

URGENT_WORDS = {"urgent", "immediately", "asap", "emergency", "now", "legal", "lawyer", "fraud"}

CATEGORY_KEYWORDS = {
    "Billing": ["bill", "billing", "invoice", "charge", "charged", "refund", "payment", "price", "overcharged"],
    "Technical": ["error", "bug", "crash", "login", "password", "app", "website", "broken", "install", "failed"],
    "Delivery": ["delivery", "shipping", "shipment", "package", "order", "late", "delayed", "tracking", "damaged"],
    "Account": ["account", "profile", "subscription", "cancel", "upgrade", "email", "address"],
}


# ---------------------------------------------------------------- analysis
def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())


def sentiment_score(text):
    """Return score in [-1, 1]. Handles simple negation (e.g. 'not good')."""
    tokens = tokenize(text)
    score = 0
    for i, tok in enumerate(tokens):
        sign = 0
        if tok in POSITIVE_WORDS:
            sign = 1
        elif tok in NEGATIVE_WORDS:
            sign = -1
        if sign and i > 0 and tokens[i - 1] in NEGATIONS:
            sign = -sign
        score += sign
    if not tokens:
        return 0.0
    # normalise: squash by number of sentiment hits so long messages don't dominate
    hits = sum(1 for t in tokens if t in POSITIVE_WORDS or t in NEGATIVE_WORDS)
    return round(score / hits, 2) if hits else 0.0


def sentiment_label(score):
    if score > 0.2:
        return "Positive"
    if score < -0.2:
        return "Negative"
    return "Neutral"


def detect_category(text):
    tokens = set(tokenize(text))
    best, best_hits = "General", 0
    for category, words in CATEGORY_KEYWORDS.items():
        hits = len(tokens.intersection(words))
        if hits > best_hits:
            best, best_hits = category, hits
    return best


def assign_priority(score, text, response_minutes):
    tokens = set(tokenize(text))
    if tokens & URGENT_WORDS or score <= -0.6:
        return "High"
    if score < -0.2 or response_minutes > 240:
        return "Medium"
    return "Low"


def analyze(tickets):
    results = []
    for t in tickets:
        message = t["message"]
        response = float(t.get("response_minutes") or 0)
        score = sentiment_score(message)
        results.append({
            **t,
            "response_minutes": response,
            "resolved": str(t.get("resolved", "")).strip().lower() in {"yes", "true", "1"},
            "sentiment_score": score,
            "sentiment": sentiment_label(score),
            "category": detect_category(message),
            "priority": assign_priority(score, message, response),
        })
    return results


# ---------------------------------------------------------------- reporting
def build_report(results):
    total = len(results)
    if not total:
        return "No tickets to analyze."

    sentiments = Counter(r["sentiment"] for r in results)
    categories = Counter(r["category"] for r in results)
    priorities = Counter(r["priority"] for r in results)
    resolved_rate = sum(r["resolved"] for r in results) / total * 100

    by_channel = defaultdict(list)
    by_category_sent = defaultdict(list)
    for r in results:
        by_channel[r["channel"]].append(r["response_minutes"])
        by_category_sent[r["category"]].append(r["sentiment_score"])

    lines = []
    add = lines.append
    add("=" * 58)
    add("        CUSTOMER SERVICE INTELLIGENCE REPORT")
    add("=" * 58)
    add(f"Total tickets          : {total}")
    add(f"Average sentiment      : {mean(r['sentiment_score'] for r in results):+.2f}")
    add(f"Avg response time      : {mean(r['response_minutes'] for r in results):.0f} min")
    add(f"Resolution rate        : {resolved_rate:.0f}%")

    add("\nSentiment breakdown")
    for label in ("Positive", "Neutral", "Negative"):
        add(f"  {label:<9}: {sentiments[label]:>3}  ({sentiments[label] / total * 100:.0f}%)")

    add("\nTickets by category (avg sentiment)")
    for cat, n in categories.most_common():
        add(f"  {cat:<10}: {n:>3}   {mean(by_category_sent[cat]):+.2f}")

    add("\nAvg response time by channel")
    for ch, times in sorted(by_channel.items()):
        add(f"  {ch:<10}: {mean(times):.0f} min")

    add("\nPriority breakdown")
    for p in ("High", "Medium", "Low"):
        add(f"  {p:<7}: {priorities[p]}")

    add("\nTickets needing attention (High priority, unresolved)")
    urgent = [r for r in results if r["priority"] == "High" and not r["resolved"]]
    if urgent:
        for r in urgent:
            add(f"  #{r['ticket_id']} [{r['category']}] {r['customer']}: {r['message'][:60]}")
    else:
        add("  None")
    add("=" * 58)
    return "\n".join(lines)


# ---------------------------------------------------------------- I/O
def load_tickets(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_results(results, path):
    fields = ["ticket_id", "customer", "channel", "message", "response_minutes",
              "resolved", "sentiment_score", "sentiment", "category", "priority"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in fields})


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else "sample_tickets.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "analyzed_tickets.csv"

    results = analyze(load_tickets(in_path))
    print(build_report(results))
    save_results(results, out_path)
    print(f"\nEnriched data saved to {out_path}")


if __name__ == "__main__":
    main()
