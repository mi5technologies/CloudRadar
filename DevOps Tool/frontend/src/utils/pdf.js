/**
 * Opens an HTML string in a new browser window/tab and immediately triggers
 * the browser's Print dialog so the user can "Save as PDF".
 *
 * @param {string} html  - Full HTML document string
 * @param {string} title - Window title shown in the print dialog
 */
export function openPrintWindow(html, title = 'CloudRadar Report') {
  // If the response is a plain JSON/text fragment (no DOCTYPE), wrap it
  const isFullDoc = html.trimStart().toLowerCase().startsWith('<!doctype') ||
                    html.trimStart().toLowerCase().startsWith('<html')

  const fullHtml = isFullDoc ? html : `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <style>
    body { font-family: sans-serif; font-size: 13px; color: #111; padding: 24px; }
    pre  { background: #f1f5f9; padding: 16px; border-radius: 6px; font-size: 12px;
           white-space: pre-wrap; word-break: break-word; }
    h1   { font-size: 18px; margin-bottom: 16px; }
    @media print { body { padding: 0; } }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <pre>${html.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
</body>
</html>`

  const win = window.open('', '_blank')
  if (!win) {
    // Pop-up blocked — fall back to blob download
    const blob = new Blob([fullHtml], { type: 'text/html' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `${title.replace(/\s+/g, '_')}.html`
    a.click()
    URL.revokeObjectURL(url)
    return
  }

  win.document.write(fullHtml)
  win.document.close()

  // Slight delay to let the page render before triggering print
  win.onload = () => {
    win.focus()
    win.print()
  }
  // Fallback if onload doesn't fire (already loaded)
  setTimeout(() => {
    try { win.focus(); win.print() } catch (_) {}
  }, 600)
}
