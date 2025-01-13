import { resolve } from 'path'

export default {
    root: resolve(__dirname, 'src'),
    build: {
        outDir: '../../html'
    },
    server: {
        port: 8080
    }
}