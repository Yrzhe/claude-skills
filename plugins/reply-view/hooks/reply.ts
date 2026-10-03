import type { SessionMessage } from 'claude-code'
import type { ReplyLink, Reply } from '../types'

const IMAGE = /\.(png|jpe?g|webp|gif|avif|bmp|tiff?|heic|svg)$/i
const VIDEO = /\.(mp4|m4v|mov|webm|mkv|avi|ogv)$/i
const LOCALHOST = /^(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)(?:[/?#]|$)/i

/** Only web URLs and explicit file paths become actions; never executable schemes. */
export function normalizeTarget(raw: string, cwd: string): string | null {
  let value = raw.trim().replace(/^<|>$/g, '')
  if (!value || /[\x00-\x1f\x7f]/.test(value)) return null
  if (LOCALHOST.test(value)) value = `http://${value}`
  if (/^https?:\/\//i.test(value)) {
    try {
      const url = new URL(value)
      if (!url.hostname || url.username || url.password) return null
      if (url.hostname === '0.0.0.0') url.hostname = 'localhost'
      return url.href
    } catch { return null }
  }
  if (/^file:\/\//i.test(value)) {
    try {
      const url = new URL(value)
      if (url.hostname && url.hostname !== 'localhost') return null
      value = decodeURIComponent(url.pathname)
    } catch { return null }
  } else if (/^[a-z][a-z\d+.-]*:/i.test(value)) return null
  // Claude's file citations may have :line or #Lline suffixes.
  value = value.replace(/(?::\d+(?::\d+)?|#L\d+(?:-L?\d+)?)$/, '')
  // Slash commands are not root-level file references. Repository slugs and
  // package names are not relative files unless they carry a file extension.
  if (/^\/[a-z][\w-]*(?:\s|$)/i.test(value)) return null
  if (value.startsWith('~/')) return value
  if (value.startsWith('/')) return value
  if (value.startsWith('./') || value.startsWith('../') || (/^[\w.-]+\/.+/.test(value) && /\.[a-z\d]{1,10}$/i.test(value))) {
    try { return decodeURIComponent(new URL(value, `file://${cwd.replace(/\/$/, '')}/`).pathname) }
    catch { return null }
  }
  if (IMAGE.test(value) || VIDEO.test(value)) return `${cwd}/${value}`
  return null
}

function trimBare(value: string): string {
  value = value.replace(/[.,;:!?，。；：！？、]+$/, '')
  while (value.endsWith(')') && (value.match(/\)/g)?.length ?? 0) > (value.match(/\(/g)?.length ?? 0)) value = value.slice(0, -1)
  return value
}

export function extractLinks(text: string, cwd: string): ReplyLink[] {
  const candidates: { raw: string; label?: string; image?: boolean; index: number }[] = []
  const covered: [number, number][] = []
  // Angle-bracket destinations support spaces; bare destinations support balanced parentheses.
  const markdown = /!?\[([^\]\n]*)\]\(\s*(<[^>\n]+>|(?:[^\s()]|\([^()]*\))+)(?:\s+["'][^\n]*?["'])?\s*\)/g
  for (const match of text.matchAll(markdown)) {
    candidates.push({ raw: match[2]!, label: match[1], image: match[0].startsWith('!'), index: match.index! })
    covered.push([match.index!, match.index! + match[0].length])
  }
  for (const match of text.matchAll(/`([^`\n]+)`/g)) {
    candidates.push({ raw: match[1]!, index: match.index! })
    covered.push([match.index!, match.index! + match[0].length])
  }
  const bare = /(?:https?:\/\/|file:\/\/|(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]):\d+)[^\s<>"'`\u3000-\u303f\uff00-\uffef]*|(?:~\/|\.{0,2}\/)[^\s<>"'`\u3000-\u303f\uff00-\uffef]+\.(?:png|jpe?g|webp|gif|avif|bmp|tiff?|heic|svg|mp4|m4v|mov|webm|mkv|avi|ogv)(?::\d+)?/gi
  for (const match of text.matchAll(bare)) {
    if (covered.some(([a, b]) => match.index! >= a && match.index! < b)) continue
    // Do not turn the // inside a rejected custom scheme into a local path.
    if (match.index! > 0 && /[\w:/]/.test(text[match.index! - 1]!)) continue
    candidates.push({ raw: trimBare(match[0]), index: match.index! })
  }
  const seen = new Set<string>()
  const links: ReplyLink[] = []
  for (const { raw, label, image } of candidates.sort((a, b) => a.index - b.index)) {
    const target = normalizeTarget(raw, cwd)
    if (!target || seen.has(target)) continue
    seen.add(target)
    const path = /^https?:/.test(target) ? new URL(target).pathname : target
    const kind = image || IMAGE.test(path) || IMAGE.test(label ?? '') ? 'image' : VIDEO.test(path) || VIDEO.test(label ?? '') ? 'video' : 'link'
    links.push({ target, label: (label || target.split('/').pop() || target).slice(0, 200), kind })
  }
  return links
}

/** Restore the last completed visible response without including tool output or user text. */
export function lastReply(messages: readonly SessionMessage[]): { text: string; answer: string } | null {
  let end = messages.length - 1
  while (end >= 0 && !(messages[end]!.role === 'assistant' && messages[end]!.text && messages[end]!.toolUses.length === 0)) end--
  if (end < 0) return null
  let start = end
  while (start > 0) {
    const previous = messages[start - 1]!
    if (previous.role === 'user' && !previous.toolResults?.length) break
    start--
  }
  return { answer: messages[end]!.text, text: messages.slice(start, end + 1).filter(m => m.role === 'assistant' && m.text).map(m => m.text).join('\n\n') }
}

export function makeReply(text: string, answer: string, cwd: string): Reply {
  const links = extractLinks(answer, cwd)
  return { text, links, media: links.filter(link => link.kind !== 'link').map(link => ({ ...link, path: null, size: null, status: 'pending' })) }
}
