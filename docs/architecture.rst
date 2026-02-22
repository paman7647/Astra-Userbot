Architecture
============

Astra Userbot is structured around a single event loop and an underlying
WhatsApp client library (imported at runtime).  When a new message arrives the
client library emits an event that is handled by ``bot.py``.  The message
text is inspected for a command prefix; if present the name is looked up in the
registry populated by ``@astra_command`` decorators during plugin import.

Commands are simple async functions that receive the ``client`` object and the
``message``.  They may call ``await message.reply()`` or ``await status.edit()``
for interaction.  The ``smart_reply`` helper abstracts reply vs edit based on
whether the message was sent by the bot.

Plugins are standard Python modules loaded from the ``commands`` folder.  A
plugin file can register multiple commands; its top-level code is executed once
at import time.

Configuration is handled by ``config.py`` which reads environment variables.
The ``state`` utility provides a simple dictionary-backed persistence layer
(using SQLite or MongoDB).

Message editing is asynchronous.  To avoid hitting the WhatsApp edit rate
limit the code often pauses half a second between consecutive edits.  This is
handled manually in many of the example commands.

Logging uses Python's ``logging`` module; errors within command handlers are
caught and reported back to the owner via ``report_error``.

The project layout:

.. code-block:: text

    /bot.py              # entry point
    /config.py           # configuration container
    /commands/           # plugin modules
    /utils/              # helper functions and state management

All interaction with the WhatsApp API is performed through the client object
passed to handlers; the core framework itself is minimal and acts mostly as a
dispatcher and environment for plugins.
