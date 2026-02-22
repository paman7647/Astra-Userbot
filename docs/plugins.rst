Plugin System
=============

Plugins are Python files located in the ``commands/`` directory.  At startup the
bot scans this directory and imports every ``*.py`` file; each file may
register one or more commands via the ``@astra_command`` decorator.

A plugin file is simply a normal Python module.  For example:

.. code-block:: python

    # commands/hello.py
    from . import *

    @astra_command(
        name="hello",
        description="Say hello.",
        usage="",
        is_public=True
    )
    async def hello_handler(client, message):
        await message.reply("Hello!")


## Enabling and disabling

Plugins are enabled by virtue of being present in the directory.  To disable
a plugin, remove or rename the file and run ``.admin reload``.  There is no
built-in runtime switch; a disabled plugin will not be imported on restart.

Errors during plugin load are logged to the console and sent to the owner via
``report_error`` helper.  A syntax error in a single plugin will not stop the
entire bot but will prevent that plugin from registering its commands.

### Order and overrides

The loading order is alphanumeric; if two plugins register the same command name
the latter will overwrite the former.  Avoid duplicate command names by
designing clear prefixes or categories.

### Updating plugins

Edit the file in place and then run:

.. code-block:: bash

    python bot.py --reload   # or .admin reload from within WhatsApp

This will import the updated code and rebind handlers.  Some state may persist
in global variables unless explicitly cleared.


