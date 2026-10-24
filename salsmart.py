#!/usr/bin/env python3
"""Salsmart JSONL/CSV client. Python 3.9+, standard library only."""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://salsmart.com"
CSV_FIELDS = ["query", "barcode", "name", "manufacturer", "price_ils",
              "chain_id", "chain_name", "store_id", "store_name", "store_city",
              "source_url", "source_published_at", "fetched_at", "update_date"]


class ClientError(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    # Never forward an API key or query to a different destination.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(path, key=None, request_id=None, opener=None):
    headers = {"Accept": "application/json", "User-Agent": "salsmart-starter/1.0"}
    if key:
        headers["Authorization"] = "Bearer " + key
    if request_id:
        headers["Idempotency-Key"] = request_id
    request = Request(ORIGIN + path, headers=headers)
    try:
        with (opener or build_opener(NoRedirects())).open(request, timeout=30) as response:
            raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ClientError("Response too large; retry with a smaller limit.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ClientError("Unexpected response shape.")
            return result
    except HTTPError as error:
        hints = {
            400: "Invalid query, limit or request ID.",
            401: "API key is invalid or inactive.",
            402: "Credits exhausted. Manage your prepaid pack at https://salsmart.com/api-plan.",
            409: "Request ID conflict or expired 24-hour replay window; do not blindly create a new paid request.",
            429: "Free quota reached. Wait for the server's Retry-After interval; free access remains available after reset.",
            503: "Temporarily unavailable. For paid search, retry the SAME run ID and parameters.",
        }
        retry_after = error.headers.get("Retry-After", "") if error.headers else ""
        wait = f" Retry-After: {retry_after} seconds." if re.fullmatch(r"[0-9]{1,8}", retry_after) else ""
        raise ClientError(f"HTTP {error.code}: {hints.get(error.code, 'Request failed; no automatic retry.')}" + wait) from None
    except (URLError, TimeoutError, OSError):
        raise ClientError("Network failure. A paid request may have completed: retry the SAME run ID and parameters within 24 hours.") from None
    except (ValueError, UnicodeError):
        raise ClientError("Server did not return valid JSON.") from None


def paid_request_id(run_id, index):
    # The same batch position always has the same key. Changed parameters must
    # reach the server's conflict guard rather than silently charge a new search.
    digest = hashlib.sha256((run_id + ":" + str(index)).encode("utf-8")).hexdigest()
    return "starter-" + digest


def csv_cell(value):
    if value is None:
        return ""
    text = str(value)
    # Exported names/provenance are third-party data, never spreadsheet formulas.
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def csv_rows(result):
    for product in result.get("products", []):
        for offer in product.get("offers", []):
            row = {"query": result.get("query"), "barcode": product.get("barcode"),
                   "name": product.get("name"), "manufacturer": product.get("manufacturer"),
                   "price_ils": offer.get("price")}
            for field in CSV_FIELDS[5:]:
                row[field] = offer.get(field)
            yield {field: csv_cell(row.get(field)) for field in CSV_FIELDS}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["search", "usage", "status"])
    p.add_argument("-q", "--query", action="append", default=[], help="Repeat for multiple queries (maximum 100).")
    p.add_argument("--query-file", help="UTF-8 file, one query per line, maximum 100 queries.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")
    p.add_argument("--output", help="Create a NEW output file; existing files are never overwritten.")
    p.add_argument("--paid", action="store_true", help="Use prepaid credits; key from SALSMART_API_KEY only.")
    p.add_argument("--run-id", help="Required for paid search. Reuse for retries of the identical batch within 24 hours.")
    p.add_argument("--max-credits", type=int, default=1, help="Paid batch cost ceiling (default 1). Each successful search, even empty, costs 1.")
    return p


def main(argv=None, request_fn=request_json):
    p = parser()
    args = p.parse_args(argv)
    key = os.environ.get("SALSMART_API_KEY", "")
    if args.command == "usage" or args.paid:
        if not re.fullmatch(r"sk_salsmart_live_[A-Za-z0-9_-]{43}", key):
            p.error("Set SALSMART_API_KEY to your private live key. Never pass it as a command argument.")
    if args.command != "search":
        if args.query or args.query_file or args.paid or args.run_id or args.format != "jsonl":
            p.error("usage/status accept only --output. usage is authenticated and costs no credit.")
        result = request_fn("/api/v1/usage" if args.command == "usage" else "/api/data-status",
                            key if args.command == "usage" else None)
        text = json.dumps(result, ensure_ascii=False) + "\n"
        if args.output:
            with open(args.output, "x", encoding="utf-8") as output:
                output.write(text)
        else:
            sys.stdout.write(text)
        return
    queries = list(args.query)
    if args.query_file:
        with open(args.query_file, encoding="utf-8-sig") as query_file:
            # Bound input before making any network request.
            for line in query_file:
                if line.strip():
                    queries.append(line.strip())
                if len(queries) > 100:
                    p.error("Maximum 100 queries per batch.")
    queries = [query.strip() for query in queries]
    if not 1 <= len(queries) <= 100 or any(not 2 <= len(query) <= 100 for query in queries):
        p.error("Provide 1–100 queries, each 2–100 characters.")
    if not 1 <= args.limit <= (100 if args.paid else 20):
        p.error("limit must be 1–20 free, or 1–100 with --paid.")
    if args.paid:
        if not args.run_id or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", args.run_id):
            p.error("Paid search requires --run-id (8–80 letters/digits/_/-). Reuse it only for the same batch retry.")
        if not 1 <= args.max_credits <= 100 or len(queries) > args.max_credits:
            p.error("Batch exceeds --max-credits. No requests sent.")
        print(f"Paid batch: at most {len(queries)} credits; run ID {args.run_id}. Keep it for safe retries.", file=sys.stderr)
    elif args.run_id:
        p.error("--run-id applies only to --paid search.")
    output = open(args.output, "x", encoding="utf-8-sig" if args.format == "csv" else "utf-8", newline="") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS) if args.format == "csv" else None
        if writer:
            writer.writeheader()
        for index, query in enumerate(queries):
            path = "/api/v1/search" if args.paid else "/api/product-search"
            result = request_fn(path + "?" + urlencode({"q": query, "limit": args.limit}),
                                key if args.paid else None,
                                paid_request_id(args.run_id, index) if args.paid else None)
            if not isinstance(result.get("products"), list):
                raise ClientError("Unexpected search response. Keep the same run ID for any paid retry.")
            if writer:
                writer.writerows(csv_rows(result))
            else:
                output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()
    finally:
        if output is not sys.stdout:
            output.close()


if __name__ == "__main__":
    try:
        main()
    except (ClientError, OSError) as error:
        print(f"Salsmart: {error}", file=sys.stderr)
        sys.exit(1)
