import { responsiveTables } from './tables'

export type Config = {
  configPath?: string; keyInfo?: Record<string, { active: string; saved: string }>;
  sources?: Record<string, string>; envStatus?: Record<string, boolean>; effectiveJevModel?: string;
  jevConfigSource?: string; jevUrlEnv?: string; jevModelEnv?: string;
  llmConfigSource?: string; detectionModel?: string; effectiveModel?: string;
  enabled: boolean; incomingLanguage: string; outgoingLanguage: string; detection: string;
  baseUrl: string; postUrl: string; model: string; baseUrlEnv: string; apiKeyEnv: string; modelEnv: string;
  jevUrl: string; jevKeyEnv: string; jevModel: string; incomingPrompt: string; outgoingPrompt: string;
  hasApiKey: boolean; hasJevKey: boolean; ready: boolean;
}
export const languages = [
  ['en', 'English'], ['zh', '简体中文'], ['zh-TW', '繁體中文'], ['ja', '日本語'], ['ko', '한국어'],
  ['fr', 'Français'], ['de', 'Deutsch'], ['es', 'Español'], ['pt', 'Português'], ['it', 'Italiano'],
  ['ru', 'Русский'], ['ar', 'العربية'], ['vi', 'Tiếng Việt'],
].map(([value, label]) => ({ value: value!, label: label! }))
export function languageOptions(value: string) {
  return languages.some(item => item.value === value) ? languages : [...languages, { value, label: value }]
}
export function cleanText(text: string): string {
  return text.replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, '').replace(/[\x00-\x08\x0b-\x1f\x7f]/g, '')
}
function cells(char: string): number {
  if (/\p{Mark}/u.test(char)) return 0
  const n = char.codePointAt(0)!
  return n >= 0x1100 && (n <= 0x115f || n >= 0x2e80 && n <= 0xa4cf || n >= 0xac00 && n <= 0xd7a3 || n >= 0xf900 && n <= 0xfaff || n >= 0xfe10 && n <= 0xfe6f || n >= 0xff00 && n <= 0xff60 || n >= 0x1f000) ? 2 : 1
}
export function wrapLines(text: string, columns: number): string[] {
  const lines: string[] = []
  for (const raw of cleanText(text).replace(/\t/g, '    ').split('\n')) {
    let line = '', width = 0
    for (const char of raw) {
      const size = cells(char)
      if (width + size > Math.max(2, columns) && line) { lines.push(line); line = ''; width = 0 }
      line += char; width += size
    }
    lines.push(line)
  }
  return lines
}
// Batch the backlog, rather than issuing detection + translation per paragraph.
// Live batches end at a complete line/sentence outside a fence; a finished
// ordinary reply is translated in one streaming request.
export function nextSegment(source: string, cursor: number, done: boolean): string | undefined {
  const tail = source.slice(cursor)
  if (!tail) return undefined
  const limit = done ? 12000 : 1600
  if (done && tail.length <= limit) return tail
  let fence = '', candidate = 0, index = 0
  for (const line of tail.match(/[^\n]*\n|[^\n]+$/g) ?? []) {
    if (index + line.length > limit && candidate >= 160) break
    const match = /^ {0,3}(`{3,}|~{3,})/.exec(line)
    if (match) {
      if (!fence) fence = match[1]!
      else if (match[1]![0] === fence[0] && match[1]!.length >= fence.length && !line.trim().slice(match[1]!.length).trim()) fence = ''
    }
    index += line.length
    if (!fence && line.endsWith('\n')) candidate = index
    if (index >= limit && candidate >= 160) break
  }
  if (candidate >= 160) return tail.slice(0, candidate)
  if (done) return tail
  if (!fence && tail.length >= 160) {
    const sentence = /^([\s\S]{160,}[.!?。！？](?:\s+|(?=[\u3400-\u9fff])))/.exec(tail.slice(0, limit))
    if (sentence) return sentence[1]
  }
  return undefined
}

export function isControlPrompt(text: string): boolean {
  return /^\s*\/[A-Za-z][\w:-]*(?:\s|$)/.test(text) || /^\s*!(?!\[)/.test(text)
}

// Native Markdown leaves accept at most 10,000 characters. Keep ordinary
// paragraphs, lists and fenced blocks intact. Oversized blocks fall back to
// bounded Text leaves so a long reply cannot invalidate the whole pane.
export function markdownParts(source: string, columns?: number): { text: string; plain: boolean }[] {
  const clean = cleanText(source)
  const text = columns === undefined ? clean : responsiveTables(clean, columns, value => Array.from(value).reduce((sum, char) => sum + cells(char), 0))
  const blocks: string[] = []
  let block = '', fence = ''
  for (const line of text.match(/[^\n]*\n|[^\n]+$/g) ?? []) {
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line)?.[1]
    if (marker) {
      if (!fence) fence = marker
      else if (marker[0] === fence[0] && marker.length >= fence.length && !line.trim().slice(marker.length).trim()) fence = ''
    }
    block += line
    if (!fence && !line.trim()) { blocks.push(block); block = '' }
  }
  if (block) blocks.push(block)
  const parts: { text: string; plain: boolean }[] = []
  for (const value of blocks) {
    const previous = parts[parts.length - 1]
    if (previous && !previous.plain && previous.text.length + value.length <= 9000) previous.text += value
    else if (value.length <= 9000) parts.push({ text: value, plain: false })
    else for (let index = 0; index < value.length;) {
      let end = Math.min(index + 9000, value.length)
      if (end < value.length && /[\uD800-\uDBFF]/.test(value[end - 1]!)) end--
      parts.push({ text: value.slice(index, end), plain: true }); index = end
    }
  }
  return parts
}

export function settingsGroups<T extends { label: string }>(items: T[], columns: number): T[][] {
  const groups: T[][] = []
  let group: T[] = [], used = 0
  for (const item of items) {
    // Four cells for the native button brackets/padding, two for its active marker.
    const width = Array.from(item.label).reduce((sum, char) => sum + cells(char), 6)
    if (group.length && used + 1 + width > columns) { groups.push(group); group = []; used = 0 }
    used += (group.length ? 1 : 0) + width; group.push(item)
  }
  if (group.length) groups.push(group)
  return groups
}
