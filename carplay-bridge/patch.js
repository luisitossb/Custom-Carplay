import { readFileSync, writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const file = join(__dirname, 'node_modules/node-carplay/dist/node/CarplayNode.js')

let content
try {
    content = readFileSync(file, 'utf8')
} catch {
    console.error('[patch] CarplayNode.js not found — run npm install first')
    process.exit(1)
}

if (content.includes('dongle self-cycling')) {
    console.log('[patch] Already patched')
    process.exit(0)
}

// Wrap reset in try-catch so a self-cycling dongle doesn't crash start()
content = content.replace(
    '        await device.reset();\n        await device.close();',
    '        try { await device.reset(); } catch (e) { console.log(\'Reset failed (dongle self-cycling), continuing...\'); }\n        try { await device.close(); } catch (_) {}'
)

// Reduce post-reset wait from 3s to 1s to stay within the dongle's 9s timeout window
content = content.replace(
    'const USB_WAIT_PERIOD_MS = 3000;',
    'const USB_WAIT_PERIOD_MS = 1000;'
)

writeFileSync(file, content)
console.log('[patch] CarplayNode patched — reset is fault-tolerant, wait reduced to 1s')
