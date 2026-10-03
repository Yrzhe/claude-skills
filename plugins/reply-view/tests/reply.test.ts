import { expect, mock, test, type Mounted } from 'claude-code/testing'
import { extractLinks, lastReply, normalizeTarget } from '../hooks/reply'

const BAND = {
  plugin: 'reply-view', component: 'AbovePrompt', requestId: 'above-prompt',
  viewport: { columns: 120, rows: 40, isFullscreen: true },
  props: { hasSurvey: false, isWorking: false, maxRows: 20, bodyColumns: 120, scroll: { offset: 0, bodyRows: 20 }, view: {} },
} as const
const completed = (answer: string, turnId = 'turn-1') => ({ answer, turnId, durationMs: 100, isAborted: false, reason: 'answer' as const })

async function pressOpen(ui: Mounted<'terminal', 'AbovePrompt'>, key: string) {
  const client = `hover-${key.slice(5)}`
  if (await ui.find({ key: client })) {
    await ui.resize({ in: client, columns: 28, rows: 1 })
    await ui.pointer({ in: client, type: 'down', x: 1, y: 0, button: 'left' })
    await ui.pointer({ in: client, type: 'up', x: 1, y: 0, button: 'left' })
    return
  }
  const node = await ui.find({ key })
  const href = String(node?.props.text).match(/\]\((.*)\)$/)?.[1]
  expect(href).toBeDefined()
  await ui.press({ key, link: { href: href! } })
}
async function linkTargets(ui: Mounted<'terminal', 'AbovePrompt'>) {
  return (await ui.findAll({ type: 'Markdown' })).map(node => String(node.props.text).match(/\]\((.*)\)$/)?.[1])
}

test('extracts ordered media, paths with spaces, signed URLs and localhost without duplicates', () => {
  const links = extractLinks('图片 [封面](</tmp/my cover.png>)，视频 `./out/demo.mp4`。\n[Site](http://localhost:3000/a) and http://localhost:3000/a\nhttps://example.com/a.jpg?token=x&n=1。\nlocalhost:4321/test。', '/work')
  expect(links.map(link => [link.target, link.kind])).toEqual([
    ['/tmp/my cover.png', 'image'], ['/work/out/demo.mp4', 'video'],
    ['http://localhost:3000/a', 'link'], ['https://example.com/a.jpg?token=x&n=1', 'image'], ['http://localhost:4321/test', 'link'],
  ])
})

test('handles parentheses, file URLs, line anchors and Markdown images without extensions', () => {
  expect(extractLinks('[figure](/tmp/figure(1).png) ![chart](https://example.com/render?id=1) [clip.mp4](https://example.com/download?id=2) file:///tmp/cat%20photo.png', '/work').map(link => [link.target, link.kind])).toEqual([
    ['/tmp/figure(1).png', 'image'], ['https://example.com/render?id=1', 'image'], ['https://example.com/download?id=2', 'video'], ['/tmp/cat photo.png', 'image'],
  ])
  expect(normalizeTarget('/tmp/doc.md:12', '/work')).toBe('/tmp/doc.md')
  expect(normalizeTarget('0.0.0.0:3000', '/work')).toBe('http://localhost:3000/')
  expect(normalizeTarget('[::1]:8080', '/work')).toBe('http://[::1]:8080/')
})

test('does not turn executable schemes, embedded shell commands or URL credentials into actions', () => {
  for (const raw of ['javascript:alert(1)', 'data:image/png,abc', 'ftp://host/file.png', 'https://user:pass@example.com/a', 'curl https://example.com/a', 'file://other-host/a.png', '/tmp/x\nopen']) expect(normalizeTarget(raw, '/work')).toBeNull()
  expect(extractLinks('[bad](javascript:alert(1)) ftp://host/a.png', '/work')).toEqual([])
})

test('restores the preceding completed turn including commentary but excluding tool output and user text', () => {
  expect(lastReply([
    { role: 'user', text: 'make a chart', toolUses: [] },
    { role: 'assistant', text: 'I will plot it.', toolUses: [{ name: 'Bash' }] as never },
    { role: 'user', text: 'private tool output', toolUses: [], toolResults: [{ tool_use_id: 'x' }] as never },
    { role: 'assistant', text: 'Done: /tmp/chart.png', toolUses: [] },
    { role: 'user', text: 'next task', toolUses: [] },
  ])).toEqual({ text: 'I will plot it.\n\nDone: /tmp/chart.png', answer: 'Done: /tmp/chart.png' })
})

