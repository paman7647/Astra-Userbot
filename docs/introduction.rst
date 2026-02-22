Introduction
============

A userbot is a piece of code that logs in to a WhatsApp account and acts like a
normal user: it reads incoming messages, it can send replies, and it can perform
any task that a human could type.

Astra Userbot is an open‑source Python framework that wraps a WhatsApp client
library and exposes a lightweight plugin system.  Developers may drop new
commands into the ``commands/`` directory or configure the bot behaviour via
environment variables.  The project is appropriate for hobbyists, community
group administrators, or anyone who wants a customizable automation layer on
their personal account.

The code and issue tracker live on GitHub <https://github.com/paman7647/Astra-Userbot>.
Contributions are welcome; please read the developer notes before submitting
a pull request.

*Typical use cases*

* Automating repetitive replies or group administration.
* Fetching information (weather, wiki summaries, definitions) via commands.
* Downloading media from social services within the chat.
* Writing small games or fun utilities (meme fetcher, hack simulator).

The repository is organised as a flat Python package; main code lives in the
root and commands live in ``commands/``.  The core includes a decorator,
configuration helper and plugin loader; most logic is implemented as simple
async functions.
