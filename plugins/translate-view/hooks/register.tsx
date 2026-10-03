import { atom, read, update } from 'claude-code'
import type { EngineInterface, HookStream, ProcessSpawnChunk, ProcessSpawnResult, Register } from 'claude-code'
import { isControlPrompt, languageOptions, nextSegment, wrapLines } from './core'
import type { Config } from './core'

const PANE = 'translate-view'
let cfg: Config | undefined
let draft: Record<string, unknown> = {}
let page = ''
let tab = 'language'
let notice = ''
let interactive = false
let activeTurn = ''
let generation = 0
let busy = false
let offset = 0
let follow = true
let viewRows = 1
let linesCount = 1
let currentStream: HookStream<ProcessSpawnChunk, ProcessSpawnResult> | undefined
const displayOriginals = atom({ plugin: 'translate-view', key: 'originals' } as const, {} as Record<string, string>)
let originals = new Map<string, { original: string }[]>()
let failedPrompts: string[] = []
let job: { source: string; cursor: number; done: boolean; pieces: string[]; pending: string; error: string; skipped: boolean } | undefined

function redraw($: EngineInterface) { $.ui.invalidate('ui.render') }
function reset(source = '', done = false) {
  generation++
  const stream = currentStream
  currentStream = undefined
  if (stream) { void stream.result.catch(() => {}); void stream.return({ code: null, signal: 'SIGTERM' }).catch(() => {}) }
  job = { source, cursor: 0, done, pieces: [], pending: '', error: '', skipped: true }
  offset = 0; follow = true
}
async function recover($: EngineInterface, text: string) {
  const current = await $.prompt.read().catch(() => null)
  if (current && !current.text) {
    const result = await $.prompt.fill({ text, mode: 'append' }).catch(() => null)
    if (result?.isFilled) return
  }
  failedPrompts.push(text)
}
async function helper($: EngineInterface, data: object): Promise<Record<string, any>> {
  const result = await $.process.run(['python3', `${$.plugin.root}/scripts/translate.py`], { stdin: JSON.stringify(data), timeoutMs: 95000 })
  let value
  try { value = JSON.parse(result.stdout) } catch { throw new Error('翻译服务未返回有效结果。') }
  if (result.exitCode !== 0 || value.error) throw new Error(value.error || '翻译失败。')
  return value
}
async function load($: EngineInterface) {
  cfg = await helper($, { action: 'load' }) as Config
}
async function open($: EngineInterface, settings = false) {
  if (!cfg) await load($)
  if (settings || !cfg?.enabled) { page = 'settings'; draft = { ...cfg }; tab = 'language' }
  await $.ui.open({ id: PANE, title: 'Translation', columns: 52, rows: 24 })
  redraw($)
}
async function save($: EngineInterface, patch: Record<string, unknown>, close = true) {
  try {
    cfg = await helper($, { action: 'save', patch }) as Config
    draft = { ...cfg }; notice = '已保存'; if (close) page = ''
    const source = job?.source ?? ''; const done = job?.done ?? true
    reset(source, done)
  } catch (e) { notice = e instanceof Error ? e.message : '保存失败。' }
  redraw($)
}
async function pump($: EngineInterface) {
  if (busy || !cfg?.enabled || !job || job.error) return
  const segment = nextSegment(job.source, job.cursor, job.done)
  if (!segment) return
  busy = true
  const token = generation, target = job
  let buffer = '', final: { text: string; skipped?: boolean } | undefined
  try {
    const stream = $.process.spawn({ argv: ['python3', `${$.plugin.root}/scripts/translate.py`], input: JSON.stringify({ action: 'stream', direction: 'outgoing', text: segment }) })
    currentStream = stream
    for await (const chunk of stream) {
      if (token !== generation) break
      if (chunk.stream !== 'stdout') continue
      buffer += chunk.text
      if (buffer.length > 2_000_000) throw new Error('译文过长。')
      let at: number
      while ((at = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, at); buffer = buffer.slice(at + 1)
        if (!line.trim()) continue
        const data = JSON.parse(line)
        if (data.type === 'error') throw new Error(data.error)
        if (data.type === 'partial' && typeof data.text === 'string') target.pending = data.text
        if (data.type === 'done' && typeof data.text === 'string') final = data
      }
      redraw($)
    }
    if (token !== generation) return
    const result = await stream.result
    if (result.code !== 0 || !final) throw new Error('翻译流未完成，请重试。')
    target.pieces.push(final.text); target.pending = ''; target.cursor += segment.length
    target.skipped = target.skipped && final.skipped === true
  } catch (e) {
    if (token === generation) { target.pending = ''; target.error = e instanceof Error ? e.message : '翻译失败。' }
  } finally {
    currentStream = undefined; busy = false; redraw($)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    interactive = e.isInteractive && e.surface === 'terminal'
    await $.command.register({ name: 'translate', description: 'Open translation pane or settings', argumentHint: '[settings|on|off]', immediate: true })
    try { await load($) } catch (e) { notice = e instanceof Error ? e.message : '配置读取失败。' }
    if (interactive && cfg) await open($)
    $.clock.every(250, () => pump($))
    return next(e)
  })
  on('command.run', { command: 'translate' }, async ($, e) => {
    if (e.args.trim() === 'off' || e.args.trim() === 'on') await save($, { enabled: e.args.trim() === 'on' })
    await open($, e.args.trim() === 'settings')
    return { text: '' }
  })
  on('session.end', ($, e, next) => { reset(); originals.clear(); return next(e) })
  on('classic.SessionStart', { source: 'clear' }, async ($, e, next) => { reset(); originals.clear(); failedPrompts = []; await update($, displayOriginals, () => ({})); redraw($); return next(e) })
  on('prompt.submit', async ($, e, next) => {
    if (!cfg?.enabled || !['composer', 'bridge', 'sdk'].includes(e.origin.kind) || !e.text.trim() || isControlPrompt(e.text)) return next(e)
    let pending: { original: string } | undefined
    let pendingKey = ''
    let entered = false
    try {
      const translated = await helper($, { action: 'translate', direction: 'incoming', text: e.text })
      if (typeof translated.text !== 'string' || !translated.text.trim()) throw new Error('未收到有效译文。')
      if (translated.text !== e.text) {
        pending = { original: e.text }; pendingKey = translated.text
        originals.set(translated.text, [...(originals.get(translated.text) ?? []), pending])
        while (originals.size > 100) originals.delete(originals.keys().next().value!)
      }
      // Attachments/context/wait/origin are passed through, never sent to the translator.
      const result = await next({ ...e, text: translated.text })
      entered = !result.drop
      if (result.drop) await recover($, e.text)
      return result
    } catch (error) {
      notice = error instanceof Error ? error.message : '发送前翻译失败。'
      await recover($, e.text)
      redraw($)
      // Keep the user's draft available instead of silently sending a mistranslation.
      return { drop: `发送前翻译失败：${notice} 原文未发送；可重试，或 /translate off 后发送。` }
    } finally {
      if (pending && !entered) {
        const queue = originals.get(pendingKey)?.filter(item => item !== pending)
        if (queue?.length) originals.set(pendingKey, queue)
        else originals.delete(pendingKey)
      }
    }
  })
  on('session.append', { door: 'prompt' }, async ($, e, next) => {
    if (!e.agentId && e.message.type === 'user') {
      const text = e.message.content.filter(block => block.type === 'text').map(block => typeof block.text === 'string' ? block.text : '').join('')
      const queue = originals.get(text)
      const original = queue?.shift()?.original
      if (queue?.length === 0) originals.delete(text)
      if (original !== undefined) await update($, displayOriginals, previous => {
        const entries = [...Object.entries(previous), [e.uuid, original] as [string, string]]
        let size = entries.reduce((sum, [, value]) => sum + value.length, 0)
        while (entries.length > 100 || size > 200_000 && entries.length > 1) size -= entries.shift()![1].length
        return Object.fromEntries(entries)
      })
    }
    return next(e)
  })
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    const original = (await read($, displayOriginals))[e.requestId]
    return next(original !== undefined ? { ...e, props: { ...e.props, text: original } } : e)
  })
  on('turn.start', ($, e, next) => { activeTurn = e.turnId; reset(); notice = ''; redraw($); return next(e) })
  on('turn.step', async function* ($, e, next) {
    if (e.agentId || !interactive || !cfg?.enabled) return yield* next(e)
    const stream = next(e)
    let source = '', began = false
    for await (const chunk of stream) {
      if (chunk.kind === 'text' && e.turnId === activeTurn) {
        if (!began) { reset(); began = true }
        source += chunk.text
        if (job) job.source = source
        redraw($)
      }
      yield chunk
    }
    const result = await stream.result
    if (e.turnId === activeTurn && result.answer) {
      if (job?.source !== result.answer) reset(result.answer, result.stopReason === 'end_turn')
      else if (job) job.done = result.stopReason === 'end_turn'
      redraw($)
    }
    return result
  })
  on('turn.complete', ($, e, next) => {
    if (!e.agentId && interactive && e.turnId === activeTurn) {
      if (e.isAborted) { reset(); notice = '本轮已停止'; }
      else if (job?.source !== e.answer) reset(e.answer, true)
      else if (job) job.done = true
      redraw($)
    }
    return next(e)
  })
  on('ui.scroll', { component: 'Pane' }, ($, e, next) => {
    if (e.requestId !== PANE || page === 'settings') return next(e)
    offset = Math.max(0, Math.min(Math.max(0, linesCount - viewRows), offset + e.by))
    follow = offset >= linesCount - viewRows
    redraw($)
    return {}
  })
  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE || e.surface !== 'terminal') return next(e)
    const { Box, Text, Button, Input, Select } = $.ui.resolve(e)
    if (!cfg) return <Text>{notice || '正在读取设置…'}</Text>
    const settings = () => { draft = { ...cfg }; page = 'settings'; notice = ''; redraw($) }
    const set = (key: string, value: unknown) => { draft[key] = value }
    const field = (key: string, label: string, placeholder = '') => <Input key={`input-${key}`} label={label} value={String(draft[key] ?? '')} placeholder={placeholder} onInput={value => set(key, value)} onSubmit={value => set(key, value)} />
    if (page === 'settings') return <Box key="settings" flexDirection="column" width={e.props.bodyColumns}>
      <Box flexDirection="row" justifyContent="space-between" width={Math.max(1, e.props.bodyColumns - 4)}>
        <Text bold>翻译设置</Text>
        <Box flexDirection="row" columnGap={1}>
          <Button key="cancel-settings" plain label="取消" onPress={() => { draft = {}; page = ''; notice = ''; redraw($) }} />
          <Button key="save-settings" plain label="保存" onPress={() => save($, draft)} />
        </Box>
      </Box>
      <Box flexDirection="row" columnGap={1}>
        {['language', 'llm', 'jev', 'prompt'].map((value, index) => <Button key={`tab-${value}`} plain label={['语言', 'LLM', 'Jev', 'Prompt'][index]!} onPress={() => { tab = value; redraw($) }} />)}
      </Box>
      {notice && <Text>{notice}</Text>}
      {tab === 'language' && <Box flexDirection="column">
        <Select key="enabled" label="自动翻译" value={draft.enabled ? 'on' : 'off'} options={[{ value: 'on', label: '开启' }, { value: 'off', label: '关闭' }]} onSelect={value => { set('enabled', value === 'on'); redraw($) }} />
        <Select key="incomingLanguage" label="Agent 接收" value={String(draft.incomingLanguage)} options={languageOptions(String(draft.incomingLanguage))} onSelect={value => { set('incomingLanguage', value); redraw($) }} />
        <Select key="outgoingLanguage" label="我的阅读" value={String(draft.outgoingLanguage)} options={languageOptions(String(draft.outgoingLanguage))} onSelect={value => { set('outgoingLanguage', value); redraw($) }} />
        {field('incomingLanguage', '自定义接收代码', 'en / zh / ja')}
        {field('outgoingLanguage', '自定义阅读代码', 'en / zh / ja')}
        <Select key="detection" label="语言检测" value={String(draft.detection)} options={[{ value: 'script', label: '本地脚本' }, { value: 'llm', label: '通用 LLM' }, { value: 'jev', label: 'Jev' }]} onSelect={value => { set('detection', value); redraw($) }} />
        <Text dimColor>脚本不联网；混合语言或不确定时交给翻译模型。LLM 检测复用翻译接口。Jev 在独立页配置。</Text>
        <Text dimColor>发送前译文不会另占一行；右侧译文保留左侧原回复。</Text>
      </Box>}
      {tab === 'llm' && <Box flexDirection="column">
        <Text dimColor>兼容 Chat Completions 的接口。完整 POST URL 优先于 Base URL。</Text>
        {field('baseUrl', 'Base URL', 'https://provider.example/v1')}
        {field('postUrl', 'POST URL', '可留空')}
        {field('model', '模型名')}
        {field('apiKey', '新 API Key', cfg.hasApiKey ? '已保存，留空保留' : '可留空，用环境变量')}
        <Text dimColor>新输入的密钥会显示；保存后不再回显。</Text>
        {field('baseUrlEnv', 'URL 环境变量')}
        {field('apiKeyEnv', 'Key 环境变量')}
        {field('modelEnv', '模型环境变量')}
        <Button key="clear-api-key" plain label="清除已保存密钥" onPress={() => { set('clearApiKey', true); set('apiKey', ''); notice = '保存后清除密钥'; redraw($) }} />
        <Text dimColor>直接填写的值优先。Base URL 应包含 /v1 等前缀；插件仅追加 /chat/completions。</Text>
      </Box>}
      {tab === 'jev' && <Box flexDirection="column">
        <Text dimColor>Jev 仅判断语言；实际翻译仍使用 LLM 页中的模型。</Text>
        {field('jevUrl', 'POST URL')}
        {field('jevModel', '模型名')}
        {field('jevKey', '新 API Key', cfg.hasJevKey ? '已保存，留空保留' : '可留空，用环境变量')}
        {field('jevKeyEnv', 'Key 环境变量')}
        <Button key="clear-jev-key" plain label="清除已保存 Jev 密钥" onPress={() => { set('clearJevKey', true); set('jevKey', ''); notice = '保存后清除密钥'; redraw($) }} />
      </Box>}
      {tab === 'prompt' && <Box flexDirection="column">
        <Text dimColor>分别设置两个方向的系统提示词。变量：{'{target_language}'}、{'{source_language}'}。</Text>
        {field('incomingPrompt', '发送前')}
        {field('outgoingPrompt', '回复')}
        <Text dimColor>代码与链接占位符必须保留；不要在 Prompt 中填写密钥。</Text>
      </Box>}
    </Box>
    const translating = !!job && (job.cursor < job.source.length || !job.done) && cfg.enabled
    const text = job ? job.pieces.join('') + job.pending : ''
    const lines = wrapLines(text || (cfg.enabled ? '等待 Agent 回复…' : '翻译已关闭，点击设置配置并开启。'), Math.max(2, e.props.bodyColumns - 2))
    linesCount = lines.length; viewRows = Math.max(1, e.props.scroll.bodyRows - 5)
    offset = follow ? Math.max(0, linesCount - viewRows) : Math.min(offset, Math.max(0, linesCount - viewRows))
    return <Box key="translation-pane" flexDirection="column" width={e.props.bodyColumns}>
      <Box key="header" flexDirection="row" justifyContent="space-between" height={1} width={Math.max(1, e.props.bodyColumns - 4)}>
        <Text bold>Translation</Text><Button key="settings-button" plain label="设置" onPress={settings} />
      </Box>
      <Select key="agent-language" label="Agent 接收" value={cfg.incomingLanguage} options={languageOptions(cfg.incomingLanguage)} onSelect={value => save($, { incomingLanguage: value })} />
      <Select key="reader-language" label="我的阅读" value={cfg.outgoingLanguage} options={languageOptions(cfg.outgoingLanguage)} onSelect={value => save($, { outgoingLanguage: value })} />
      <Box flexDirection="row" justifyContent="space-between" height={1}>
        <Text dimColor>{job?.error ? '翻译失败' : !cfg.enabled ? '已关闭' : translating ? '翻译中…' : job?.source && job.skipped ? '已是目标语言' : '译文'}</Text>
        {failedPrompts.length > 0 && <Button key="recover-input" plain label="恢复输入" onPress={async () => {
          const current = await $.prompt.read()
          const result = await $.prompt.fill({ text: (current.text ? '\n\n' : '') + failedPrompts.join('\n\n'), mode: 'append' })
          if (result.isFilled) failedPrompts = []
          redraw($)
        }} />}
        <Button key="retry" plain label={job?.error ? '重试' : '回到底部'} onPress={() => { if (job?.error) reset(job.source, job.done); follow = true; redraw($) }} />
      </Box>
      <Box key="translation-body" flexDirection="column" height={viewRows} overflow="hidden">
        {lines.slice(offset, offset + viewRows).map((line, i) => <Text key={`line-${i}`}>{line || ' '}</Text>)}
      </Box>
      <Text dimColor>{job?.error || notice || `${Math.min(offset + 1, linesCount)}–${Math.min(offset + viewRows, linesCount)} / ${linesCount} · 滚轮翻阅`}</Text>
    </Box>
  })
}
