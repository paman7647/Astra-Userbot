# Changelog

All notable changes to the **Astra-Userbot** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1b7] - 2026-02-21
### Added
- **Engine Sync (v0.0.2b7)**: Full integration with the latest Astra Engine, including the new 3-stage history retrieval strategy.
- **Improved History Command**: The `.history` and `.fetch` commands now support anchorless execution, defaulting to the latest 10 messages.
- **Enhanced Debug Visibility**: Bridge logs are now streamed directly to the bot console at INFO level, making it easier to track fetch operations and engine decisions.
- **Robust Purge Logic**: Improved multi-message deletion reliability during high-latency scenarios.
### Fixed
- **History Command Crash**: Resolved a `TypeError` when calling `.history` without replying to a message.
- **Fetch Count Consistency**: Fixed an issue where `.fetch` would sometimes return fewer messages than requested.

## [0.0.1b] - 2026-02-20

Welcome to the initial public beta release of the **Astra-Userbot**.

This is a powerful, modular WhatsApp Userbot framework built on top of the ultra-fast asynchronous `astra-engine`.

### Initial Features

**Core Framework Integration**
- Fully utilizes `astra-engine` for anti-ban asynchronous message processing, media handling, and headless browser session management.
- Built-in SQLite local storage to handle bot state, settings, afk flags, and user restrictions.
- Easy-to-extend architecture. Every `.py` file inside the `commands/` directory is automatically loaded as a modular plugin.

**Artificial Intelligence**
- Out-of-the-box advanced interaction with Google's `gemini-3-flash-preview` model via `.ai`, `.chat`, or `.ask`.

**Media & Download Suite**
- Robust media downloading pipeline built on top of a Node.js JS bridge and `yt-dlp`.
- **YouTube Support**: Download videos directly via `.yt` or pure audio using `.song`.
- **Instagram & Socials**: Extract high-quality media from Instagram using `.ig` / `.reel`, Twitter/X via `.twitter`, and Pinterest using `.pinterest`.
- **Spotify**: Download high-quality tracks directly using `.spotify`.

**Moderation & Group Security**
- Advanced multi-level user permissions involving strict owner filters and sudo privileges (`.sudo`).
- PM Protection System: Automatic warnings to mitigate spam and unwanted personal messages (`.pmpermit`).
- **Group Management**: Commands to efficiently manage group dynamics including `.mute`, `.spam`, and dynamic message purging (`.del`, `.purge`).

**Utility & Productivity Tools**
- **Notes System**: Save, fetch, and delete custom text payloads directly in chat using `.notes`.
- **Translations & Lookups**: Built-in translation commands (`.translate`), Wikipedia lookups (`.wiki`), and dictionary definition lookups (`.define`).
- **System Diagnostics**: Detailed system health tracking using `.alive`, latency measurements via `.ping`, and execution of raw system commands via `.exec`.
- **Fun Modules**: Generate random facts (`.fact`), interactive jokes (`.joke`), games (`.truth`, `.dare`), dynamic memes (`.meme`), mathematical quizzes (`.mathquiz`), and ship percent calculators (`.ship`).

### Deployment & Ecosystem

- **Native Cloud Support**: Pre-configured setups for 1-click deployments to **Railway** (`railway.json`), **Heroku** (`app.json`), and **Render** (`render.yaml` + `render.py`).
- **Universal Auto-Installers**: Automated environment bootstrap files for cross-platform zero-dependency setups (`install.sh` for Linux/macOS and `install.ps1` for Windows).
- **Production Built Container**: Professional `Dockerfile` running on `python:3.11-slim-bookworm` paired with Node.js 20, designed for seamless VPS containerization.
- **State Persistence**: Secure internal session directory structure `(.astra_sessions)` preventing authentication drops during scheduled reboots or cloud spin-downs.
