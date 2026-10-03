import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { PastedImage } from '../types'
import { fitCells, imageNumbers, pngSize } from './layout'
import { pixelCells, stripItems, stripLayout } from './strip'
import type { StripItem } from './strip'
import type { Size } from './layout'
import { lastReply, makeReply } from './reply'
import type { Preview, Reply, PixelPreview } from '../types'

// Pasting an image raises no prompt.edit (the tag only shows up on the next keystroke),
// so the draft is polled instead.
const POLL_MS = 200

const images = atom({ plugin: 'reply-view', key: 'images' } as const, [] as PastedImage[])
const reply = atom({ plugin: 'reply-view', key: 'reply' } as const, null as Reply | null)
let generation = 0
const pixels = atom({ plugin: 'reply-view', key: 'pixels' } as const, {} as Record<string, PixelPreview>)
let scrollOffset = 0
let collapsed = false
let nativeImages = false
let wanted: StripItem[] = []
let previewTimerStarted = false
let stripBounds: { requestId: string; rows: number; width: number; maxOffset: number } | undefined
let activeTurn = ''
let steps = new Map<number, string>()
let sessionKey = ''
let interactive = true
let previewBusy = false

async function helper($: EngineInterface, request: object): Promise<{ path?: string; size?: Size; error?: string; pixels?: string; pixelError?: string }> {
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

// The render hook records only the visible window. A timer performs one job at
// a time outside rendering; scrolling or collapsing stops offscreen downloads.
function startPreviewTimer($: EngineInterface) {
  if (previewTimerStarted) return
  previewTimerStarted = true
  $.clock.every(100, () => prepareVisible($))
}

async function prepareVisible($: EngineInterface) {
  if (previewBusy || collapsed || wanted.length === 0) return
  const token = generation
  const current = await read($, reply)
  const savedPixels = await read($, pixels)
  const item = wanted.find(candidate => {
    if (!candidate.target || candidate.kind === 'link') return false
    if (candidate.kind === 'paste') return !nativeImages && !savedPixels[candidate.target]
    return current?.media.some(media => media.target === candidate.target && media.status === 'pending')
  })
  if (!item?.target || token !== generation || previewBusy) return
  previewBusy = true
  try {
    if (item.kind === 'paste') {
      let result: PixelPreview
      try {
        const data = await helper($, { action: 'pixels', target: item.target })
        result = { pixels: data.pixels, error: data.pixelError || (!data.pixels ? 'Preview unavailable' : undefined) }
      } catch { result = { error: 'Preview unavailable' } }
      if (token === generation) await update($, pixels, value => ({ ...value, [item.target!]: result }))
    } else {
      let result: Partial<Preview>
      try {
        const data = await helper($, { action: 'preview', target: item.target, kind: item.kind, withPixels: !nativeImages, cacheKey: `${sessionKey}:${token}` })
        if (!data.path || !data.size) throw new Error('No preview available')
        result = { path: data.path, size: data.size, pixels: data.pixels, error: data.pixelError, status: 'ready' }
      } catch (error) {
        result = { status: 'unavailable', error: error instanceof Error ? error.message : 'No preview available' }
      }
      if (token === generation) await update($, reply, value => value && ({ ...value, media: value.media.map(media => media.target === item.target ? { ...media, ...result } : media) }))
    }
  } finally { previewBusy = false }
}

async function setReply($: EngineInterface, text: string, answer: string) {
  const token = ++generation
  scrollOffset = 0
  wanted = []
  const cwd = await $.session.cwd()
  const id = await $.session.id()
  if (token !== generation) return
  sessionKey = id
  const value = makeReply(text, answer, cwd)
  const existing = await Promise.all(value.links.map(async link => link.kind !== 'link' || /^https?:/.test(link.target) || await $.fs.exists(link.target).catch(() => false)))
  value.links = value.links.filter((_, index) => existing[index])
  if (token !== generation) return
  await update($, reply, () => value)
  startPreviewTimer($)
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
    const program = (await $.env.get('TERM_PROGRAM').catch(() => '') ?? '').toLowerCase()
    const term = (await $.env.get('TERM').catch(() => '') ?? '').toLowerCase()
    nativeImages = program === 'ghostty' || program === 'kitty' || term === 'xterm-kitty'
    await restore($)
    startPreviewTimer($)
    $.clock.every(POLL_MS, () => check($))
    return next(e)
  })

  on('session.end', async ($, e, next) => {
    generation++
    wanted = []
    stripBounds = undefined
    scrollOffset = 0
    activeTurn = ''
    steps.clear()
    found = undefined
    shownKey = undefined
    sizes.clear()
    await update($, reply, () => null)
    await update($, images, () => [])
    await update($, pixels, () => ({}))
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

  on('ui.scroll', { component: 'AbovePrompt' }, async ($, e, next) => {
    const box = stripBounds
    if (!box || collapsed || e.requestId !== box.requestId || e.origin.kind !== 'person' || !e.pointer ||
      e.pointer.row < 1 || e.pointer.row >= box.rows || e.pointer.column < 0 || e.pointer.column >= box.width || box.maxOffset === 0) return next(e)
    scrollOffset = Math.max(0, Math.min(box.maxOffset, scrollOffset + Math.sign(e.by)))
    wanted = []
    $.ui.invalidate('ui.render')
    return {}
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.surface !== 'terminal' || e.props.hasSurvey) { wanted = []; return next(e) }
    const pasted = await read($, images)
    const previous = await read($, reply)
    const pixelPreviews = await read($, pixels)
    const below = await next(e)
    const width = Math.floor(e.props.bodyColumns)
    const all = stripItems(pasted, previous)
    if ((!previous && all.length === 0) || width < 20 || e.props.maxRows < 1) {
      wanted = []; stripBounds = undefined; return below
    }
    const { Box, Image, Raster, Text, Button } = $.ui.resolve(e)
    const layout = stripLayout(all.length, width, e.props.maxRows, scrollOffset)
    const visible = all.slice(layout.start, layout.start + layout.visibleCount)
    const expanded = !collapsed && layout.rows >= 3 && all.length > 0
    wanted = expanded && layout.pictureRows > 0 ? visible.filter(item => item.kind !== 'link') : []
    stripBounds = { requestId: e.requestId, rows: expanded ? layout.rows : 1, width, maxOffset: layout.maxOffset }
    const move = (offset: number) => {
      scrollOffset = Math.max(0, Math.min(layout.maxOffset, offset))
      wanted = []
      $.ui.invalidate('ui.render')
    }
    return (
      <Box key="reply-strip" flexDirection="column">
        <Box key="strip-toolbar" flexDirection="row" justifyContent="space-between" height={1} width={Math.max(1, width - 4)}>
          <Box key="strip-left" flexDirection="row" columnGap={1}>
            <Button key="scroll-home" plain label={width >= 60 ? 'Start' : '|<'} dimColor={layout.start === 0} onPress={() => move(0)} />
            {layout.maxOffset > 0 && <Button key="scroll-left" plain label="<" dimColor={layout.start === 0} onPress={() => move(layout.start - 1)} />}
            {all.length > 0 && width >= 50 && <Text dimColor>{layout.start + 1}-{Math.min(all.length, layout.start + layout.visibleCount)}/{all.length}</Text>}
            {layout.maxOffset > 0 && <Button key="scroll-right" plain label=">" dimColor={layout.start === layout.maxOffset} onPress={() => move(layout.start + 1)} />}
          </Box>
          <Box key="strip-right" flexDirection="row" columnGap={1}>
            {all.length > 0 && <Button key="toggle-strip" plain label={collapsed ? 'Show' : 'Hide'} onPress={() => { collapsed = !collapsed; wanted = []; $.ui.invalidate('ui.render') }} />}
            {previous && <Button key="copy-reply" plain label={width >= 60 ? 'Copy reply' : 'Copy'} onPress={async press => {
              try {
                const result = await $.ui.copy({ text: previous.text, surface: press.surface })
                $.ui.toast(result.isCopied ? 'Reply copied' : `Could not copy: ${result.reason}`)
              } catch { $.ui.toast('Could not copy reply') }
            }} />}
          </Box>
        </Box>
        {expanded && <Box key="strip-window" flexDirection="row" columnGap={2} height={layout.rows - 1} width={width}>
          {visible.map(item => {
            const pixel = item.kind === 'paste' && item.target ? pixelPreviews[item.target] : undefined
            const samples = item.pixels || pixel?.pixels
            const fit = fitCells(item.size, Math.max(1, layout.pictureRows))
            const columns = Math.min(fit.columns, layout.cardWidth)
            const rows = Math.max(1, Math.min(fit.rows, Math.round(fit.rows * columns / fit.columns)))
            const placeholder = item.kind === 'link' ? item.target! : item.status === 'unavailable' ? 'Preview unavailable' : !nativeImages && !samples && (pixel?.error || item.status === 'ready' && item.kind !== 'paste') ? 'Open to view' : 'Loading preview'
            return <Box key={`card-${item.key}`} flexDirection="column" width={layout.cardWidth} height={layout.rows - 1}>
              <Text dimColor wrap="truncate">{item.kind === 'paste' ? item.label : `${item.kind === 'link' ? 'Link' : item.kind === 'video' ? 'Video' : 'Image'}: ${item.label}`}</Text>
              {layout.pictureRows > 0 && <Box width={layout.cardWidth} height={layout.pictureRows} justifyContent="center" alignItems="center">
                {item.kind !== 'link' && nativeImages && item.path ? <Image key={`image-${item.key}`} source={{ file: item.path, format: 'png' }} columns={columns} rows={rows} alt="Open to view" /> :
                 item.kind !== 'link' && samples ? <Raster key={`pixels-${item.key}`} columns={layout.cardWidth} rows={layout.pictureRows} cells={pixelCells(samples, item.size, layout.cardWidth, layout.pictureRows)} /> :
                 <Text dimColor wrap="truncate">{placeholder}</Text>}
              </Box>}
              {item.target ? <Button key={`open-${item.key}`} plain label={item.kind === 'link' ? 'Open link' : item.kind === 'video' ? 'Play video' : 'Open image'} onPress={() => action($, { action: 'open', target: item.target }, 'Opened')} /> : <Text dimColor>File unavailable</Text>}
            </Box>
          })}
        </Box>}
        {below}
      </Box>
    )
  })
}
