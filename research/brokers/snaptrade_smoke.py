"""Live check that Hone's SnapTrade client works with real keys.

    python research/brokers/snaptrade_smoke.py          # read-only checks
    python research/brokers/snaptrade_smoke.py --link   # also print a portal link

Uses SNAPTRADE_CLIENT_ID / SNAPTRADE_CONSUMER_KEY (or SnapTrade_ClientID /
SnapTrade_API). Creates a throwaway SnapTrade user, checks every call Hone
makes, and deletes the user at the end so nothing is left behind or
billed. Prints no secrets.
"""

from __future__ import annotations

import argparse
import sys
import uuid

from hone.market_data.brokers import snaptrade as snap


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--link", action="store_true",
                    help="print a Connection Portal link and keep the test user "
                         "(link a broker, then rerun with --user to read it)")
    ap.add_argument("--user", help="existing test user id (with --secret) to read holdings")
    ap.add_argument("--secret", help="that user's secret")
    args = ap.parse_args()

    if not snap.configured():
        print("No SnapTrade keys in the environment. Set SNAPTRADE_CLIENT_ID and "
              "SNAPTRADE_CONSUMER_KEY (or SnapTrade_ClientID / SnapTrade_API).")
        return 2
    client = snap.SnapTradeClient()

    if args.user and args.secret:
        conns = client.list_connections(args.user, args.secret)
        print(f"connections: {[c.get('brokerage', {}).get('display_name') for c in conns]}")
        h = snap.fetch_holdings(client, args.user, args.secret, fresh=True)
        print(f"accounts: {[snap.account_label(a) for a in h.accounts]}")
        print(f"modelled: {[(x.symbol, round(x.market_value)) for x in h.holdings]}")
        print(f"skipped: {[(k.symbol, k.reason) for k in h.skipped]}")
        return 0

    user_id = f"hone-smoke-{uuid.uuid4().hex[:12]}"
    steps = []
    try:
        secret = client.register_user(user_id)
        steps.append("register user: ok (request signing works)")
        steps.append(f"list connections: ok ({len(client.list_connections(user_id, secret))})")
        steps.append(f"list accounts: ok ({len(client.list_accounts(user_id, secret))})")
        url = client.login_link(user_id, secret)
        steps.append("connection portal link: ok")
        if args.link:
            print("\n".join(steps))
            print(f"\nOpen this to link a broker (read-only):\n{url}\n")
            print(f"Then: python {sys.argv[0]} --user {user_id} --secret <printed below>")
            print(f"secret: {secret}")
            return 0
    except snap.SnapTradeError as exc:
        steps.append(f"FAILED: {exc} (status {exc.status})")
        print("\n".join(steps))
        return 1
    finally:
        if not args.link:
            try:
                client.delete_user(user_id)
                steps.append("delete test user: ok")
            except snap.SnapTradeError as exc:
                steps.append(f"delete test user: failed ({exc})")
    print("\n".join(steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
