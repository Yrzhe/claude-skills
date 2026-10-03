import type { PastedImage, Reply } from '../types'
import type { Size } from './layout'

export type StripItem = {
  key: string
  label: string
  kind: 'paste' | 'image' | 'video' | 'link'
  target: string | null
  path: string | null
  size: Size | null
  status: 'ready' | 'pending' | 'unavailable'
  pixels?: string
}

export function stripItems(pasted: PastedImage[], reply: Reply | null): StripItem[] {
  const media = new Map(reply?.media.map(item => [item.target, item]))
  return [
    ...pasted.map(item => ({ key: `paste-${item.n}`, label: `Pasted #${item.n}`, kind: 'paste' as const,
      target: item.path, path: item.path, size: item.size, status: item.path ? 'ready' as const : 'unavailable' as const })),
    ...(reply?.links ?? []).map((link, index) => {
      const preview = media.get(link.target)
      const label = link.kind === 'link' && /^https?:/.test(link.target) ? new URL(link.target).host : link.label
      return { ...link, label, key: `reply-${index}`, path: preview?.path ?? null, size: preview?.size ?? null,
        status: preview?.status ?? 'ready' as const, pixels: preview?.pixels }
    }),
  ]
}

/** One toolbar plus a single horizontal row. Item count never increases height. */
export function stripLayout(count: number, width: number, maxRows: number, requestedOffset: number) {
  const visibleCount = Math.max(1, Math.min(4, Math.floor((width + 2) / 26)))
  const maxOffset = Math.max(0, count - visibleCount)
  const start = Math.min(Math.max(0, requestedOffset), maxOffset)
  const cardWidth = Math.max(1, Math.min(32, Math.floor((width - 2 * (visibleCount - 1)) / visibleCount)))
  const rows = Math.max(0, Math.min(6, maxRows))
  return { visibleCount, maxOffset, cardWidth, rows, pictureRows: Math.max(0, rows - 3), start }
}

/** 64x32 RGB samples to colored half-block cells, with letterboxing. */
export function pixelCells(base64: string, size: Size | null, columns: number, rows: number): string {
  const rgb = Uint8Array.from(atob(base64), c => c.charCodeAt(0))
  if (rgb.length !== 64 * 32 * 3) throw new Error('Invalid preview pixels')
  const bytes = new Uint8Array(columns * rows * 12)
  const view = new DataView(bytes.buffer)
  const ratio = size ? size.width / size.height : 2
  const pixelWidth = Math.min(columns, Math.max(1, Math.round(rows * 2 * ratio)))
  const pixelHeight = Math.min(rows * 2, Math.max(1, Math.round(columns / ratio)))
  const left = Math.floor((columns - pixelWidth) / 2)
  const top = Math.floor((rows * 2 - pixelHeight) / 2)
  const color = (x: number, y: number) => {
    if (x < left || x >= left + pixelWidth || y < top || y >= top + pixelHeight) return 0x01000000
    const sx = Math.min(63, Math.floor((x - left) * 64 / pixelWidth))
    const sy = Math.min(31, Math.floor((y - top) * 32 / pixelHeight))
    const offset = (sy * 64 + sx) * 3
    return (rgb[offset]! << 16) | (rgb[offset + 1]! << 8) | rgb[offset + 2]!
  }
  for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
    const at = (y * columns + x) * 12
    const upper = color(x, y * 2)
    const lower = color(x, y * 2 + 1)
    const empty = 0x01000000
    // Default foreground and default background are different colors. Blank
    // letterboxing must use a space, not a half-block in the default foreground.
    view.setUint32(at, upper === empty ? lower === empty ? 0x20 : 0x2584 : 0x2580, true)
    view.setUint32(at + 4, upper === empty ? lower : upper, true)
    view.setUint32(at + 8, upper === empty ? empty : lower, true)
  }
  return btoa(String.fromCharCode(...bytes))
}
