Examples
========

The following snippets demonstrate common workflows and utilities.

Auto-reply to keyword:

.. code-block:: python

    from . import *

    @astra_command(name="hello", description="Responds to hi")
    async def hello_handler(client, message):
        if message.body.lower().startswith("hi"):
            await message.reply("Hello there!")


Delete old messages tool:

.. code-block:: python

    import time
    from . import *

    @astra_command(name="clean", description="Remove messages older than N seconds")
    async def clean_handler(client, message):
        args = extract_args(message)
        seconds = int(args[0]) if args else 3600
        info = await client.chat.get_info(message.chat_id)
        # hypothetical API to iterate messages
        for msg in await client.chat.fetch_messages(message.chat_id, limit=100):
            if time.time() - msg.timestamp > seconds:
                await msg.delete()


Download file and send back:

.. code-block:: python

    import aiohttp
    from . import *

    @astra_command(name="getfile")
    async def getfile_handler(client, message):
        url = extract_args(message)[0]
        async with aiohttp.ClientSession() as sess:
            r = await sess.get(url)
            data = await r.read()
        await client.send_document(message.chat_id, data, filename="download.bin")


These examples are based on real behaviour of the core library.  They can be
extended with error handling or progress reporting as needed.
