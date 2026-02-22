Installation
============

Astra Userbot runs on Python 3.10+ and requires a WhatsApp client library to
interface with the service.  The bot itself has no external dependencies
beyond those declared in ``requirements.txt``.

Requirements
------------

* Python 3.10 or newer
* pip
* Git (for cloning the repository)
* Optionally Docker for containerised deployment

Create a virtual environment and install:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate   # or venv\Scripts\activate on Windows
    pip install -U pip
    pip install -r requirements.txt

Optionally, to build the documentation you will also need Sphinx and a
compatible theme such as ``sphinx_rtd_theme``.  Install them with:

.. code-block:: bash

    pip install sphinx sphinx_rtd_theme

This extra step is not required to run the bot itself.

The list in requirements includes packages such as ``aiohttp`` and the
underlying WhatsApp client.

Windows / macOS / Linux
-----------------------

On any Unix-like system, follow the above virtualenv steps.  On Windows you can
use WSL which provides a more predictable environment.

Docker
------

A basic Dockerfile is included in the repository.  Build and run with:

.. code-block:: bash

    docker build -t astra-userbot .
    docker run -e OWNER_WHATSAPP_ID="12345" astra-userbot

The container will behave the same as the command-line bot.

API credentials
---------------

To operate the userbot you must supply your WhatsApp API ID and API HASH.  Use
your account configuration or WhatsApp tools to obtain them, then set the
following environment variables or place them in a ``.env`` file at the
repository root:

.. code-block:: ini

    WHATSAPP_API_ID=123456
    WHATSAPP_API_HASH=abcdef0123456789

Troubleshooting
---------------

* ``ModuleNotFoundError``: make sure the virtual environment is activated.
* ``python: command not found``: install Python from the official website.
* Docker permission errors: run commands with ``sudo`` or use a user in the
  docker group.

