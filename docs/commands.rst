Command Reference
=================

Commands are defined inside plugin files using the ``@astra_command``
decorator.  Each command has a name, description, usage string and optional
aliases.  They are executed when a message begins with one of the configured
prefixes followed by the command name.

System commands
---------------

``.ping``
: Check latency between the bot and WhatsApp servers.

``.help [command]``
: Display the help menu or information for a specific command.

``.admin <action>``
: Group administration actions: kick, add, promote, demote, tagall.

``.restart`` / ``.shutdown``
: Restart or stop the bot process (owner only).

``.update``
: Pull the latest code from git and restart.

``.reload``
: Hot-reload plugins without restarting the process.

Utility commands
----------------

``.wiki <query>``
: Search Wikipedia and return a summary.

``.translate [lang] <text>``
: Translate a message into a target language.

``.define <word>``
: Look up definitions via the Free Dictionary API.

``.weather <city>``
: Get current weather for a city using wttr.in.

``.calc <expression>``
: Evaluate a simple arithmetic expression.

Media commands
--------------

``.youtube <url> [video|audio]``
: Download media from YouTube.

``.spotify <query>``
: Search and retrieve audio from Spotify via yt-dlp.

``.instagram <url>``
: Download Instagram posts/reels.

``.twitter <url>``
: Download Twitter/X videos.

``.pinterest <url>``
: Download Pinterest media.

Fun commands
------------

``.meme`` / ``.dmeme``
: Fetch a random meme from Reddit (SFW / NSFW).

``.hack <target>``
: Play a fake hacking animation.

``.truth <truth|dare>``
: Truth or dare prompts.

``.joke``
: Retrieve a random joke.

``.mathquiz``
: Generate a simple arithmetic quiz.

Administration & owner commands
-------------------------------

``.setname <new_name>`` – change profile name.

``.bio <text>`` – update "about" text.

``.status <text/reply>`` – post a status message.

``.setpfp`` / ``.setgpic`` – update profile or group picture.

``.privacy [category value]`` – view or change privacy settings.

``.sudo <add|rem> [user]`` – grant or revoke sudo rights.

``.pmpermit <on|off|approve|deny>`` – manage private message permits.

``.setprefix <new_prefix>`` – change command prefix.

``.mute <on|off>`` – toggle group command mute.

Other commands are scattered through the ``commands`` folder; consult this
reference when you need details.  Aliases and advanced usage are provided in
the docstrings above each handler.
