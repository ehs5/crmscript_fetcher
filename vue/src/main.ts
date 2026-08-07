import { createApp } from "vue"
import ElementPlus from "element-plus"
import "element-plus/dist/index.css"
import "./assets/main.css"
import App from "./App.vue"

/** Creates and mounts the Vue app. */
function mountApp() {
  const app = createApp(App)
  app.use(ElementPlus)
  app.mount("#app")
}

// pywebview injects window.pywebview.api asynchronously, after the window has
// finished loading the page - there's no blocking <script> tag to rely on like
// Eel's eel.js include, so we wait for its readiness event before mounting.
// Vue's onMounted() hooks (which call the API) would otherwise race the injection.
if (window.pywebview) {
  mountApp()
} else {
  window.addEventListener("pywebviewready", mountApp, { once: true })
}
