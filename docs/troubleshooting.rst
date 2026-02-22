Troubleshooting
===============

**API errors**

* "Invalid API credentials" – check your WHATSAPP_API_ID and HASH.
* "Flood wait" – slow down or wait for the indicated number of seconds.

**Session issues**

* Session not starting: delete ``session.session`` file and re-login.
* QR code not appearing: ensure terminal supports images or copy URL into a browser.

**Plugin crashes**

* Syntax error: see log output; correct the Python code and reload.
* Remote API failing: add try/except and notify owner.

**Missing modules**

* ``ModuleNotFoundError: aiohttp`` – re-install requirements.
* Wrong Python version – use 3.10+.

**Docker network**

* Cannot access external URL – check container internet connectivity.

**General**

* ``Permission denied`` – run with appropriate user privileges.
* ``Too many requests`` – respect rate limits, add sleeps.
