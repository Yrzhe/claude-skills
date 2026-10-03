import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { PastedImage } from '../types'
import { fitRow, imageNumbers, pngSize } from './layout'
import type { Size } from './layout'
import { lastReply, makeReply } from './reply'
import type { Preview, Reply } from '../types'

// Pasting an image raises no prompt.edit (the tag only shows up on the next keystroke),
// so the draft is polled instead.
const POLL_MS = 200

const images = atom({ plugin: 'reply-view', key: 'images' } as const, [] as PastedImage[])
const reply = atom({ plugin: 'reply-view', key: 'reply' } as const, null as Reply | null)
let generation = 0
let mediaPage = 0
let linkPage = 0
let activeTurn = ''
let steps = new Map<number, string>()
let sessionKey = ''
let interactive = true
let previewBusy = false

async function helper($: EngineInterface, request: object): Promise<{ path?: string; size?: Size; error?: string }> {
  const root = $.plugin.root
  const result = await $.process.run(['python3', `${root}/scripts/media.py`], {
    stdin: JSON.stringify(request), timeoutMs: 40000,
  })
  let data
  try { data = JSON.parse(result.stdout) } catch { throw new Error('Media helper returned no result') }
  if (result.exitCode !== 0 || data.error) throw new Error(data.error || 'System action failed')
  return data
}

async function action($: EngineInterface, request: object, success: string) {
  try {
    await helper($, request)
    $.ui.toast(success)
  } catch (error) {
    $.ui.toast(error instanceof Error ? error.message : 'System action failed')
  }
}

// One bounded conversion at a time, outside turn completion and render hooks.
function queuePreview($: EngineInterface, token: number, index = 0, delay = 1) {
  $.clock.after(delay, async () => {
    if (token !== generation) return
    if (previewBusy) { queuePreview($, token, index, 100); return }
    const current = await read($, reply)
    const media = current?.media[index]
    if (!media) return
    previewBusy = true
    let result: Partial<Preview>
    try {
      const data = await helper($, { action: 'preview', target: media.target, kind: media.kind, cacheKey: `${sessionKey}:${token}` })
      if (!data.path || !data.size) throw new Error('No preview available')
      result = { path: data.path, size: data.size, status: 'ready' }
    } catch (error) {
      result = { status: 'unavailable', error: error instanceof Error ? error.message : 'No preview available' }
    } finally {
      previewBusy = false
    }
    if (token !== generation) return
    await update($, reply, value => value && ({ ...value, media: value.media.map((item, i) => i === index ? { ...item, ...result } : item) }))
    if (token === generation) queuePreview($, token, index + 1)
  })
}

async function setReply($: EngineInterface, text: string, answer: string) {
  const token = ++generation
  mediaPage = 0
  linkPage = 0
  const cwd = await $.session.cwd()
  const id = await $.session.id()
  if (token !== generation) return
  sessionKey = id
  await update($, reply, () => makeReply(text, answer, cwd))
  queuePreview($, token)
}

async function restore($: EngineInterface) {
  const token = generation
  const saved = lastReply(await $.session.messages().catch(() => []))
  if (saved && token === generation) await setReply($, saved.text, saved.answer)
}

let tmpRoot: string | undefined
let found: { sessionId: string; dir: string } | undefined
// The image numbers last drawn, so an unchanged draft doesn't rewrite state; undefined
// while a drawn image's file is still missing, so the next poll looks again.
let shownKey: string | undefined
let isChecking = false
const sizes = new Map<string, Size | null>()

// Claude Code caches each paste as <tmp>/<project>/<session>/images/<n>.png. The project
// folder is named after a working directory that may since have moved, so find it by the
// session id instead of rebuilding it.
async function imagesDir($: EngineInterface): Promise<string | undefined> {
  const sessionId = await $.session.id()
  if (found?.sessionId === sessionId) return found.dir
  if (tmpRoot === undefined) {
    const fromEnv = await $.env.get('CLAUDE_CODE_TMPDIR')
    tmpRoot = fromEnv ?? `/tmp/claude-${(await $.process.run(['id', '-u'])).stdout.trim()}`
  }
  const entries = await $.fs.list(tmpRoot).catch(() => [])
  for (const entry of entries) {
    const dir = `${tmpRoot}/${entry.name}/${sessionId}/images`
    if (entry.kind === 'dir' && (await $.fs.exists(dir))) {
      found = { sessionId, dir }
      return dir
    }
  }
  return undefined
}

