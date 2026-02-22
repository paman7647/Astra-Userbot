Getting Started
===============

After installing dependencies, creating a virtual environment and setting
up your configuration, start the bot with:

.. code-block:: bash

    python bot.py

On first run the library will prompt you to scan a QR code to authenticate the
WhatsApp account.  Follow the on-screen instructions from the console.

## Basic operations

* **Restarting** – send a ``SIGTERM`` or press Ctrl-C; the process will exit.
* **Uptime** – use the ``.platform`` or ``.stats`` command to see running time.
* **Updating** – pull the latest code from git and restart the bot.
* **Plugins** – the ``/commands`` directory holds Python files; the
  ``.admin reload`` command refreshes them without restarting.

Example session (Unix shell):

.. code-block:: bash

    $ python bot.py
    [2026-02-22 12:00:00] Astra starting...
    Scan the QR code displayed on WhatsApp mobile.

    # After login
    > .ping
    🏓 Pong! Latency: 45ms

    > .help
    ... (menu shown)

    > .admin reload meme
    ✅ Plugin `meme` reloaded successfully!


Restarting the bot is as simple as stopping and starting the process.  State is
persisted in a local SQLite database by default; plugins may also write to the
same state object.
