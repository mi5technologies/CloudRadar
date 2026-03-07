import { reactive } from 'vue'

const toasts = reactive([])
let nextId = 1

export function useToast() {
  function add(message, type = 'info', duration = 4000) {
    const id = nextId++
    toasts.push({ id, message, type })
    if (duration > 0) setTimeout(() => remove(id), duration)
    return id
  }

  function remove(id) {
    const idx = toasts.findIndex(t => t.id === id)
    if (idx !== -1) toasts.splice(idx, 1)
  }

  const success = (msg, dur) => add(msg, 'success', dur)
  const error   = (msg, dur) => add(msg, 'error', dur ?? 6000)
  const info    = (msg, dur) => add(msg, 'info', dur)
  const warn    = (msg, dur) => add(msg, 'warn', dur)

  return { toasts, add, remove, success, error, info, warn }
}