test('reply media and pasted images coexist; copy and open buttons invoke exact user actions', async ($, on) => {
  const clock = mock.clock(on)
  let draft = '[Image #1]'
  const requests: Record<string, string>[] = []
  on('ui.copy', ($, e) => { requests.push({ action: 'copy', text: e.text }); return { value: { isCopied: true } } })
  on('session.start', () => ({ cwd: '/work' }))
  on('session.messages', () => ({ value: [] }))
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess-1' }))
  on('prompt.read', () => ({ value: { text: draft, cursor: draft.length } }))
  on('env.get', ($, e) => ({ value: e.name === 'TERM_PROGRAM' ? 'ghostty' : '/tmp/claude-test' }))
  on('fs.list', () => ({ value: [] }))
  on('fs.read', () => ({ value: { base64: 'iVBORw0KGgoAAAANSUhEUgAAAoAAAAFoAAAAAAAAAAAA' } }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('process.run', ($, e) => {
    const request = JSON.parse(e.init?.stdin!)
    requests.push(request)
    return { value: { exitCode: 0, isStdoutTruncated: false, isStderrTruncated: false, stderr: '', stdout: JSON.stringify(request.action === 'preview' ? { path: '/tmp/preview.png', size: { width: 640, height: 360 } } : { ok: true }) } }
  })
  on('ui.toast', () => ({ value: undefined }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await clock.advance(200)
  const answer = 'Done: [movie](./demo.mp4) [site](http://localhost:3000/)'
  await $.turn.complete(completed(answer))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await clock.advance(100)
  expect(await ui.find({ type: 'Text', text: 'Image unavailable' })).toBeDefined()
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
  await ui.resize({ in: 'hover-reply-0', columns: 28, rows: 1 })
  await ui.pointer({ in: 'hover-reply-0', type: 'enter', x: 1, y: 0 })
  expect((await ui.find({ type: 'Image' }))?.props).toMatchObject({ source: { png: 'iVBORw0KGgoAAAANSUhEUgAAAoAAAAFoAAAAAAAAAAAA' } })
  await ui.press({ key: 'copy-reply' })
  await pressOpen(ui, 'open-reply-1')
  await pressOpen(ui, 'open-reply-0')
  expect(requests).toEqual([
    { action: 'preview', target: '/work/demo.mp4', kind: 'video', cacheKey: 'sess-1:1' },
    { action: 'copy', text: answer },
    { action: 'open', target: 'http://localhost:3000/' },
    { action: 'open', target: '/work/demo.mp4' },
  ])
  draft = ''
  await clock.advance(200)
  expect(await ui.find({ type: 'Text', text: 'Image unavailable' })).toBeUndefined()
  expect(await ui.find({ key: 'copy-reply' })).toBeDefined()
  await $.turn.complete({ ...completed('subagent text'), agentId: 'child' })
  await ui.press({ key: 'copy-reply' })
  expect(requests.at(-1)).toEqual({ action: 'copy', text: answer })
})

test('copy includes every visible step once, while links come from the final answer only', async ($, on) => {
  mock.clock(on)
  let copied = ''
  on('ui.copy', ($, e) => { copied = e.text; return { value: { isCopied: true } } })
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('turn.step', async function* ($, e) {
    return { turnId: e.turnId, index: e.index, answer: e.index === 0 ? 'Checking http://old.test/' : 'Done http://localhost:3000/', toolUses: [], stopReason: 'end_turn', usage: null }
  })
  on('process.run', ($, e) => {
    copied = JSON.parse(e.init?.stdin!).text
    return { value: { exitCode: 0, isStdoutTruncated: false, isStderrTruncated: false, stderr: '', stdout: '{"ok":true}' } }
  })
  on('ui.toast', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  await $.turn.start({ turnId: 't', text: 'work' })
  for (const index of [0, 1]) {
    const stream = $.turn.step({ turnId: 't', index, model: 'mock', messageCount: 1 })
    for await (const _ of stream) { /* pass through */ }
  }
  await $.turn.complete(completed('Done http://localhost:3000/', 't'))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await ui.press({ key: 'copy-reply' })
  expect(copied).toBe('Checking http://old.test/\n\nDone http://localhost:3000/')
  expect((await linkTargets(ui)).includes('http://old.test/')).toBe(false)
  expect((await linkTargets(ui)).includes('http://localhost:3000/')).toBe(true)
})

test('short bands keep localhost reachable and horizontal scrolling reaches every item', async ($, on) => {
  mock.clock(on)
  const opened: string[] = []
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [] }))
  on('ui.toast', () => ({ value: undefined }))
  on('process.run', ($, e) => {
    opened.push(JSON.parse(e.init?.stdin!).target)
    return { value: { exitCode: 0, isStdoutTruncated: false, isStderrTruncated: false, stderr: '', stdout: '{"ok":true}' } }
  })
  await $.turn.complete(completed('/tmp/a.png /tmp/b.mp4 http://localhost:8080/'))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, maxRows: 5, bodyColumns: 40 } })
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
  await pressOpen(ui, 'open-reply-0')
  await ui.press({ key: 'scroll-right' })
  await pressOpen(ui, 'open-reply-1')
  await ui.press({ key: 'scroll-right' })
  await pressOpen(ui, 'open-reply-2')
  expect(opened).toEqual(['/tmp/a.png', '/tmp/b.mp4', 'http://localhost:8080/'])
})

