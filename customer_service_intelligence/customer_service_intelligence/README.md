# Customer Service Intelligence

A simple base project that turns raw customer support tickets into actionable insights.

## Features
- **Sentiment analysis** – lexicon-based score from -1 to +1 with simple negation handling
- **Category detection** – Billing, Technical, Delivery, Account, General
- **Priority assignment** – High / Medium / Low based on sentiment, urgent keywords and response time
- **Summary report** – sentiment mix, category stats, response time per channel, unresolved high-priority tickets
- **CSV export** – enriched data saved to `analyzed_tickets.csv`

## Run
Requires Python 3.8+ (no external packages).

```bash
python customer_service_intelligence.py
# or with your own data
python customer_service_intelligence.py my_tickets.csv output.csv
```

## Input format
CSV with columns: `ticket_id, customer, channel, message, response_minutes, resolved`

## Ideas for extending
- Swap the lexicon for a model (e.g. VADER, TextBlob, or an LLM API)
- Add a Streamlit or Flask dashboard
- Track trends over time and SLA breaches
- Auto-suggest reply templates per category
