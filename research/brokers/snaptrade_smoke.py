"""Live check that Hone's SnapTrade client works with real keys.

    python research/brokers/snaptrade_smoke.py            # check every call, then clean up
    python research/brokers/snaptrade_smoke.py --link     # make a test user + a portal link
    python research/brokers/snaptrade_smoke.py --read     # after linking: show what Hone sees
    python research/brokers/snaptrade_smoke.py --cleanup  # delete the test user (stops billing)

Uses SNAPTRADE_CLIENT_ID / SNAPTRADE_CONSUMER_KEY (or SnapTrade_ClientID /
SnapTrade_API). Never prints a secret: the --link test user's credentials
are saved to a private file outside the repo (--store, default
~/.hone_snaptrade_test.json, readable only by you).
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path

from hone.market_data.brokers import snaptrade as snap

DEFAULT_STORE = Path.home() / ".hone_snaptrade_test.json"


def _save(path: Path, user_id: str, secret: str) -> None:
    path.write_text(json.dumps({"user_id": user_id, "user_secret": secret}))
    os.chmod(path, 0o600)


def _load(path: Path) -> tuple[str, str]:
    d = json.loads(path.read_text())
    return d["user_id"], d["user_secret"]


def check(client: snap.SnapTradeClient) -> int:
    user_id = f"hone-smoke-{uuid.uuid4().hex[:12]}"
    steps, ok = [], True
    try:
        secret = client.register_user(user_id)
        steps.append("register user: ok (request signing works)")
        steps.append(f"list connections: ok ({len(client.list_connections(user_id, secret))})")
        steps.append(f"list accounts: ok ({len(client.list_accounts(user_id, secret))})")
        client.login_link(user_id, secret)
        steps.append("connection portal link: ok")
    except snap.SnapTradeError as exc:
        steps.append(f"FAILED: {exc} (status {exc.status})")
        ok = False
    finally:
        try:
            client.delete_user(user_id)
            steps.append("delete test user: ok")
        except snap.SnapTradeError as exc:
            steps.append(f"delete test user: failed ({exc})")
    print("\n".join(steps))
    return 0 if ok else 1


def link(client: snap.SnapTradeClient, store: Path) -> int:
    if store.exists():
        user_id, secret = _load(store)
        print(f"reusing test user {user_id}")
    else:
        user_id = f"hone-test-{uuid.uuid4().hex[:12]}"
        secret = client.register_user(user_id)
        _save(store, user_id, secret)
        print(f"created test user {user_id} (credentials saved to {store})")
    url = client.login_link(user_id, secret)
    print("\nOpen this link to connect a brokerage (read-only). It expires in a few minutes;")
    print("run --link again for a fresh one.\n")
    print(url)
    return 0


def read(client: snap.SnapTradeClient, store: Path) -> int:
    user_id, secret = _load(store)
    conns = client.list_connections(user_id, secret)
    print("connections:", [(c.get("brokerage") or {}).get("display_name") or c.get("name") for c in conns])
    print("disabled:", [c.get("id") for c in conns if c.get("disabled")])
    h = snap.fetch_holdings(client, user_id, secret, fresh=True)
    print("accounts:", [snap.account_label(a) for a in h.accounts])
    print(f"modelled ({len(h.holdings)}):")
    for x in h.holdings:
        print(f"  {x.symbol:<10} ${x.market_value:>12,.2f}  qty {x.qty:g}  [{', '.join(x.accounts)}]")
    print(f"skipped ({len(h.skipped)}):")
    for k in h.skipped:
        mv = f"${k.market_value:,.2f}" if k.market_value is not None else "—"
        print(f"  {k.symbol:<10} {mv:>12}  {k.reason}  [{k.account}]")
    return 0


def cleanup(client: snap.SnapTradeClient, store: Path) -> int:
    user_id, _ = _load(store)
    client.delete_user(user_id)
    store.unlink()
    print(f"deleted test user {user_id} and {store}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--link", action="store_true")
    g.add_argument("--read", action="store_true")
    g.add_argument("--cleanup", action="store_true")
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    args = ap.parse_args()
    if not snap.configured():
        print("No SnapTrade keys in the environment. Set SNAPTRADE_CLIENT_ID and "
              "SNAPTRADE_CONSUMER_KEY (or SnapTrade_ClientID / SnapTrade_API).")
        return 2
    client = snap.SnapTradeClient()
    if args.link:
        return link(client, args.store)
    if args.read:
        return read(client, args.store)
    if args.cleanup:
        return cleanup(client, args.store)
    return check(client)


if __name__ == "__main__":
    raise SystemExit(main())
