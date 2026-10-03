export type Config = {
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
// Commit complete paragraphs/sentences, never half a fenced code block. The last
// incomplete phrase waits for more tokens; the final turn flushes it in full.
export function nextSegment(source: string, cursor: number, done: boolean): string | undefined {
  const tail = source.slice(cursor)
  if (!tail) return undefined
  let fence = '', candidate = 0, index = 0
  for (const line of tail.match(/[^\n]*\n|[^\n]+$/g) ?? []) {
    const match = /^\s*(`{3,}|~{3,})/.exec(line)
    if (match) {
      if (!fence) fence = match[1]!
      else if (match[1]![0] === fence[0] && match[1]!.length >= fence.length) fence = ''
    }
    index += line.length
    if (!fence && line.endsWith('\n') && (!line.trim() || index >= 160)) { candidate = index; break }
  }
  if (candidate) return tail.slice(0, candidate)
  if (done) return tail
  if (!fence && tail.length >= 100) {
    const sentence = /^([\s\S]{60,}?[.!?。！？](?:\s+|(?=[\u3400-\u9fff])))/.exec(tail)
    if (sentence) return sentence[1]
  }
  return undefined
}

export function isControlPrompt(text: string): boolean {
  return /^\s*\/[A-Za-z][\w:-]*(?:\s|$)/.test(text) || /^\s*!(?!\[)/.test(text)
}
