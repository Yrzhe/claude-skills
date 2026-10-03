import { expect, mock, test } from 'claude-code/testing'
import { extractLinks, lastReply, normalizeTarget } from '../hooks/reply'

const BAND = {
  plugin: 'reply-view', component: 'AbovePrompt', requestId: 'above-prompt',
  viewport: { columns: 120, rows: 40 },
  props: { hasSurvey: false, isWorking: false, maxRows: 20, bodyColumns: 120, scroll: { offset: 0, bodyRows: 20 }, view: {} },
} as const
const completed = (answer: string, turnId = 'turn-1') => ({ answer, turnId, durationMs: 100, isAborted: false, reason: 'answer' as const })

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
  on('env.get', () => ({ value: '/tmp/claude-test' }))
  on('fs.list', () => ({ value: [] }))
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
  await clock.advance(10)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: '#1' })).toBeDefined()
  expect((await ui.find({ type: 'Image' }))?.props).toMatchObject({ source: { file: '/tmp/preview.png', format: 'png' } })
  await ui.press({ key: 'copy-reply' })
  await ui.press({ key: 'open-link-0' })
  await ui.press({ key: 'open-media-1' })
  expect(requests).toEqual([
    { action: 'preview', target: '/work/demo.mp4', kind: 'video', cacheKey: 'sess-1:1' },
    { action: 'copy', text: answer },
    { action: 'open', target: 'http://localhost:3000/' },
    { action: 'open', target: '/work/demo.mp4' },
  ])
  draft = ''
  await clock.advance(200)
  expect(await ui.find({ type: 'Text', text: '#1' })).toBeUndefined()
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
  expect(await ui.find({ type: 'Text', text: 'http://old.test/' })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: 'http://localhost:3000/' })).toBeDefined()
})

test('short bands keep localhost reachable and compact media pagination reaches every item', async ($, on) => {
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
  await ui.press({ key: 'open-link-0' })
  await ui.press({ key: 'open-compact-media' })
  await ui.press({ key: 'compact-next' })
  await ui.press({ key: 'open-compact-media' })
  expect(opened).toEqual(['http://localhost:8080/', '/tmp/a.png', '/tmp/b.mp4'])
})

test('failed previews retain open actions; a newer reply or clear discards pending work', async ($, on) => {
  const clock = mock.clock(on)
  on('session.cwd', () => ({ value: '/work' }))
  on('session.id', () => ({ value: 'sess' }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('session.end', () => ({ sessionId: 'sess' }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: ['engine band'] }))
  on('process.run', () => ({ value: { exitCode: 1, isStdoutTruncated: false, isStderrTruncated: false, stderr: '', stdout: '{"error":"File not found"}' } }))
  await $.turn.complete(completed('/tmp/missing.mp4'))
  await clock.advance(10)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: 'no preview' })).toBeDefined()
  expect(await ui.find({ key: 'open-media-0' })).toBeDefined()
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
  await $.turn.complete(completed('/tmp/old.png'))
  const pending = clock.advance(1)
  await clock.settle()
  await $.session.end({ reason: 'clear', sessionId: 'sess', resume: { id: 'sess' } })
  expect(release).toBeDefined()
  release!()
  await pending
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ key: 'copy-reply' })).toBeUndefined()
  expect(await ui.find({ type: 'Image' })).toBeUndefined()
})

test('many links and media remain reachable after paging', async ($, on) => {
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
  await ui.press({ key: 'media-next' })
  await ui.press({ key: 'open-media-0' })
  await ui.press({ key: 'links-next' })
  await ui.press({ key: 'open-link-0' })
  expect(opened).toEqual(['/tmp/3.png', 'http://localhost:3004/'])
})