async function describe($: EngineInterface, dir: string | undefined, n: number): Promise<PastedImage> {
  const path = `${dir}/${n}.png`
  if (dir === undefined || !(await $.fs.exists(path))) return { n, path: null, size: null }
  if (!sizes.has(path)) {
    const head = await $.fs.read(path, { as: 'bytes' }).then(
      ({ base64 }) => pngSize(base64),
      () => undefined, // too big to read: still drawable, just without its aspect ratio
    )
    if (head === null) return { n, path: null, size: null }
    sizes.set(path, head ?? null)
  }
  return { n, path, size: sizes.get(path) ?? null }
}

async function show($: EngineInterface, draft: string) {
  const token = generation
  const numbers = imageNumbers(draft)
  const key = numbers.join(',')
  if (key === shownKey) return
  const dir = numbers.length > 0 ? await imagesDir($) : undefined
  const list: PastedImage[] = []
  for (const n of numbers) list.push(await describe($, dir, n))
  if (token !== generation) return
  shownKey = list.every(image => image.path !== null) ? key : undefined
  await update($, images, () => list)
}

async function check($: EngineInterface) {
  if (isChecking) return
  isChecking = true
  try {
    const id = await $.session.id()
    if (sessionKey !== id) {
      sessionKey = id
      shownKey = undefined
      found = undefined
      sizes.clear()
    }
    await show($, (await $.prompt.read()).text)
  } finally {
    isChecking = false
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    interactive = e.isInteractive && e.surface === 'terminal'
    if (!interactive) return next(e)
    await restore($)
    $.clock.every(POLL_MS, () => check($))
    return next(e)
  })

  on('session.end', async ($, e, next) => {
    generation++
    activeTurn = ''
    steps.clear()
    found = undefined
    shownKey = undefined
    sizes.clear()
    await update($, reply, () => null)
    await update($, images, () => [])
    return next(e)
  })

  on('classic.SessionStart', { source: ['clear', 'resume', 'fork'] }, async ($, e, next) => {
    await restore($)
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    activeTurn = e.turnId
    steps.clear()
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    if (!e.agentId && e.turnId === activeTurn && result.answer) steps.set(e.index, result.answer)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    if (!e.agentId && interactive) {
      const texts = e.turnId === activeTurn ? [...steps.entries()].sort((a, b) => a[0] - b[0]).map(([, text]) => text) : []
      if (e.answer && texts.at(-1) !== e.answer) texts.push(e.answer)
      const text = texts.join('\n\n')
      if (text) await setReply($, text, e.answer)
      else {
        generation++
        await update($, reply, () => null)
      }
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.surface !== 'terminal' || e.props.hasSurvey) return next(e)
    const pasted = await read($, images)
    const previous = await read($, reply)
    if (pasted.length === 0 && !previous) return next(e)

    const { Box, Image, Text, Button } = $.ui.resolve(e)
    const width = Math.max(1, e.props.bodyColumns)
    const maxRows = Math.max(0, e.props.maxRows)
    const below = await next(e)
    if (maxRows < 1 || width < 16) return below
    const all = [
      ...pasted.map(image => ({ ...image, label: `Paste #${image.n}`, target: image.path, status: image.path ? 'ready' : 'unavailable', error: 'no preview' })),
      ...(previous?.media ?? []).map((media, i) => ({ ...media, n: i, label: `${media.kind === 'video' ? 'Video' : 'Image'}: ${media.label}` })),
    ]
    const links = previous?.links.filter(link => link.kind === 'link') ?? []
    const toolbarRows = previous ? 1 : 0
    const linkRows = Math.min(3, links.length, Math.max(0, maxRows - toolbarRows - (all.length ? 2 : 0) - 1))
    const linkPages = linkRows ? Math.ceil(links.length / linkRows) : 0
    const currentLinkPage = Math.min(linkPage, Math.max(0, linkPages - 1))
    const fullPageSize = Math.max(1, Math.min(6, Math.floor((width + 1) / 15)))
    const mediaNavRows = all.length > fullPageSize ? 1 : 0
    const tileBudget = maxRows - toolbarRows - mediaNavRows - (linkRows ? linkRows + 1 : 0)
    const showTiles = all.length > 0 && tileBudget >= 4
    const pageSize = showTiles ? fullPageSize : 1
    const mediaPages = Math.ceil(all.length / pageSize)
    const currentMediaPage = Math.min(mediaPage, Math.max(0, mediaPages - 1))
    const list = all.slice(currentMediaPage * pageSize, (currentMediaPage + 1) * pageSize)
    const cells = fitRow(list.map(image => image.size), tileBudget, width)
    const redraw = () => $.ui.invalidate('ui.render')
    return (
      <Box flexDirection="column">
        {previous && <Box flexDirection="row" columnGap={1}>
          {width >= 40 && <Text dimColor>Last reply</Text>}
          <Button key="copy-reply" label="Copy reply" onPress={async press => {
            try {
              const result = await $.ui.copy({ text: previous.text, surface: press.surface })
              $.ui.toast(result.isCopied ? 'Reply copied' : `Could not copy: ${result.reason}`)
            } catch { $.ui.toast('Could not copy reply') }
          }} />
        </Box>}
        {showTiles && mediaPages > 1 && <Box flexDirection="row" columnGap={1}>
          <Text dimColor>{currentMediaPage + 1}/{mediaPages}</Text>
          <Button key="media-next" label="Next" onPress={() => { mediaPage = (currentMediaPage + 1) % mediaPages; redraw() }} />
        </Box>}
        {showTiles && <Box flexDirection="row" columnGap={1}>
          {list.map((image, i) => {
            const { columns, rows } = cells[i] ?? { columns: 4, rows: 1 }
            return (
              <Box key={`tile-${i}`} flexDirection="column" alignItems="center" width={columns + 2} borderStyle="round" borderDimColor>
                {image.path === null ? (
                  <Box width={columns} height={rows} alignItems="center" justifyContent="center">
                    <Text dimColor wrap="truncate">{image.status === 'pending' ? 'Loading...' : 'no preview'}</Text>
                  </Box>
                ) : (
                  <Image
                    key={`image-${i}`}
                    source={{ file: image.path, format: 'png' }}
                    columns={columns}
                    rows={rows}
                    alt={image.label}
                  />
                )}
                {image.target ? <Button key={`open-media-${i}`} plain label={image.label.slice(0, columns)} onPress={() => action($, { action: 'open', target: image.target }, 'Opened')} /> : <Text dimColor>#{image.n}</Text>}
              </Box>
            )
          })}
        </Box>}
        {!showTiles && all.length > 0 && maxRows > toolbarRows && <Box flexDirection="row" columnGap={1}>
          {width >= 32 && <Text dimColor>{currentMediaPage + 1}/{all.length} media</Text>}
          {list[0]?.target && <Button key="open-compact-media" label="Open" onPress={() => action($, { action: 'open', target: list[0]!.target }, 'Opened')} />}
          {all.length > 1 && <Button key="compact-next" label="Next" onPress={() => { mediaPage = (currentMediaPage + 1) % mediaPages; redraw() }} />}
        </Box>}
        {linkRows > 0 && <Box flexDirection="row" columnGap={1}>
          <Text dimColor>Links</Text>
          {linkPages > 1 && <Button key="links-next" label="Next" onPress={() => { linkPage = (currentLinkPage + 1) % linkPages; redraw() }} />}
        </Box>}
        {links.slice(currentLinkPage * linkRows, currentLinkPage * linkRows + linkRows).map((link, i) => <Box key={`link-${i}`} flexDirection="row" columnGap={1}>
          <Button key={`open-link-${i}`} label="Open" onPress={() => action($, { action: 'open', target: link.target }, 'Opened')} />
          <Text dimColor wrap="truncate">{link.target}</Text>
        </Box>)}
        {below}
      </Box>
    )
  })
}
