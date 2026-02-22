Best Practices
==============

Keep plugins small and focused – a single command per file is an easy rule.
Avoid blocking operations such as heavy computations or long file I/O; use
``await asyncio.to_thread()`` if you must run something outside the event loop.

When editing messages repeatedly (progress bars, animations) insert short
pauses:

.. code-block:: python

    await asyncio.sleep(0.5)
    await status.edit("next step")

Catch exceptions within each handler and call ``report_error`` to notify the
owner rather than letting the error propagate silently.

Do not hardcode secret values in plugins; read from ``config`` or environment
variables.

Use descriptive command names and provide clear ``usage`` strings – they appear
in the help menu.

Avoid repeating logic across plugins; factor common helpers into ``utils/``.

When writing asynchronous loops that iterate over messages or external APIs,
respect service rate limits and provide graceful fallback when networks fail.

Document any new commands you add by editing ``commands.rst`` accordingly; this
keeps the reference in sync.

