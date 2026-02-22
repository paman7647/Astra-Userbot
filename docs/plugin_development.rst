Plugin Development
==================

Writing a plugin is simply creating a normal Python module that imports the
framework helpers and registers one or more commands.  Plugins live in the
``commands/`` directory; the loader scans that folder at startup and executes
each module once.  If the module defines a command (using the decorator) the
metadata is stored globally and the handler function is retained for later
invocation.

Files that do not end in ``.py`` are ignored; use descriptive filenames and
avoid name collisions.  You do not need to restart the entire bot when
modifying a plugin – the ``.admin reload`` command will re-import modules and
refresh handlers in place.  However, global variables defined at import time
are not reset unless you manually clear them, so treat state accordingly.

Below is the absolute minimum structure of a plugin file:

.. code-block:: python

    # commands/sample.py
    from . import *

    @astra_command(
        name="sample",
        description="A sample command",
        usage="",
        is_public=True
    )
    async def sample_handler(client, message):
        await message.reply("This is a sample plugin.")


### The decorator

``@astra_command`` accepts the following keyword arguments:

* ``name`` – command name string (required)
* ``description`` – short text used in the help menu
* ``aliases`` – list of alternate names
* ``usage`` – textual usage hint, shown when user misuses command
* ``category`` – grouping for help menu
* ``owner_only`` – restrict to owner/sudo
* ``is_public`` – whether the command can be executed by anyone

The decorated function must be ``async`` and takes ``client`` and ``message``
as parameters.  ``client`` is the WhatsApp client instance; ``message`` is the
incoming message object.

### Handling messages

Inside your handler you can call ``extract_args(message)`` to split arguments
by whitespace.  ``smart_reply()`` sends a reply or edits the message if the bot
sent it.

Example with arguments and error handling:

.. code-block:: python

    @astra_command(name="echo", description="Echo text", usage="<text>")
    async def echo_handler(client, message):
        args = extract_args(message)
        if not args:
            return await smart_reply(message, "Usage: .echo <text>")
        await smart_reply(message, " ".join(args))


### Using async and delays

Because the bot is asynchronous you must avoid blocking operations such as
``time.sleep``.  When you need a pause between message edits use
``await asyncio.sleep(0.5)`` or, if running synchronously, import ``time`` then
call ``time.sleep`` before the edit (the main loop is not blocked by very short
sleeps).

Example multi-edit sequence:

.. code-block:: python

    async def fun_handler(client, message):
        status = await message.reply("Starting...")
        for i in range(3):
            await asyncio.sleep(0.5)
            await status.edit(f"Step {i}")


### Error handling

Wrap plugin logic in try/except and call ``report_error(client, exc, context)``
so the owner is notified.  Uncaught exceptions are logged but may silently
stop your command from finishing.

### Advanced features

Plugins can import and use any utility from ``utils/`` such as
``get_contact_name`` or ``safe_edit``.  They may also schedule background tasks
or interact with the database via the shared ``state`` object in
``utils/state.py`` (not covered here).

Refer to existing commands for concrete patterns and copy the structure when
building new functionality.

### Additional examples

**Progress indicator** – update a status message repeatedly with a delay:

.. code-block:: python

    @astra_command(name="countdown", usage="<n>")
    async def countdown(client, message):
        args = extract_args(message)
        n = int(args[0]) if args else 5
        status = await message.reply("Starting countdown...")
        for i in range(n, 0, -1):
            await asyncio.sleep(1)
            await status.edit(f"{i}...")
        await status.edit("Done!")

**External API** – fetch a brief weather report from wttr.in:

.. code-block:: python

    @astra_command(name="weather", usage="<city>")
    async def weather_cmd(client, message):
        import aiohttp
        args = extract_args(message)
        city = args[0] if args else "London"
        status = await message.reply("Fetching...")
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"https://wttr.in/{city}?format=3") as resp:
                data = await resp.text()
        await status.edit(data)

### Contribution and credits

Astra Userbot is authored by **Aman Kumar Pandey** (GitHub:
`paman7647 <https://github.com/paman7647>`_).  The entire framework is
contained in this repository; there is no separate upstream core library.

To contribute:

* Fork the repository and create a feature branch.
* Write clear commit messages and include tests or examples.
* Ensure your code follows PEP8 and runs under Python 3.10+.
* Submit a pull request; maintainers will review and merge accordingly.

Issues not addressed by existing commands should be reported via GitHub
Issues.  When a plugin throws an exception, the framework logs the traceback
and, if OWNER_ID is configured, sends the trace to the owner for diagnostics.

Thank you to all contributors and users who have helped improve Astra Userbot
since its initial release.  Your examples and bug reports make the project
stronger.
