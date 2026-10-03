import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import { isControlPrompt, nextSegment, wrapLines, markdownParts } from '../hooks/core'
const CONFIG = {
  enabled: true, incomingLanguage: 'en', outgoingLanguage: 'zh', detection: 'script',
  baseUrl: 'http://localhost:9999/v1', postUrl: '', model: 'test', baseUrlEnv: '', apiKeyEnv: '', modelEnv: '',
  jevUrl: 'https://api.typesafe.ai/v1/systemone', jevKeyEnv: 'TYPESAFE_API_KEY', jevModel: 'jev-latest',
  incomingPrompt: 'Translate to {target_language}', outgoingPrompt: 'Translate to {target_language}',
  hasApiKey: true, hasJevKey: false, ready: true,
}
const PANE = {
  plugin: 'translate-view', component: 'Pane', requestId: 'translate-view', surface: 'terminal',
  viewport: { columns: 160, rows: 40, isFullscreen: true },
  props: { title: 'Translation', isFocused: true, bodyColumns: 52, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const
function setup(on: On, config = CONFIG, inspect?: (request: any) => any, composer = { text: '', fills: [] as string[] }) {
  const clock = mock.clock(on)
  on('session.start', () => ({ cwd: '/work' }))
  on('command.register', () => ({ value: { command: 'translate' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.scroll', () => ({}))
  on('prompt.read', () => ({ value: { text: composer.text, cursor: composer.text.length } }))
  on('prompt.fill', ($, e) => { composer.fills.push(e.text); return { isFilled: true } })
  on('ui.render', ($, e) => ({ type: 'Text', props: {}, children: [e.component === 'UserMessage' ? e.props.text : 'engine'] }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('process.run', ($, e) => {
    const request = JSON.parse(e.init?.stdin ?? '{}')
    const override = inspect?.(request)
    const result = override ?? (request.action === 'load' ? config : request.action === 'save' ? { ...config, ...request.patch } : { text: 'Please fix it.', skipped: false })
    return { value: { exitCode: 0, stdout: JSON.stringify(result), stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return clock
}
const start = { cwd: '/work', surface: 'terminal', isInteractive: true } as const
const done = (answer: string, turnId = 't') => ({ answer, turnId, reason: 'answer', isAborted: false, durationMs: 100 }) as const

test('paragraph batching does not split fenced code and flushes final short replies', () => {
  const paragraph = 'First paragraph. '.repeat(12) + '\n\n'
  const source = paragraph + '```py\nprint("x")\n\n'
  expect(nextSegment(source, 0, false)).toBe(paragraph)
  expect(nextSegment(source, paragraph.length, false)).toBeUndefined()
  expect(nextSegment('Done.', 0, true)).toBe('Done.')
})
test('CJK wrapping fits a narrow sidebar and strips terminal control sequences', () => {
  expect(wrapLines('你好世界', 4)).toEqual(['你好', '世界'])
  expect(wrapLines('\x1b[31mhello\x1b[0m', 10)).toEqual(['hello'])
})
test('submission translates only human text and preserves attachments and context', async ($, on) => {
  setup(on)
  let received: any
  on('prompt.submit', ($, e) => { received = e; return { text: e.text } })
  await $.session.start(start)
  const attachments = [{ type: 'image', mediaType: 'image/png', filename: 'test.png' }] as const
  await $.prompt.submit({ text: '请修复它。', origin: { kind: 'composer' }, wait: true, attachments, context: ['keep context'] })
  expect(received.text).toBe('Please fix it.')
  expect(received.attachments).toEqual(attachments)
  expect(received.context).toEqual(['keep context'])
  expect(received.wait).toBe(true)

})
test('slash commands, shell mode, peer messages and disabled translation pass through', async ($, on) => {
  let calls = 0
  setup(on, CONFIG, req => { if (req.action === 'translate') calls++ })
  on('prompt.submit', ($, e) => ({ text: e.text }))
  await $.session.start(start)
  for (const text of ['/plugin update', '!git status']) {
    expect((await $.prompt.submit({ text, origin: { kind: 'composer' }, wait: false })).text).toBe(text)
  }
  expect((await $.prompt.submit({ text: '你好', origin: { kind: 'peer' }, wait: false })).text).toBe('你好')
  expect(calls).toBe(0)
})
test('incoming translation errors block sending instead of dropping or altering the original', async ($, on) => {
  setup(on, CONFIG, req => req.action === 'translate' ? { error: 'timeout' } : undefined)
  let sent = false
  on('prompt.submit', ($, e) => { sent = true; return { text: e.text } })
  await $.session.start(start)
  const result = await $.prompt.submit({ text: '请修复', origin: { kind: 'composer' }, wait: false })
  expect(result.drop).toContain('timeout')
  expect(sent).toBe(false)
})
test('settings save both language directions, detector, model and custom prompts; keys are not prefilled', async ($, on) => {
  let saved: any
  setup(on, CONFIG, req => { if (req.action === 'save') saved = req.patch })
  await $.session.start(start)
  const ui = await $.ui.mount(PANE)
  await ui.press({ key: 'settings-button' })
  await ui.select({ key: 'incomingLanguage', value: 'zh' })
  await ui.select({ key: 'outgoingLanguage', value: 'en' })
  await ui.select({ key: 'detection', value: 'jev' })
  await ui.press({ key: 'tab-llm' })
  expect((await ui.find({ key: 'input-apiKey' }))?.props.value).toBe('')
  await ui.input({ key: 'input-model', text: 'new-model' })
  await ui.press({ key: 'tab-prompt' })
  await ui.input({ key: 'input-incomingPrompt', text: 'Send as {target_language}.' })
  await ui.input({ key: 'input-outgoingPrompt', text: 'Read in {target_language}.' })
  await ui.press({ key: 'save-settings' })
  expect(saved).toMatchObject({ incomingLanguage: 'zh', outgoingLanguage: 'en', detection: 'jev', model: 'new-model', incomingPrompt: 'Send as {target_language}.', outgoingPrompt: 'Read in {target_language}.' })
  expect(await ui.find({ key: 'translation-body' })).toBeDefined()
})
test('streamed answer is unchanged and translation arrives in a separate pane', async ($, on) => {
  const clock = setup(on)
  on('turn.step', async function* ($, e) {
    yield { kind: 'text', index: 0, text: 'Here is the answer.\n\n' } as const
    return { ...e, answer: 'Here is the answer.\n\n', toolUses: [], stopReason: 'end_turn', usage: null }
  })
  on('process.spawn', async function* () {
    yield { stream: 'stdout', text: '{"type":"partial","text":"这是"}\n' } as const
    yield { stream: 'stdout', text: '{"type":"done","text":"这是答案。\\n\\n","skipped":false}\n' } as const
    return { value: { code: 0, signal: null } }
  })
  await $.session.start(start)
  await $.turn.start({ text: 'hello', turnId: 't' })
  const stream = $.turn.step({ turnId: 't', index: 0, model: 'mock', messageCount: 1 })
  const chunks = []
  for await (const chunk of stream) chunks.push(chunk)
  expect(chunks).toEqual([{ kind: 'text', index: 0, text: 'Here is the answer.\n\n' }])
  await $.turn.complete(done('Here is the answer.\n\n'))
  await clock.advance(250)
  const ui = await $.ui.mount(PANE)
  expect(JSON.stringify(await ui.findAll({ type: 'Markdown' }))).toContain('这是答案。')
  expect(await ui.find({ key: 'settings-button' })).toBeDefined()
})
test('long translations scroll while header and target languages stay visible', async ($, on) => {
  const clock = setup(on)
  on('process.spawn', async function* () {
    yield { stream: 'stdout', text: JSON.stringify({ type: 'done', text: Array.from({ length: 100 }, (_, i) => `line-${i}`).join('\n') }) + '\n' } as const
    return { value: { code: 0, signal: null } }
  })
  await $.session.start(start)
  await $.turn.start({ text: 'hello', turnId: 't' })
  await $.turn.complete(done('Long answer.'))
  await clock.advance(250)
  const ui = await $.ui.mount(PANE)
  expect(JSON.stringify(await ui.findAll({ type: 'Markdown' }))).toContain('line-99')
  await $.ui.scroll({ component: 'Pane', requestId: 'translate-view', offset: 0, by: -100, bodyRows: 30, contentRows: 100, origin: { kind: 'person' } })
  expect(JSON.stringify(await ui.findAll({ type: 'Markdown' }))).toContain('line-0')
  await ui.redraw({ ...PANE.props, scroll: { offset: 37, bodyRows: 30 } })
  expect((await ui.find({ key: 'sticky-header' }))?.props.top).toBe(37)
  expect(await ui.find({ key: 'agent-language' })).toBeDefined()
  expect(await ui.find({ key: 'settings-button' })).toBeDefined()
})
test('subagent answers do not appear or trigger translation calls', async ($, on) => {
  const clock = setup(on)
  let calls = 0
  on('process.spawn', async function* () { calls++; return { value: { code: 0, signal: null } } })
  await $.session.start(start)
  await $.turn.start({ text: 'hello', turnId: 't' })
  await $.turn.complete({ ...done('Private worker answer.'), agentId: 'worker' })
  await clock.advance(250)
  expect(calls).toBe(0)
})

test('disabled plugin leaves human prompts unchanged and makes no translation calls', async ($, on) => {
  let calls = 0
  setup(on, { ...CONFIG, enabled: false }, req => { if (req.action === 'translate') calls++ })
  on('prompt.submit', ($, e) => ({ text: e.text }))
  await $.session.start(start)
  expect((await $.prompt.submit({ text: '请帮我', origin: { kind: 'composer' }, wait: false })).text).toBe('请帮我')
  expect(calls).toBe(0)
})
test('late output from a superseded turn cannot replace the new translation', async ($, on) => {
  const clock = setup(on)
  let release: (() => void) | undefined
  let began: (() => void) | undefined
  const started = new Promise<void>(resolve => { began = resolve })
  on('process.spawn', async function* ($, e) {
    const request = JSON.parse(e.input!)
    if (request.text === 'Old answer.') {
      began!()
      await new Promise<void>(resolve => { release = resolve })
      yield { stream: 'stdout', text: '{"type":"done","text":"旧译文"}\n' } as const
    } else yield { stream: 'stdout', text: '{"type":"done","text":"新译文"}\n' } as const
    return { value: { code: 0, signal: null } }
  })
  await $.session.start(start)
  await $.turn.start({ text: 'old', turnId: 't' })
  await $.turn.complete(done('Old answer.'))
  const pending = clock.advance(250)
  await started
  await $.turn.start({ text: 'new', turnId: 't2' })
  await $.turn.complete(done('New answer.', 't2'))
  release!()
  await pending
  await clock.advance(250)
  const ui = await $.ui.mount(PANE)
  const content = JSON.stringify(await ui.findAll({ type: 'Markdown' }))
  expect(content).toContain('新译文')
  expect(content.includes('旧译文')).toBe(false)
})
test('translation streaming failure exposes retry and preserves the main response', async ($, on) => {
  const clock = setup(on)
  let count = 0
  on('process.spawn', async function* () {
    count++
    yield { stream: 'stdout', text: JSON.stringify(count === 1 ? { type: 'error', error: 'endpoint unavailable' } : { type: 'done', text: '已恢复' }) + '\n' } as const
    return { value: { code: count === 1 ? 1 : 0, signal: null } }
  })
  await $.session.start(start)
  await $.turn.start({ text: 'hello', turnId: 't' })
  const original = await $.turn.complete(done('Original answer.'))
  await clock.advance(250)
  const ui = await $.ui.mount(PANE)
  expect(JSON.stringify(await ui.findAll({ type: 'Text' }))).toContain('endpoint unavailable')
  expect(original.text).toBe('Original answer.')
  await ui.press({ key: 'retry' })
  await clock.advance(250)
  expect(JSON.stringify(await ui.findAll({ type: 'Markdown' }))).toContain('已恢复')
})

// session.append is an engine-pinned event: its terminal persistence is exercised
// by tests/terminal_smoke.py, not a forged bottom hook in the mod test runner.
test('original prompt rendering is keyed by message identity, not identical translated text', async ($, on) => {
  setup(on)
  on('state.get', () => ({ value: { value: { first: '请修好', second: '帮我修好' }, version: 1 } }))
  for (const [requestId, original] of [['first', '请修好'], ['second', '帮我修好']]) {
    const ui = await $.ui.mount({ plugin: 'translate-view', component: 'UserMessage', requestId: requestId!, surface: 'terminal', props: { text: 'Please fix it.', origin: { kind: 'composer' }, isExpanded: false } })
    expect(JSON.stringify(await ui.findAll({ type: 'Text' }))).toContain(original!)
  }
})

test('file paths and Markdown images can be translated while commands retain their meaning', () => {
  expect(isControlPrompt('/plugin update')).toBe(true)
  expect(isControlPrompt('!git status')).toBe(true)
  expect(isControlPrompt('/Users/me/file.ts 请解释这个文件')).toBe(false)
  expect(isControlPrompt('![图片](https://example.com/a.png) 请解释')).toBe(false)
})

test('failed input recovery preserves the next draft and appends only on explicit recovery', async ($, on) => {
  const composer = { text: '正在写下一条', fills: [] as string[] }
  setup(on, CONFIG, req => req.action === 'translate' ? { error: 'unavailable' } : undefined, composer)
  on('prompt.submit', ($, e) => ({ text: e.text }))
  await $.session.start(start)
  await $.prompt.submit({ text: '上一条未发送内容', origin: { kind: 'composer' }, wait: false })
  expect(composer.fills).toEqual([])
  const ui = await $.ui.mount(PANE)
  await ui.press({ key: 'recover-input' })
  expect(composer.fills).toEqual(['\n\n上一条未发送内容'])
  expect(composer.text).toBe('正在写下一条')
  expect(await ui.find({ key: 'recover-input' })).toBeUndefined()
})

test('Markdown chunks preserve formatting and fence boundaries within native leaf limits', () => {
  const markdown = '# Title\n\n**Bold** and `code`.\n\n- one\n- two\n\n```py\nprint("x")\n\nprint("y")\n```\n'
  expect(markdownParts(markdown)).toEqual([{ text: markdown, plain: false }])
  const long = (markdown + '\n').repeat(200)
  const chunks = markdownParts(long)
  expect(chunks.map(part => part.text).join('')).toBe(long)
  expect(chunks.every(part => part.text.length <= 10000 && !part.plain)).toBe(true)
  const huge = '```text\n' + 'x'.repeat(24000) + '\n```'
  expect(markdownParts(huge).map(part => part.text).join('')).toBe(huge)
  expect(markdownParts(huge).every(part => part.plain && part.text.length <= 10000)).toBe(true)
})

test('finished replies merge paragraph backlog into one request and live batches keep complete paragraphs', () => {
  const answer = 'A short paragraph.\n\n'.repeat(80)
  expect(nextSegment(answer, 0, true)).toBe(answer)
  const live = nextSegment(answer, 0, false)!
  expect(live.length > 1000 && live.length <= 1600).toBe(true)
  expect(answer.startsWith(live)).toBe(true)
  expect(nextSegment('Short opening.\n\n', 0, false)).toBeUndefined()
})

test('settings expose detector, environment fields and reset to the language overview on reopen', async ($, on) => {
  let saved: any
  setup(on, CONFIG, req => { if (req.action === 'save') saved = req.patch })
  await $.session.start(start)
  const ui = await $.ui.mount(PANE)
  await ui.press({ key: 'settings-button' })
  expect((await ui.find({ key: 'tab-language' }))?.props.label).toBe('● 语言检测')
  expect(await ui.find({ key: 'detection' })).toBeDefined()
  await ui.select({ key: 'detection', value: 'llm' })
  await ui.input({ key: 'input-detectionModel', text: 'gemini-example' })
  await ui.press({ key: 'tab-env' })
  for (const key of ['baseUrlEnv', 'apiKeyEnv', 'modelEnv']) expect(await ui.find({ key: `input-${key}` })).toBeDefined()
  await ui.select({ key: 'envConfigSource', value: 'env' })
  await ui.input({ key: 'input-apiKeyEnv', text: 'MY_TRANSLATOR_KEY' })
  await ui.press({ key: 'tab-prompt' })
  await ui.press({ key: 'save-settings' })
  expect(saved).toMatchObject({ detection: 'llm', detectionModel: 'gemini-example', llmConfigSource: 'env', apiKeyEnv: 'MY_TRANSLATOR_KEY' })
  await ui.press({ key: 'settings-button' })
  expect((await ui.find({ key: 'tab-language' }))?.props.label).toBe('● 语言检测')
  await ui.redraw({ ...PANE.props, scroll: { offset: 17, bodyRows: 12 } })
  expect((await ui.find({ key: 'settings-header' }))?.props.top).toBe(17)
  await ui.redraw({ ...PANE.props, bodyColumns: 22, scroll: { offset: 0, bodyRows: 23 } })
  expect((await ui.find({ key: 'settings-header' }))?.props.height).toBe(8)
  expect((await ui.findAll({ type: 'Button' })).filter(item => String(item.props.key || '').startsWith('tab-')).length).toBe(5)
})
