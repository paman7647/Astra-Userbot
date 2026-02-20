const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * JS Downloader Bridge for Astra Userbot
 * Bypasses Python environment instability for media downloads.
 */

async function download() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error(JSON.stringify({ error: 'No URL provided' }));
        process.exit(1);
    }

    const url = args[0];
    const mode = args[1] || 'video'; // 'video' or 'audio'
    const cookies_file = args[2] || null;
    const cookies_browser = args[3] || null;

    const tempDir = path.join(__dirname, '../temp');
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

    const timestamp = Date.now();
    const outputTmpl = path.join(tempDir, `jsdl_${timestamp}_%(id)s.%(ext)s`);

    let ytArgs = [
        '--newline',
        '--no-playlist',
        '--geo-bypass',
        '--no-check-certificates',
        '--add-header', 'Referer:https://www.instagram.com/',
        '--add-header', 'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        '--add-header', 'Accept-Language:en-US,en;q=0.9',
        '--extractor-args', 'instagram:allow_direct_url',
        '-o', outputTmpl
    ];

    if (cookies_file && cookies_file !== 'None' && cookies_file !== '') {
        ytArgs.push('--cookies', cookies_file);
    } else if (cookies_browser && cookies_browser !== 'None' && cookies_browser !== '') {
        ytArgs.push('--cookies-from-browser', cookies_browser);
    }

    if (mode === 'audio') {
        ytArgs.push('--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0');
        ytArgs.push('-f', 'ba/b');
    } else {
        // Force H.264/MP4 for maximum compatibility across all devices
        ytArgs.push('-f', 'bestvideo[vcodec^=avc1][height<=720]+bestaudio[ext=m4a]/best[vcodec^=avc1][height<=720]/best[ext=mp4]/best');
        ytArgs.push('--merge-output-format', 'mp4');
    }

    ytArgs.push(url);

    // 1. Get Metadata First
    const metaArgs = ['-j', '--simulate', '--no-playlist', url];
    if (cookies_file && cookies_file !== 'None' && cookies_file !== '') metaArgs.push('--cookies', cookies_file);
    else if (cookies_browser && cookies_browser !== 'None' && cookies_browser !== '') metaArgs.push('--cookies-from-browser', cookies_browser);

    const metaCp = spawn('python3', ['-m', 'yt_dlp', ...metaArgs]);
    let metaData = '';
    metaCp.stdout.on('data', (d) => metaData += d.toString());

    await new Promise((resolve) => metaCp.on('close', resolve));

    let info = {};
    try {
        info = JSON.parse(metaData);
        // Direct output for Python to capture metadata immediately
        process.stdout.write(`METADATA:${JSON.stringify({
            title: info.title || 'Unknown Title',
            platform: info.extractor_key || 'Unknown',
            uploader: info.uploader || info.channel || '',
            url: info.webpage_url || url
        })}\n`);
    } catch (e) {
        process.stdout.write(`METADATA:{"title":"Media Content","platform":"Direct","url":"${url}"}\n`);
    }

    // 2. Perform Download
    const cp = spawn('python3', ['-m', 'yt_dlp', ...ytArgs]);

    cp.stdout.on('data', (data) => {
        // Forward yt-dlp progress to Python
        process.stdout.write(data);
    });

    cp.stderr.on('data', (data) => {
        process.stderr.write(data);
    });

    cp.on('close', (code) => {
        if (code !== 0) {
            process.exit(code);
        }

        const files = fs.readdirSync(tempDir).filter(f => f.startsWith(`jsdl_${timestamp}_`));
        if (files.length === 0) {
            console.error(JSON.stringify({ error: 'No file found after download' }));
            process.exit(1);
        }

        const results = files.map(f => path.join(tempDir, f));
        process.stdout.write(`SUCCESS:${JSON.stringify({ files: results })}\n`);
    });
}

download().catch(err => {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
});
