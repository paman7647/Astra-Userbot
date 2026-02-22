Developer Notes
================

This section targets contributors and developers who wish to understand or
extend the framework.  Before making changes, fork the repository at
https://github.com/paman7647/Astra-Userbot and open pull requests against the
``main`` branch.

* **Entry point**: ``bot.py`` – sets up logging, loads configuration, and starts
  the WhatsApp client.

* **Plugin discovery**: ``utils/plugin_utils.py`` contains helper functions to
  import and reload plugin modules, tracking handles in a global dictionary.

* **Command decorator**: ``decorators`` are defined in the core; they attach
  metadata to functions and register them in a global ``COMMANDS_METADATA``
  list.


File layout summary:

.. code-block:: text

    /bot.py
    /config.py
    /commands/*.py
    /utils/*.py
    /requirements.txt
    /Dockerfile
    /docs/  <-- documentation files

To debug a plugin, insert ``print()`` statements or use the ``logging``
module.  Exceptions in plugins are caught by wrapper code in the decorator
itself, but you can always wrap your handler in a try/except and call
``report_error``.

Naming conventions: keep plugin filenames and command names lower‑case and
underscore-separated.  Avoid collisions with Python standard library names.

The WhatsApp client stores session data on disk; treat this file as sensitive.

Pull requests should include tests for new features where applicable and
adhere to the existing code style (mostly PEP8 with 120‑column line length).

