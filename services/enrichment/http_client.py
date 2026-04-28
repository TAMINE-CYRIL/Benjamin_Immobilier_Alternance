import json
import os
import ssl
import urllib.parse
import urllib.request
from urllib.error import URLError

try:
    import certifi
except ImportError:
    certifi = None


class HttpClientError(RuntimeError):
    pass


class JsonHttpClient:
    def __init__(self, timeout=20, ssl_verify=None):
        self.timeout = timeout
        self.ssl_verify = ssl_verify if ssl_verify is not None else os.getenv("ENRICHMENT_SSL_VERIFY", "true") != "false"

    def _ssl_context(self, verify=None):
        should_verify = self.ssl_verify if verify is None else verify
        if not should_verify:
            return ssl._create_unverified_context()
        if certifi:
            return ssl.create_default_context(cafile=certifi.where())
        return ssl.create_default_context()

    def get_json(self, url, params=None):
        query = urllib.parse.urlencode(params or {})
        full_url = f"{url}?{query}" if query else url
        request = urllib.request.Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "BenjaminImmobilier-Enrichment/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=self._ssl_context()) as response:
                body = response.read().decode("utf-8")
        except URLError as exc:
            if self.ssl_verify and "CERTIFICATE_VERIFY_FAILED" in str(exc):
                with urllib.request.urlopen(request, timeout=self.timeout, context=self._ssl_context(verify=False)) as response:
                    body = response.read().decode("utf-8")
            else:
                raise HttpClientError(str(exc)) from exc
        except Exception as exc:
            raise HttpClientError(str(exc)) from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise HttpClientError(f"Invalid JSON response from {url}") from exc
