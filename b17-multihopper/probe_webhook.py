"""Angle B: register a webhook (via webhook.site public URL), store secret.
Next step: create a transfer to trigger events, then read webhook.site for payloads + x-multihopper-signature."""
import sys, json
import config
from config import assert_test_env
from mh_client import MultiHopperClient, MultiHopperError

assert_test_env()
client = MultiHopperClient(config.API_BASE, config.API_KEY)

ws_uuid = sys.argv[1] if len(sys.argv) > 1 else None
if not ws_uuid:
    sys.exit("usage: probe_webhook.py <webhook.site-uuid> [event1 event2 ...]")
url = f"https://webhook.site/{ws_uuid}"
events = sys.argv[2:] if len(sys.argv) > 2 else None

body = {"url": url}
if events:
    body["events"] = events
print(f"[register] url={url} events={events}")
try:
    r = client.register_webhook(body)
    print(json.dumps(r, indent=2, default=str))
    secret = r.get("secret")
    wh_id = r.get("id")
    print(f"\nSECRET: {secret}\nWebhook ID: {wh_id}")
except MultiHopperError as e:
    print(f"REGISTER ERROR {e.code} ({e.status}): {e.message}\nbody: {json.dumps(e.body, default=str)[:500]}")
    sys.exit(1)

import os
ev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidence", "webhook_registered.json")
with open(ev, "w") as f:
    json.dump({"uuid": ws_uuid, "url": url, "secret": secret, "id": wh_id, "events": events}, f, indent=2)
print("\nSaved evidence/webhook_registered.json")
print("Next: python probe_trigger_events.py  # create transfer to fire events")
print("Then: read https://webhook.site/<uuid> (or via API) for payloads + x-multihopper-signature header")
