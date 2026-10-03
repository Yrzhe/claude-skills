import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { PastedImage } from '../types'
import { imageNumbers, pngSize } from './layout'
import { hoverLayout, linkHref, stripItems, stripLayout } from './strip'
import type { StripItem } from './strip'
import type { Size } from './layout'
import { lastReply, makeReply } from './reply'
import type { Preview, Reply } from '../types'

// Pasting an image raises no prompt.edit (the tag only shows up on the next keystroke),
// so the draft is polled instead.
const POLL_MS = 200

const images = atom({ plugin: 'reply-view', key: 'images' } as const, [] as PastedImage[])
const reply = atom({ plugin: 'reply-view', key: 'reply' } as const, null as Reply | null)
const hovered = atom({ plugin: 'reply-view', key: 'hovered' } as const, null as string | null)
let generation = 0
let scrollOffset = 0
let collapsed = false
let nativeImages = false
let terminalLinks = true
let wanted: StripItem[] = []
let previewTimerStarted = false
let stripBounds: { requestId: string; rows: number; width: number; maxOffset: number } | undefined
let activeTurn = ''
let steps = new Map<number, string>()
let sessionKey = ''
let interactive = true
let previewBusy = false
const nativeSources = new Map<string, { png?: string; size?: Size; error?: string }>()

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
  const item = wanted.find(candidate => candidate.target && !nativeSources.has(candidate.target) &&
    (candidate.kind === 'paste' || current?.media.some(media => media.target === candidate.target && media.status !== 'unavailable')))
  if (!item?.target || token !== generation || previewBusy) return
  previewBusy = true
  try {
    let result: Partial<Preview>
    try {
      let data: { path?: string; size?: Size } = { path: item.path ?? undefined, size: item.size ?? undefined }
      let png: string | undefined
      if (item.kind === 'paste') {
        png = await $.fs.read(item.target, { as: 'bytes' }).then(value => value.base64).catch(() => undefined)
        if (png && png.length > 2796200) png = undefined
      }
      if (!png) {
        data = await helper($, { action: 'preview', target: item.target, kind: item.kind, cacheKey: `${sessionKey}:${token}` })
        if (!data.path || !data.size) throw new Error('No preview available')
        png = (await $.fs.read(data.path, { as: 'bytes' })).base64
      }
      if (!png || png.length > 2796200) throw new Error('Preview exceeds image transport limit')
      if (token !== generation) return
      nativeSources.set(item.target, { png, size: data.size })
      while (nativeSources.size > 12) nativeSources.delete(nativeSources.keys().next().value!)
      result = { path: data.path ?? item.path, size: data.size ?? item.size, status: 'ready' }
    } catch (error) {
      if (token !== generation) return
      nativeSources.set(item.target, { error: 'Preview unavailable' })
      result = { status: 'unavailable', error: error instanceof Error ? error.message : 'No preview available' }
    }
    if (token === generation && item.kind !== 'paste') await update($, reply, value => value && ({ ...value, media: value.media.map(media => media.target === item.target ? { ...media, ...result } : media) }))
    $.ui.invalidate('ui.render')
  } finally { previewBusy = false }
}

