import { createApp } from "vue"
import ElementPlus from "element-plus"
import "element-plus/dist/index.css"
import "./assets/main.css"
import App from "./App.vue"
import type { Eel } from "@/composables/useEel"

// To make dev mode know what port to use
const PORT_NUMBER = 8686

// Tell Typescript that 'eel' exists on the window object
declare global {
  interface Window {
    eel: Eel
  }
}

// Explicitly set the eel host to localhost:8686. This allows us to switch between dev and production without any config changes.
if (import.meta.env.MODE === "development") {
  window.eel._host = `http://localhost:${PORT_NUMBER}`
  console.log(`Development mode started`)
}

console.log(`Eel host set to ${window.eel._host}`)

// Mount Vue app
const app = createApp(App)

app.use(ElementPlus)
app.mount("#app")
