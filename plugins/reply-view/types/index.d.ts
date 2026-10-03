export type PastedImage = {
  n: number
  /** Absolute path of the cached PNG; null when it can't be found. */
  path: string | null
  /** Pixel size; null when unknown, and the tile falls back to a default shape. */
  size: { width: number; height: number } | null
}

declare module 'claude-code' {
  interface PluginState {
    'reply-view': { images: PastedImage[]; reply: Reply | null; hovered: string | null }
  }
}
export type ReplyLink = { target: string; label: string; kind: 'image' | 'video' | 'link' }
export type Preview = ReplyLink & {
  path: string | null
  size: { width: number; height: number } | null
  status: 'pending' | 'ready' | 'unavailable'
  error?: string
}
export type Reply = { text: string; links: ReplyLink[]; media: Preview[] }