async function setReply($: EngineInterface, text: string, answer: string) {
  const token = ++generation
  nativeSources.clear()
  await update($, hovered, () => null)
  scrollOffset = 0
  wanted = []
  const cwd = await $.session.cwd()
  const id = await $.session.id()
  if (token !== generation) return
  sessionKey = id
  const value = makeReply(text, answer, cwd)
  if (value.links.some(link => link.target.startsWith('~/'))) {
    const home = await $.env.get('HOME').catch(() => undefined)
    if (home) {
      for (const link of [...value.links, ...value.media]) {
        if (link.target.startsWith('~/')) link.target = `${home}/${link.target.slice(2)}`
      }
    }
  }
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
    nativeImages = program === 'ghostty' || program === 'kitty' || term === 'xterm-kitty' || await $.env.get('CLAUDE_CODE_FORCE_TERMINAL_IMAGES').catch(() => '') === '1'
    terminalLinks = nativeImages || await $.env.get('FORCE_HYPERLINK').catch(() => '') === '1'
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
    nativeSources.clear()
    await update($, hovered, () => null)
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

  on('ui.message', async ($, e, next) => {
    if (e.module !== 'hooks/hover-link.tsx') return next(e)
    const data = e.data as { action?: string; id?: string } | null
    if (!data || typeof data.id !== 'string' || e.element !== `hover-${data.id}`) return next(e)
    const item = stripItems(await read($, images), await read($, reply)).find(item => item.key === data.id)
    if (!item?.target) return {}
    if (data.action === 'open') await action($, { action: 'open', target: item.target }, 'Opened')
    else if (data.action === 'hover') await update($, hovered, () => item.key)
    else if (data.action === 'leave') await update($, hovered, value => value === item.key ? null : value)
    return {}
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
    const hoveredId = await read($, hovered)
    const below = await next(e)
    const width = Math.floor(e.props.bodyColumns)
    const all = stripItems(pasted, previous)
    if ((!previous && all.length === 0) || width < 20 || e.props.maxRows < 1) {
      wanted = []; stripBounds = undefined; return below
    }
    const { Box, Image, Client, Markdown, Text, Button } = $.ui.resolve(e)
    const layout = stripLayout(all.length, width, e.props.maxRows, scrollOffset)
    const visible = all.slice(layout.start, layout.start + layout.visibleCount)
    const expanded = !collapsed && layout.rows >= 2 && all.length > 0
    const canHoverImage = nativeImages && e.viewport?.isFullscreen === true
    wanted = expanded && canHoverImage ? visible.filter(item => item.kind !== 'link') : []
    const hoverItem = expanded && canHoverImage ? visible.find(item => item.key === hoveredId && item.target && item.kind !== 'link') : undefined
    const hoverSource = hoverItem?.target ? nativeSources.get(hoverItem.target) : undefined
    const hoverSize = hoverItem && e.props.maxRows > 3 ? hoverLayout(hoverSource?.size ?? hoverItem.size, width, e.props.maxRows - 2) : undefined
    const extraRows = hoverSize?.rows ?? 0
    stripBounds = { requestId: e.requestId, rows: expanded ? layout.rows + extraRows : 1, width, maxOffset: layout.maxOffset }

    const move = async (offset: number) => {
      await update($, hovered, () => null)
      scrollOffset = Math.max(0, Math.min(layout.maxOffset, offset))
      wanted = []
      $.ui.invalidate('ui.render')
    }
    return (
      <Box key="reply-strip" flexDirection="column">
        {hoverItem && hoverSize && <Box key="hover-preview" width={width} height={hoverSize.rows} justifyContent="center">
          {hoverSource?.png ? <Image key={`image-${hoverItem.key}`} source={{ png: hoverSource.png }} columns={hoverSize.columns} rows={hoverSize.rows} alt="Open image to view" /> : <Text dimColor>{hoverSource?.error || 'Loading image…'}</Text>}
        </Box>}
        <Box key="strip-toolbar" flexDirection="row" justifyContent="space-between" height={1} width={Math.max(1, width - 4)}>
          <Box key="strip-left" flexDirection="row" columnGap={1}>
            <Button key="scroll-home" plain label={width >= 60 ? 'Start' : '|<'} dimColor={layout.start === 0} onPress={() => move(0)} />
            {layout.maxOffset > 0 && <Button key="scroll-left" plain label="<" dimColor={layout.start === 0} onPress={() => move(layout.start - 1)} />}
            {all.length > 0 && width >= 50 && <Text dimColor>{layout.start + 1}-{Math.min(all.length, layout.start + layout.visibleCount)}/{all.length}</Text>}
            {layout.maxOffset > 0 && <Button key="scroll-right" plain label=">" dimColor={layout.start === layout.maxOffset} onPress={() => move(layout.start + 1)} />}
          </Box>
          <Box key="strip-right" flexDirection="row" columnGap={1}>
            {all.length > 0 && <Button key="toggle-strip" plain label={collapsed ? 'Show' : 'Hide'} onPress={async () => { collapsed = !collapsed; wanted = []; await update($, hovered, () => null); $.ui.invalidate('ui.render') }} />}
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
            const href = item.target ? linkHref(item.target) : undefined
            const prefix = item.kind === 'link' ? 'Open' : item.kind === 'video' ? 'Play video' : 'Open image'
            const name = item.kind === 'paste' ? item.label.replace('Pasted ', '') : item.label
            const label = (name.toLowerCase() === 'image' || name.toLowerCase() === 'video' ? prefix : `${prefix} ${name}`).slice(0, Math.max(8, layout.cardWidth - 1))
            const safeLabel = label.replace(/[\[\]\\`*_<>]/g, '')

            return <Box key={`card-${item.key}`} flexDirection="column" width={layout.cardWidth} height={1}>
              {href && canHoverImage && item.kind !== 'link' ? <Client key={`hover-${item.key}`} module="./hover-link.tsx" props={{ id: item.key, text: `[${safeLabel}](${href})`, href }} width={layout.cardWidth} height={1} /> : href && terminalLinks ? <Markdown key={`open-${item.key}`} text={`[${safeLabel}](${href})`} onLinkPress={link => {
                if (link.href === href) void action($, { action: 'open', target: item.target }, 'Opened')
              }} /> : item.target ? <Button key={`open-${item.key}`} plain label={label} onPress={() => action($, { action: 'open', target: item.target }, 'Opened')} /> : <Text dimColor>Image unavailable</Text>}

            </Box>
          })}
        </Box>}
        {below}
      </Box>
    )
  })
}
