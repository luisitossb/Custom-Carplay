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

function makeCarplay() {
    const cp = new CarplayNode()
    cp.onmessage = (msg) => {
        switch (msg.type) {
            case 'plugged':
                console.log('iPhone plugged in / connected')
                broadcast({ type: 'plugged' })
                break
            case 'unplugged':
                console.log('iPhone unplugged / disconnected')
                broadcast({ type: 'unplugged' })
                break
            case 'media':
                if (msg.message?.payload?.type === 1) {
                    const m = msg.message.payload.media
                    if (m.MediaSongName || m.MediaArtistName || m.MediaSongDuration) {
                        console.log(`Media: ${m.MediaArtistName} — ${m.MediaSongName}`)
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
                console.log('Command:', msg.message)
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
