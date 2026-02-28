/**
 * reddit.js — Astra Userbot Reddit Video Downloader
 * Based on js_downloader.js pattern.
 * Downloads Reddit/v.redd.it videos with proper audio+video merge via yt-dlp.
 *
 * Usage: node utils/reddit.js <url> [mode=video|audio]
 * Stdout protocol:
 *   METADATA:{...json...}
 *   SUCCESS:{files:[...paths...]}
 *   (or exits with non-zero on failure)
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

async function download() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error(JSON.stringify({ error: 'No URL provided' }));
        process.exit(1);
    }

    const url = args[0];
    const mode = args[1] || 'video';

    // Ensure temp dir exists
    const tempDir = path.join(__dirname, '../temp');
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

    const timestamp = Date.now();
    const outputTmpl = path.join(tempDir, `reddit_${timestamp}_%(id)s.%(ext)s`);

    // ── Step 1: Fetch Metadata ──────────────────────────────────
    const metaArgs = [
        '-m', 'yt_dlp',
        '-j', '--simulate', '--no-playlist',
        '--add-header', 'Referer:https://www.reddit.com/',
        '--add-header', 'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        url
    ];

    const metaCp = spawn('python3', metaArgs);
    let metaData = '';
    metaCp.stdout.on('data', (d) => metaData += d.toString());
    await new Promise((resolve) => metaCp.on('close', resolve));

    let info = {};
    try {
        info = JSON.parse(metaData);
        process.stdout.write(`METADATA:${JSON.stringify({
            title: info.title || 'Reddit Video',
            platform: info.extractor_key || 'Reddit',
            uploader: info.uploader || info.subreddit || '',
            url: info.webpage_url || url,
            duration: info.duration || 0
        })}\n`);
    } catch (_) {
        process.stdout.write(`METADATA:{"title":"Reddit Video","platform":"Reddit","url":"${url}"}\n`);
    }

    // ── Step 2: Build yt-dlp args ───────────────────────────────
    let ytArgs = [
        '-m', 'yt_dlp',
        '--newline',
        '--no-playlist',
        '--geo-bypass',
        '--no-check-certificates',
        '--add-header', 'Referer:https://www.reddit.com/',
        '--add-header', 'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        '--buffer-size', '1M',
        '--concurrent-fragments', '4',
        '--no-mtime',
        '--socket-timeout', '20',
        '-o', outputTmpl
    ];

    if (mode === 'audio') {
        ytArgs.push('--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0');
        ytArgs.push('-f', 'ba/b');
    } else {
        // Force H.264/MP4 — maximum device compatibility (no VP9/AV1)
        ytArgs.push(
            '-f', 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best',
            '-S', 'vcodec:h264,res,acodec:m4a',
            '--merge-output-format', 'mp4',
            '--postprocessor-args', 'ffmpeg:-movflags +faststart'
        );
    }

    ytArgs.push(url);

    // ── Step 3: Download ────────────────────────────────────────
    return new Promise((resolve, reject) => {
        const cp = spawn('python3', ytArgs);

        cp.stdout.on('data', (data) => process.stdout.write(data));
        cp.stderr.on('data', (data) => process.stderr.write(data));

        cp.on('close', (code) => {
            if (code !== 0) {
                console.error(JSON.stringify({ error: `yt-dlp exited with code ${code}` }));
                process.exit(code);
            }

            const files = fs.readdirSync(tempDir)
                .filter(f => f.startsWith(`reddit_${timestamp}_`))
                .map(f => path.join(tempDir, f));

            if (files.length === 0) {
                console.error(JSON.stringify({ error: 'No output file found after download' }));
                process.exit(1);
            }

            process.stdout.write(`SUCCESS:${JSON.stringify({ files })}\n`);
            resolve();
        });
    });
}

download().catch(err => {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
});
