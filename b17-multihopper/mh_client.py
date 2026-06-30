"""MultiHopper REST API client (devnet). Wraps create/prepare/confirm-broadcast/get/rescue/webhooks/usage."""
import uuid
import time
import requests

class MultiHopperError(Exception):
    def __init__(self, code, message, status, body=None):
        self.code = code          # e.g. "MH_039"
        self.message = message
        self.status = status      # HTTP status
        self.body = body
        super().__init__(f"{code} ({status}): {message}")

class MultiHopperClient:
    def __init__(self, base_url, api_key, timeout=60):
        self.base = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, idempotency=True):
        h = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        if idempotency:
            h["Idempotency-Key"] = str(uuid.uuid4())
        return h

    def _req(self, method, path, *, json=None, params=None, idempotency=True):
        url = f"{self.base}{path}"
        headers = self._headers(idempotency=idempotency)
        body = None
        for attempt in range(3):
            r = requests.request(method, url, json=json, params=params,
                                 headers=headers, timeout=self.timeout)
            try:
                body = r.json()
            except ValueError:
                body = {"_raw": r.text}
            if r.status_code >= 400 and r.status_code in (500, 503, 429) and attempt < 2:
                time.sleep(2)  # transient — retry with same headers (idempotency-key preserved)
                continue
            if r.status_code >= 400:
                if isinstance(body, dict):
                    err = body.get("error", {})
                    if isinstance(err, str):
                        code, message = "HTTP_ERR", err
                    elif isinstance(err, dict):
                        code = err.get("code", "HTTP_ERR")
                        message = err.get("message", r.text[:200])
                    else:
                        code, message = "HTTP_ERR", str(err)
                else:
                    code, message = "HTTP_ERR", str(body)[:300]
                raise MultiHopperError(code, message, r.status_code, body)
            return body
        raise MultiHopperError("HTTP_ERR", f"transient {r.status_code} after retries", r.status_code, body)

    # --- transfers ---
    def estimate(self, params): return self._req("POST", "/transfers/estimate", json=params)
    def create(self, params):   return self._req("POST", "/transfers", json=params)
    def prepare(self, transfer_id): return self._req("POST", f"/transfers/{transfer_id}/prepare", json={})
    def confirm_broadcast(self, transfer_id, body):
        return self._req("POST", f"/transfers/{transfer_id}/confirm-broadcast", json=body)
    def get(self, transfer_id): return self._req("GET", f"/transfers/{transfer_id}", idempotency=False)
    def list(self, params=None): return self._req("GET", "/transfers", params=params or {}, idempotency=False)
    def get_by_external(self, external_id):
        # Undocumented in llms.txt / rate-limits (finding D4)
        return self._req("GET", f"/transfers/by-external/{external_id}", idempotency=False)

    # --- recovery (finding R2: not in API index) ---
    def rescue_prepare(self, transfer_id):
        return self._req("POST", f"/transfers/{transfer_id}/rescue/prepare", json={})
    def rescue_confirm(self, transfer_id, body):
        return self._req("POST", f"/transfers/{transfer_id}/rescue/confirm", json=body)

    # --- webhooks (angle B) ---
    def register_webhook(self, body): return self._req("POST", "/webhooks", json=body)
    def list_webhooks(self): return self._req("GET", "/webhooks", idempotency=False)
    def delete_webhook(self, wid): return self._req("DELETE", f"/webhooks/{wid}", idempotency=False)

    # --- usage ---
    def usage(self): return self._req("GET", "/usage", idempotency=False)

    # --- polling helper ---
    def poll_until_terminal(self, transfer_id, interval=5, max_iter=120, logger=print):
        import time
        terminal = {"completed", "failed", "expired", "refunded"}
        for _ in range(max_iter):
            t = self.get(transfer_id)
            # response may be bare transfer or {transfer: {...}}
            tr = t.get("transfer", t) if isinstance(t, dict) else t
            status = tr.get("status")
            phase = tr.get("phase")
            progress = tr.get("progress") or {}
            last_error = tr.get("lastError")
            logger(f"[poll] id={transfer_id} status={status} phase={phase} "
                   f"hops={progress.get('hopsCompleted')}/{progress.get('hopsTotal')} "
                   f"lastError={last_error}")
            if status in terminal:
                return tr
            time.sleep(interval)
        return tr
