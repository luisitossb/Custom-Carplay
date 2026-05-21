import CarplayNode from 'node-carplay/node'
import { WebSocketServer } from 'ws'

const wss = new WebSocketServer({ port: 4000 })
const clients = new Set()

wss.on('connection', (ws) => {
    console.log('Python client connected')
    clients.add(ws)
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

// Track last known title to suppress duplicate "Now playing" logs
let _lastTitle = ''

function makeCarplay() {
    const cp = new CarplayNode({
        width: 1024,
        height: 600,
        fps: 30,
        dpi: 160,
        // frameInterval keeps periodic 'frame' commands flowing to the dongle,
        // which prevents it from going passive and dropping AVRCP updates
        phoneConfig: {
            CarPlay: { frameInterval: 33 },
            AndroidAuto: { frameInterval: 33 },
        },
    })
    cp.onmessage = (msg) => {
        switch (msg.type) {
            case 'plugged':
                console.log('iPhone plugged in / connected')
                _lastTitle = ''
                broadcast({ type: 'plugged' })
                break
            case 'unplugged':
                console.log('iPhone unplugged / disconnected')
                _lastTitle = ''
                broadcast({ type: 'unplugged' })
                break
            case 'media':
                if (msg.message?.payload?.type === 1) {
                    const m = msg.message.payload.media
                    const key = `${m.MediaArtistName}|${m.MediaSongName}`
                    if (m.MediaSongName && m.MediaArtistName && key !== _lastTitle) {
                        console.log(`Now playing: ${m.MediaArtistName} — ${m.MediaSongName}`)
                        _lastTitle = key
                    }
                    broadcast({ type: 'media', data: m })
                } else if (msg.message?.payload?.type === 3) {
                    broadcast({ type: 'albumart', data: msg.message.payload.base64Image })
                }
                break
            case 'video':
                if (msg.message?.data) {
                    broadcast({ type: 'video', data: Buffer.from(msg.message.data).toString('base64') })
                }
                break
            case 'audio':
                if (msg.message?.data) {
                    broadcast({ type: 'audio', data: Buffer.from(msg.message.data).toString('base64') })
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
