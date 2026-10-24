# Salsmart: Israeli grocery prices for apps and AI agents

Start with real Hebrew/barcode search and branch prices in ILS. This kit needs
Python 3.9+ and **no installed packages**. It includes MCP configuration for AI
clients and a command-line JSONL/CSV exporter. No account is needed for free use.

- [Try the data](https://salsmart.com/developers)
- [Connect an AI agent](https://salsmart.com/connect)
- [Freshness and branch coverage](https://salsmart.com/api/data-status)
- [API documentation](https://salsmart.com/agents.md)
- [Prepaid REST plan](https://salsmart.com/api-plan?source=developers&intent=automation)

## חיפוש ראשון בחינם — free first search

Extract the ZIP, open a terminal in the extracted folder, and run:

```sh
python3 salsmart.py search -q 'חלב תנובה'
python3 salsmart.py search -q '7290000051352' --format csv --output milk.csv
python3 salsmart.py status
```

CSV has one row per returned branch offer, including source/fetch timestamps.
Files are created only if the destination does not exist. Spreadsheet formula
prefixes in third-party text are escaped. Barcodes are identifiers; configure
their spreadsheet column as text to preserve leading zeroes. JSONL preserves the
original JSON fields. Neither format is a complete catalog download.

For several product queries, create `queries.txt` (UTF-8, one name or barcode per
line, up to 100 queries), then run:

```sh
python3 salsmart.py search --query-file queries.txt --format csv --output prices.csv
```

The default is always **free**, even when an API key is present in your
environment. Free search returns up to 20 products per query and shares a limit
of 60 admitted searches/minute and 500/day UTC per network address with MCP.
The client stops on errors, including 429, and reports a numeric Retry-After
when supplied. It never automatically switches to a paid request.

## שימוש ב־REST בתשלום — optional prepaid integration

Use this when your application needs up to 100 matching products, its own credit
balance, and paid-search replay protection. The underlying data is the same as
free search. Public MCP and basic site search remain free.

The current plan is a one-time **ILS 19 for 1,000 successful-search credits**,
without automatic renewal. Purchase and activate at
[salsmart.com/api-plan](https://salsmart.com/api-plan?source=developers&intent=automation).
Every successful paid search costs one credit, **including zero results**.
Usage checks and authentication/validation/server errors consume no credit.

Store your key in your server's secret manager or `SALSMART_API_KEY` environment
variable. Do not put it in source control, a browser, an AI prompt or a command
argument. The script only sends it directly to `https://salsmart.com` and refuses
redirects. It never buys credits, renews a plan or changes your account.

```sh
# SALSMART_API_KEY is already set securely in your environment.
python3 salsmart.py usage
python3 salsmart.py search --paid --run-id my-app-search-0001 -q 'קפה' --limit 100
```

The explicit `--paid` flag authorizes credit use. A single-query invocation has a
default ceiling of one credit. For a batch of at most 10 paid searches:

```sh
python3 salsmart.py search --paid --run-id report-2026-10-24 \
  --max-credits 10 --query-file queries.txt --limit 100 --output report.jsonl
```

Use a **new run ID for each new batch**. If a timeout leaves completion uncertain,
rerun with the **same run ID, ordered query list, and limit** within 24 hours;
each position keeps its idempotency key and an already completed search is not
charged again. Never add, remove or reorder queries or change the limit during
a retry. Changed parameters at an already completed position produce a conflict;
new or previously uncompleted positions can still consume credits. `--max-credits`
limits this invocation, not a persistent budget across separate runs. After 24
hours, expired IDs cannot replay; do not create a new ID unless you intend a new
paid search. Partial batch output is retained. Use a new output filename on a
retry; do not append blindly or count duplicate rows as additional observations.

## AI clients

See `MCP-README.md` and the included client-specific configuration files.
Endpoint: `https://salsmart.com/mcp`, Streamable HTTP, no authentication.
Tools: `search_products` and `get_data_status`, both free and read-only.
Marketplace approval is separate from direct connection support.

## Data limits

Coverage is **selected Israeli supermarket branches**, not every store or a
guarantee of the lowest price in Israel. A price does not confirm live inventory.
`update_date` is the retailer price-change date; `fetched_at` is the successful
source fetch time. Preserve nulls and old dates. Check `status` before describing
results as current. API data and prebuilt product pages can differ.

This kit makes only the requested API calls. It contains no analytics beacon or
telemetry. Normal Salsmart rate limits and server processing still apply; see
[privacy](https://salsmart.com/privacy). Support: [salsmart.com/support](https://salsmart.com/support).

The client code/configuration in this kit is MIT licensed; grocery source data
and API access remain subject to the source and service's applicable terms.
