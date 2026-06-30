"""Angle B: verify webhook HMAC signatures.
W5: secret has NO whsec_ prefix (docs say it does).
W6: signature header is x-mh-signature (docs say x-multihopper-signature).
W1: HMAC over raw body (content) vs canonical JSON.
W2: timingSafeEqual without length-check -> RangeError on length mismatch.
W3: payload has no eventId/dedupe field."""
import sys, json, hmac, hashlib, requests

WH_UUID = "a772b5f5-a1d7-44dd-91a1-c71f1d2a6d33"
WH_URL = f"https://webhook.site/token/{WH_UUID}/requests"
SECRET = "b2d9430a95fd6a36cbccc018957d8641549eb666115d9bb5d78d7d800801be95"  # NO whsec_ prefix (W5)

r = requests.get(WH_URL, params={"_limit": "20"}, timeout=30)
data = r.json().get("data", [])
print(f"webhook.site requests: {len(data)}")
if not data:
    sys.exit(0)

for i, req in enumerate(data[:15]):
    body = req.get("content", "") or ""
    headers = req.get("headers", {}) or {}
    event = (headers.get("x-mh-event") or ["?"])[0]
    sig = (headers.get("x-mh-signature") or [None])[0]
    print(f"\n--- request {i}: event={event} ---")
    print(f"body[:200]: {body[:200]}")
    print(f"x-mh-signature: {sig}")
    if not sig:
        print("NO signature -> webhooks unsigned (separate finding)")
        continue
    if body:
        expected_raw = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        print(f"HMAC(raw body)      = {expected_raw}")
        print(f"match raw body      = {hmac.compare_digest(expected_raw, sig)}")
        try:
            parsed = json.loads(body)
            canonical = json.dumps(parsed, separators=(',', ':'), sort_keys=True)
            expected_c = hmac.new(SECRET.encode(), canonical.encode(), hashlib.sha256).hexdigest()
            print(f"HMAC(canonical json)= {expected_c}")
            print(f"match canonical     = {hmac.compare_digest(expected_c, sig)}")
            print(f"payload keys        = {list(parsed.keys())}  (eventId? {'eventId' in parsed})")
        except Exception as e:
            print(f"canonical parse: {e}")
        a, b = sig.encode(), expected_raw.encode()
        if len(a) != len(b):
            print(f"W2: length mismatch ({len(a)} vs {len(b)}) -> Node timingSafeEqual THROWS RangeError")
        else:
            print(f"W2: lengths equal -> timingSafeEqual ok")
