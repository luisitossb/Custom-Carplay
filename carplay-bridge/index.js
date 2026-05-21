import CarplayNode from 'node-carplay/node'
import { WebSocketServer } from 'ws'
import { spawn } from 'child_process'

// PCM format per decodeType — matches node-carplay's decodeTypeMap
const DECODE_FMT = {
    1: { rate: 44100, ch: 2 },
    2: { rate: 44100, ch: 2 },
    3: { rate: 8000,  ch: 1 },
    4: { rate: 48000, ch: 2 },
    5: { rate: 16000, ch: 1 },
    6: { rate: 24000, ch: 1 },
    7: { rate: 16000, ch: 2 },
}

let _aplay = null
let _aplayType = null

function getAplay(decodeType) {
    if (_aplay && !_aplay.killed && _aplayType === decodeType) return _aplay
    if (_aplay) { try { _aplay.stdin.destroy(); _aplay.kill() } catch {} }
    const { rate, ch } = DECODE_FMT[decodeType] ?? { rate: 44100, ch: 2 }
    _aplay = spawn('aplay', ['-f', 'S16_LE', '-r', String(rate), '-c', String(ch), '--buffer-size=4096'], {
        stdio: ['pipe', 'ignore', 'ignore'],
    })
    _aplay.on('error', (e) => console.error('aplay:', e.message))
    _aplay.on('close', () => { _aplay = null })
    _aplayType = decodeType
    return _aplay
}

const wss = new WebSocketServer({ port: 4000 })
const clients = new Set()

// Cache current state so new clients get it immediately on connect
const cache = { plugged: false, track: null, albumart: null }

let activeCarplay = null

wss.on('connection', (ws) => {
    console.log('Python client connected')
    clients.add(ws)

    // Replay current state to the new client
    if (cache.plugged) ws.send(JSON.stringify({ type: 'plugged' }))
    if (cache.track)   ws.send(JSON.stringify({ type: 'media', data: cache.track }))
    if (cache.albumart) ws.send(JSON.stringify({ type: 'albumart', data: cache.albumart }))

    ws.on('message', (raw) => {
        try {
            const msg = JSON.parse(raw)
            if (msg.type === 'key' && activeCarplay) {
                activeCarplay.sendKey(msg.action)
            }
        } catch {}
    })

    ws.on('close', () => {
        console.log('Python client disconnected')
        clients.delete(ws)
    })
})

function broadcast(msg) {
    const data = JSON.stringify(msg)
    for (const client of clients) {
        if (client.readyState === 1) client.send(data)
    }
}

let _lastTitle = ''

function makeCarplay() {
    const cp = new CarplayNode({
        width: 1024,
        height: 600,
        fps: 30,
        dpi: 160,
        phoneConfig: {
            CarPlay: { frameInterval: 33 },
            AndroidAuto: { frameInterval: 33 },
        },
    })
    activeCarplay = cp

    cp.onmessage = (msg) => {
        switch (msg.type) {
            case 'plugged':
                console.log('iPhone plugged in / connected')
                _lastTitle = ''
                cache.plugged = true
                if (!cp._frameTimer) {
                    cp._frameTimer = setInterval(() => cp.sendKey('frame'), 100)
                }
                broadcast({ type: 'plugged' })
                break
            case 'unplugged':
                console.log('iPhone unplugged / disconnected')
                _lastTitle = ''
                cache.plugged = false
                cache.track = null
                cache.albumart = null
                if (cp._frameTimer) { clearInterval(cp._frameTimer); cp._frameTimer = null }
                broadcast({ type: 'unplugged' })
                break
            case 'media':
                if (msg.message?.payload?.type === 1) {
                    const m = msg.message.payload.media
                    const raw = Object.fromEntries(Object.entries(m).filter(([, v]) => v !== '' && v != null))

                    // Detect song change: artist changed OR duration changed significantly.
                    // When detected, drop stale identity fields from cache so the
                    // new-client replay doesn't serve the previous song's metadata.
                    const artistChanged = cache.track && raw.MediaArtistName &&
                        raw.MediaArtistName !== cache.track.MediaArtistName
                    const durationChanged = cache.track && raw.MediaSongDuration != null &&
                        Math.abs(raw.MediaSongDuration - (cache.track.MediaSongDuration ?? 0)) > 2000
                    if (artistChanged || durationChanged) {
                        delete cache.track.MediaSongName
                        delete cache.track.MediaAlbumName
                        delete cache.track.MediaSongDuration
                    }

                    // Update cache for new-client replay (full merged state)
                    cache.track = Object.assign({}, cache.track, raw)

                    // Log when a new song arrives (MediaLyrics carries the title on song changes)
                    const title = raw.MediaLyrics ?? raw.MediaSongName
                    const key = `${raw.MediaArtistName}|${title}`
                    if (title && raw.MediaArtistName && key !== _lastTitle) {
                        console.log(`Now playing: ${raw.MediaArtistName} — ${title}`)
                        _lastTitle = key
                    }

                    // Broadcast only what the phone actually sent — Python accumulates
                    // its own state via _merge_media, so sending enriched/merged packets
                    // would cause it to re-apply stale song names on every position update.
                    broadcast({ type: 'media', data: raw })
                } else if (msg.message?.payload?.type === 3) {
                    cache.albumart = msg.message.payload.base64Image
                    broadcast({ type: 'albumart', data: cache.albumart })
                }
                break
            case 'video':
                if (msg.message?.data) {
                    broadcast({ type: 'video', data: Buffer.from(msg.message.data).toString('base64') })
                }
                break
            case 'audio':
                if (msg.message?.data) {
                    const player = getAplay(msg.message.decodeType)
                    if (player && !player.killed) {
                        player.stdin.write(Buffer.from(msg.message.data.buffer))
                    }
                }
                break
            case 'command':
                broadcast({ type: 'command', data: msg.message })
                break
        }
    }
    return cp
}

async function start() {
    const carplay = makeCarplay()
    try {
        await carplay.start()
    } catch (err) {
        if (err.message?.includes('LIBUSB_ERROR_NOT_FOUND')) {
            console.log('Dongle re-enumerating after reset — retrying in 2s...')
            setTimeout(start, 2000)
        } else {
            console.error('Fatal CarPlay error:', err)
            process.exit(1)
        }
    }
}

console.log('CarPlay bridge running on ws://localhost:4000')
start()
