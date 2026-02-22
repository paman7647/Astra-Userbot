Configuration
=============

Astra uses a single Python module ``config.py`` to manage all options.  It
loads environment variables using ``python-dotenv`` when a ``.env`` file is
found in the project root.  Values are cast to the appropriate type and
accessible via the ``config`` object imported from ``config``.

On first run create a ``.env`` file with the required values, for example:

.. code-block:: ini

    # bot identity
    OWNER_WHATSAPP_ID=910000000000
    BOT_NAME=Astra Userbot

    # WhatsApp API credentials
    WHATSAPP_API_ID=123456
    WHATSAPP_API_HASH=abcdef0123456789

    # optional feature toggles
    ENABLE_YOUTUBE=true
    ENABLE_INSTAGRAM=false

All secrets should remain private; do not commit ``.env`` to git.  For
distributed deployments you can set the same variables in the system
environment or orchestration tooling.

Required keys
-------------

* ``OWNER_WHATSAPP_ID`` or ``BOT_OWNER_ID`` – the numeric JID of the bot owner.
* ``WHATSAPP_API_ID`` and ``WHATSAPP_API_HASH`` – credentials obtained from
  the WhatsApp developer portal.

Optional settings
-----------------

* ``COMMAND_PREFIX`` – default ".".  Multiple prefixes are supported.
* ``ENABLE_YOUTUBE``/``ENABLE_INSTAGRAM`` – feature flags, true by default.
* ``MAX_FILE_SIZE_MB`` – controls upload limits.  Default 2048.
* ``GEMINI_API_KEY`` – key for the AI chat command.

Example ``.env``

.. code-block:: ini

    OWNER_WHATSAPP_ID=910000000000
    COMMAND_PREFIX=.
    ENABLE_PM_PROTECTION=false
    GEMINI_API_KEY=abc123

Secrets should never be committed to version control.  Keep ``.env`` in
``.gitignore`` or use system environment variables.

Logging
-------

The bot uses the standard ``logging`` module.  Control verbosity by setting
``LOGLEVEL`` in the environment (e.g. ``DEBUG`` or ``INFO``).  Logs are written
to the console and can be redirected to a file using shell redirection when
starting the bot.

Defaults are sensible; you only need to modify config for API keys or
environment-specific flags.
