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
        status: preview?.status ?? 'ready' as const }
    }),
  ]
}

/** One toolbar plus a single horizontal row. Item count never increases height. */
export function stripLayout(count: number, width: number, maxRows: number, requestedOffset: number) {
  const visibleCount = Math.max(1, Math.min(4, Math.floor((width + 2) / 26)))
  const maxOffset = Math.max(0, count - visibleCount)
  const start = Math.min(Math.max(0, requestedOffset), maxOffset)
  const cardWidth = Math.max(1, Math.min(32, Math.floor((width - 2 * (visibleCount - 1)) / visibleCount)))
  const rows = Math.max(0, Math.min(2, maxRows))
  return { visibleCount, maxOffset, cardWidth, rows, start }
}

/** A real file URL lets terminal applications handle their own file previews. */
export function linkHref(target: string): string | undefined {
  if (/^https?:\/\//.test(target)) return target
  if (target.startsWith('/')) return `file://${target.split('/').map(encodeURIComponent).join('/')}`
  return undefined
}

export function hoverLayout(size: Size | null, width: number, maxRows: number) {
  const availableColumns = Math.max(1, Math.min(96, width))
  const availableRows = Math.max(1, Math.min(22, maxRows))
  const aspect = size ? size.width / size.height : 1.5
  const columns = Math.max(1, Math.min(availableColumns, Math.round(availableRows * 2 * aspect)))
  const rows = Math.max(1, Math.min(availableRows, Math.round(columns / (2 * aspect))))
  return { columns, rows }
}