test('failed previews retain open actions; a newer reply or clear discards pending work', async ($, on) => {
  const clock = mock.clock(on)
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('session.end', () => ({ sessionId: 'sess' }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  on('process.run', () => ({ value: { exitCode: 1, isStdoutTruncated: false, isStderrTruncated: false, stderr: '', stdout: '{"error":"File not found"}' } }))
  on('prompt.read', () => ({ value: { text: '', cursor: 0 } }))
  on('session.start', () => ({ cwd: '/work' }))
  on('session.messages', () => ({ value: [] }))
  on('env.get', () => ({ value: 'ghostty' }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await $.turn.complete(completed('/tmp/missing.mp4'))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await clock.advance(100)
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
  expect(await ui.find({ key: 'hover-reply-0' })).toBeDefined()
  await $.turn.complete(completed('/tmp/queued.png', 't2'))
  await $.session.end({ reason: 'clear', sessionId: 'sess', resume: { id: 'sess' } })
  await clock.advance(10)
  expect(await ui.find({ key: 'copy-reply' })).toBeUndefined()
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
})

test('plaintext replies copy without truncation and clipboard refusal is reported', async ($, on) => {
  mock.clock(on)
  let copied = ''
  let toast = ''
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [] }))
  on('ui.copy', ($, e) => { copied = e.text; return { value: { isCopied: false, reason: 'no-clipboard' } } })
  on('ui.toast', ($, e) => { toast = e.text; return { value: undefined } })
  const answer = '你好\n**Markdown** $HOME `code`\n'.repeat(1000)
  await $.turn.complete(completed(answer))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
  await ui.press({ key: 'copy-reply' })
  expect(copied).toBe(answer)
  expect(toast).toBe('Could not copy: no-clipboard')
})

test('a conversion finishing after clear cannot repopulate the preview', async ($, on) => {
  const clock = mock.clock(on)
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('session.end', () => ({ sessionId: 'sess' }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  let release: (() => void) | undefined
  on('process.run', async () => {
    await new Promise<void>(resolve => { release = resolve })
    return { value: { exitCode: 0, stdout: '{"path":"/tmp/old.png","size":{"width":10,"height":10}}', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('prompt.read', () => ({ value: { text: '', cursor: 0 } }))
  on('session.start', () => ({ cwd: '/work' }))
  on('session.messages', () => ({ value: [] }))
  on('env.get', () => ({ value: 'ghostty' }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await $.turn.complete(completed('/tmp/old.png'))
  const mounted = await $.ui.mount({ ...BAND, surface: 'terminal' })
  const pending = clock.advance(100)
  await clock.settle()
  await $.session.end({ reason: 'clear', sessionId: 'sess', resume: { id: 'sess' } })
  expect(release).toBeDefined()
  release!()
  await pending
  const ui = mounted
  expect(await ui.find({ key: 'copy-reply' })).toBeUndefined()
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
})

test('links and media share one horizontal window', async ($, on) => {
  mock.clock(on)
  const opened: string[] = []
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [] }))
  on('ui.toast', () => ({ value: undefined }))
  on('process.run', ($, e) => {
    opened.push(JSON.parse(e.init?.stdin!).target)
    return { value: { exitCode: 0, stdout: '{"ok":true}', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  await $.turn.complete(completed('/tmp/1.png /tmp/2.png /tmp/3.png http://localhost:3001/ http://localhost:3002/ http://localhost:3003/ http://localhost:3004/'))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, bodyColumns: 30 } })
  for (let i = 0; i < 2; i++) await ui.press({ key: 'scroll-right' })
  await pressOpen(ui, 'open-reply-2')
  for (let i = 0; i < 4; i++) await ui.press({ key: 'scroll-right' })
  await pressOpen(ui, 'open-reply-6')
  expect(opened).toEqual(['/tmp/3.png', 'http://localhost:3004/'])
})


test('slash commands and repository names never become Open links', () => {
  for (const target of ['/plugin', '/plugin install reply-view@yrzhe-skills', 'Yrzhe/claude-skills', '@scope/package']) {
    expect(normalizeTarget(target, '/work')).toBeNull()
  }
  expect(extractLinks('`/plugin` `/plugin install reply-view@yrzhe-skills` `Yrzhe/claude-skills` [site](http://localhost:3000)', '/work').map(x => x.target)).toEqual(['http://localhost:3000/'])
})

test('1000 items keep one row; only visible media loads; Start and Copy stay outside scrolling', async ($, on) => {
  const clock = mock.clock(on)
  const requests: string[] = []
  let copied = ''
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.copy', ($, e) => { copied = e.text; return { value: { isCopied: true } } })
  on('ui.toast', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [] }))
  on('process.run', ($, e) => {
    requests.push(JSON.parse(e.init?.stdin!).target)
    return { value: { exitCode: 1, isStdoutTruncated: false, isStderrTruncated: false, stdout: '{"error":"missing"}', stderr: '' } }
  })
  const answer = Array.from({ length: 1000 }, (_, i) => `/tmp/${i}.png`).join(' ')
  on('prompt.read', () => ({ value: { text: '', cursor: 0 } }))
  on('session.start', () => ({ cwd: '/work' }))
  on('session.messages', () => ({ value: [] }))
  on('env.get', () => ({ value: 'ghostty' }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
  await $.turn.complete(completed(answer))
  await clock.advance(1000)
  expect(requests).toEqual([])
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ key: 'strip-window' }))?.props).toMatchObject({ flexDirection: 'row', height: 1 })
  expect((await ui.findAll({ type: 'Client' })).length).toBe(4)
  expect((await ui.find({ key: 'strip-toolbar' }))?.props).toMatchObject({ flexDirection: 'row', justifyContent: 'space-between', width: 116, height: 1 })
  const left = await ui.find({ key: 'strip-left' })
  const right = await ui.find({ key: 'strip-right' })
  expect(left?.children?.[0]).toMatchObject({ props: { key: 'scroll-home' } })
  expect(right?.children?.at(-1)).toMatchObject({ props: { key: 'copy-reply' } })
  await clock.advance(1000)
  expect(requests).toEqual(['/tmp/0.png', '/tmp/1.png', '/tmp/2.png', '/tmp/3.png'])
  await ui.press({ key: 'scroll-right' })
  expect(await ui.find({ key: 'hover-reply-0' })).toBeUndefined()
  expect(await ui.find({ key: 'hover-reply-4' })).toBeDefined()
  await clock.advance(100)
  expect(requests.at(-1)).toBe('/tmp/4.png')
  await ui.press({ key: 'copy-reply' })
  expect(copied).toBe(answer)
  await ui.press({ key: 'scroll-home' })
  expect(await ui.find({ key: 'hover-reply-0' })).toBeDefined()
  expect(await ui.find({ key: 'strip-window' })).toBeDefined()
  await clock.advance(1000)
  expect(requests.length).toBe(5)
})

test('missing non-media paths are filtered while existing files and websites remain', async ($, on) => {
  mock.clock(on)
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('fs.exists', ($, e) => ({ value: e.path === '/work/README.md' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [] }))
  await $.turn.complete(completed('`/work/missing` `./README.md` http://localhost:3000'))
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await linkTargets(ui)).includes('file:///work/missing')).toBe(false)
  expect((await linkTargets(ui)).includes('file:///work/README.md')).toBe(true)
  expect((await linkTargets(ui)).includes('http://localhost:3000/')).toBe(true)
})
