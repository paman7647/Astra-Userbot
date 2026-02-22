Frequently Asked Questions
==========================

* **Is this safe?**
  Running a userbot uses your personal account.  Use caution, avoid spamming
  and keep backups.  WhatsApp may ban accounts for automated activity.

* **Can Telegram restrict userbots?**
  This is a WhatsApp userbot, not Telegram.

* **How do I run it 24/7?**
  Use a VPS or Raspberry Pi and a process supervisor like systemd.

* **How do I add my own plugins?**
  Create a new Python file in ``commands/`` with a command handler, then run
  ``.admin reload``.

* **How do I update the bot?**
  ``git pull`` and restart.  Use ``.update`` command for convenience.

* **Why are edits slow?**
  WhatsApp rate‑limits editing; include short sleeps between multiple edits.

* **Why do I get flood waits?**
  Sending too many messages quickly triggers server throttling.  Respect
  delays.
