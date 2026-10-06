// The terminal's native Markdown table measures the transcript, not its containing
// mod pane. Keep grids that fit, and turn wider tables into labelled records.
// Work on display text only: model prompts, translations and code stay unchanged.
export function tableCells(line: string): string[] | undefined {
  if (/^(?: {4}|\t)/.test(line)) return undefined
  const source = line.trim()
  const cells: string[] = []
  let cell = '', pipes = 0
  for (let i = 0; i < source.length; i++) {
    const char = source[i]!
    if (char === '\\' && i + 1 < source.length) { cell += char + source[++i]; continue }
    if (char === '|') { cells.push(cell.trim()); cell = ''; pipes++ }
    else cell += char
  }
  if (!pipes) return undefined
  cells.push(cell.trim())
  if (source.startsWith('|')) cells.shift()
  // An escaped final pipe belongs to the last cell, not the outside border.
  if (cell === '' && source.endsWith('|')) cells.pop()
  return cells
}

export function responsiveTables(source: string, columns: number, width: (text: string) => number): string {
  const lines = source.match(/[^\n]*\n|[^\n]+$/g) ?? []
  const result: string[] = []
  let fence = ''
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line)?.[1]
    if (marker) {
      if (!fence) fence = marker
      else if (marker[0] === fence[0] && marker.length >= fence.length && !line.trim().slice(marker.length).trim()) fence = ''
      result.push(line); continue
    }
    const headers = !fence && !/^\s*(?:>|#{1,6}\s|[-+*]\s|\d+[.)]\s)/.test(line) ? tableCells(line) : undefined
    const delimiters = headers && tableCells(lines[i + 1] ?? '')
    if (!headers?.length || !delimiters || delimiters.length !== headers.length || !delimiters.every(cell => /^:?-+:?$/.test(cell))) {
      result.push(line); continue
    }
    const rows: string[][] = []
    let end = i + 2
    while (end < lines.length) {
      const row = tableCells(lines[end]!)
      // Do not mistake a code fence, list or block quote for a data row.
      if (!row || /^\s*(?:`{3}|~{3}|>|#{1,6}\s|[-+*]\s|\d+[.)]\s)/.test(lines[end]!)) break
      rows.push(row); end++
    }
    // Counting raw inline Markdown is conservative: never underestimate a cell
    // because of code, link destinations, CJK characters or escaped delimiters.
    const count = Math.max(headers.length, ...rows.map(row => row.length))
    const widths = Array.from({ length: count }, (_, col) => Math.max(3, width(headers[col] ?? ''), ...rows.map(row => width(row[col] ?? ''))))
    const fits = widths.reduce((sum, value) => sum + value + 3, 1) <= columns
    if (fits) {
      // Keep large tables under the native Markdown leaf limit by repeating
      // their header at row boundaries, instead of falling back to raw pipes.
      const heading = line + lines[i + 1]!
      let chunk = heading
      for (let j = i + 2; j < end; j++) {
        if (chunk.length + lines[j]!.length > 8000) { result.push(chunk + '\n'); chunk = heading }
        chunk += lines[j]!
      }
      result.push(chunk)
    } else {
      const separator = '─'.repeat(Math.max(1, Math.floor(columns)))
      const records = rows.length ? rows : [headers.map(() => '')]
      result.push('\n' + records.map(row => {
        const fields = Array.from({ length: Math.max(headers.length, row.length) }, (_, col) => {
          const label = headers[col] || `第 ${col + 1} 列`
          return `${label}: ${row[col] || '—'}`
        })
        // Hard line breaks keep one field per line; blank lines separate records.
        return fields.join('  \n')
      }).join(`\n\n${separator}\n\n`) + '\n\n')
    }
    i = end - 1
  }
  return result.join('')
}
