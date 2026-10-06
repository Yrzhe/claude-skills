import { atom, read, update } from 'claude-code'
import type { EngineInterface, HookStream, ProcessSpawnChunk, ProcessSpawnResult, Register } from 'claude-code'
import { isControlPrompt, languageOptions, nextSegment, markdownParts, settingsGroups } from './core'
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
let follow = true
let needsFollow = true
let settingsStart = false
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
  follow = true; needsFollow = true
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
  if (settings || !cfg?.enabled) { page = 'settings'; draft = { ...cfg }; tab = 'language'; settingsStart = true }
  await $.ui.open({ id: PANE, title: 'Translation', columns: 52, rows: 24 })
  needsFollow = true
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
    $.clock.every(250, async () => {
      await pump($)
      if (interactive && page === 'settings' && settingsStart) {
        const result = await $.ui.scroll({ in: PANE, to: 'start' }).catch(() => ({ deny: 'pane unavailable' }))
        if (!result.deny) { settingsStart = false; redraw($) }
      }
      if (interactive && page !== 'settings' && needsFollow && follow) {
        const result = await $.ui.scroll({ in: PANE, to: 'end' }).catch(() => ({ deny: 'pane unavailable' }))
        if (!result.deny) needsFollow = false
      }
    })
    return next(e)
  })
  on('command.run', { command: 'translate' }, async ($, e) => {
    if (e.args.trim() === 'off' || e.args.trim() === 'on') await save($, { enabled: e.args.trim() === 'on' })
    await open($, e.args.trim() === 'settings')
    return { text: cfg?.enabled ? `翻译已开启 · Agent 接收 ${cfg.incomingLanguage} · 我的阅读 ${cfg.outgoingLanguage}` : '翻译已关闭；可在设置中开启。' }
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
  on('ui.scroll', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE) return next(e)
    if (page !== 'settings' && e.origin.kind === 'person') {
      follow = e.offset >= Math.max(0, e.contentRows - e.bodyRows)
      needsFollow = follow
    }
    const result = await next(e)
    redraw($)
    return result
  })
  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE || e.surface !== 'terminal') return next(e)
    const { Box, Text, Button, Input, Select, Markdown } = $.ui.resolve(e)
    if (!cfg) return <Text>{notice || '正在读取设置…'}</Text>
    const settings = () => { draft = { ...cfg }; page = 'settings'; tab = 'language'; settingsStart = true; notice = ''; redraw($) }
    const set = (key: string, value: unknown) => { draft[key] = value }
    const field = (key: string, label: string, placeholder = '') => <Box flexDirection="column"><Text dimColor>{label + ':'}</Text><Input key={`input-${key}`} label="" value={String(draft[key] ?? '')} placeholder={placeholder} onInput={value => set(key, value)} onSubmit={value => set(key, value)} /></Box>
    const envNames: Record<string, string> = { baseUrlEnv: 'OPENAI_BASE_URL', apiKeyEnv: 'OPENAI_API_KEY', modelEnv: 'OPENAI_MODEL', jevUrlEnv: 'TYPESAFE_POST_URL', jevKeyEnv: 'TYPESAFE_API_KEY', jevModelEnv: 'TYPESAFE_MODEL' }
    const sourceName = (value?: string) => value === 'manual' ? '本机填写' : value === 'env' ? '环境变量' : '未配置'
    const keySummary = (key: 'apiKey' | 'jevKey', env: 'apiKeyEnv' | 'jevKeyEnv') => {
      const source = cfg!.sources?.[key]
      const info = cfg!.keyInfo?.[key]
      const location = source === 'manual' ? `本机配置 · ${key} 字段` : source === 'env' ? `环境变量 · ${cfg![env]}` : '未配置密钥'
      return <Box key={`key-summary-${key}`} flexDirection="column">
        <Text>{'当前生效密钥：' + (info?.active || '无') + ' · ' + location}</Text>
        {source === 'manual' && <Text dimColor>{cfg!.configPath || '~/.config/claude-translate/config.json'}</Text>}
        {source === 'manual' && <Text dimColor>{`已保存的本机密钥优先；${cfg![env] || '环境变量'} 当前未用于此密钥。`}</Text>}
        {source !== 'manual' && info?.saved && <Text dimColor>{'本机另存：' + info.saved + '（当前未使用）'}</Text>}
        <Text dimColor>显示已保存配置的生效结果；修改后点「保存」更新。仅显示密钥末四位，短密钥完全隐藏。</Text>
      </Box>
    }
    const sourcePicker = (key: string) => <Select key={key} label="配置来源" value={String(draft[key] || 'manual')} options={[{ value: 'manual', label: '本机填写优先' }, { value: 'env', label: '读取环境变量' }]} onSelect={value => { set(key, value); settingsStart = true; redraw($) }} />
    const environmentFields = (provider: 'llm' | 'jev') => <Box flexDirection="column">
      {(provider === 'llm' ? [['baseUrlEnv', '地址变量名'], ['apiKeyEnv', '密钥变量名'], ['modelEnv', '模型变量名']] : [['jevUrlEnv', 'Jev 地址变量名'], ['jevKeyEnv', 'Jev 密钥变量名'], ['jevModelEnv', 'Jev 模型变量名']]).map(([key, label]) => <Box key={`binding-${key}`} flexDirection="column">
        {field(key!, label!, envNames[key!] + '（推荐名称）')}
        <Text dimColor>{!draft[key!] ? '尚未绑定；上方灰字仅是示例。' : draft[key!] !== cfg?.[key as keyof Config] ? '保存后检查此变量。' : `${String(draft[key!])}：${cfg?.envStatus?.[key!] ? '已读取（不显示变量值）' : '当前进程未设置'}`}</Text>
      </Box>)}
    </Box>
    const sections = [
      { value: 'language', label: '语言检测' }, { value: 'llm', label: '模型接口' },
      { value: 'env', label: '环境变量' }, { value: 'jev', label: 'Jev 接口' }, { value: 'prompt', label: '翻译 Prompt' },
    ]
    const narrowSettings = e.props.bodyColumns < 42
    const groups = settingsGroups(sections, e.props.bodyColumns)
    const settingsRows = (narrowSettings ? 2 : 1) + groups.length + 1
    const settingsHeader = <Box key="settings-header" position="absolute" top={e.props.scroll.offset} left={0} width={e.props.bodyColumns} height={settingsRows} flexDirection="column" backgroundColor="background">
      <Box flexDirection={narrowSettings ? 'column' : 'row'} justifyContent="space-between" width={Math.max(1, e.props.bodyColumns - 4)}>
        <Text bold>翻译设置</Text>
        <Box flexDirection="row" columnGap={1}>
          <Button key="cancel-settings" label="取消" onPress={() => { draft = {}; page = ''; notice = ''; needsFollow = true; redraw($) }} />
          <Button key="save-settings" label="保存" onPress={() => save($, draft)} />
        </Box>
      </Box>
      {groups.map((group, index) => <Box key={`settings-nav-${index}`} flexDirection="row" columnGap={1} height={1}>
        {group.map(section => <Button key={`tab-${section.value}`} label={(tab === section.value ? '● ' : '  ') + section.label} onPress={() => { tab = section.value; settingsStart = true; notice = ''; redraw($) }} />)}
      </Box>)}
      <Text dimColor wrap="truncate">{'当前检测：' + ({ script: '本地脚本', llm: 'LLM', jev: 'Jev' }[cfg.detection] || cfg.detection) + ' · 模型：' + (cfg.effectiveModel || cfg.model || '未配置')}</Text>
    </Box>
    if (page === 'settings') return <Box key="settings" flexDirection="column" width={e.props.bodyColumns} minHeight={e.props.scroll.bodyRows}>
      <Box key="settings-body" flexDirection="column" paddingTop={settingsRows}>
      {notice && <Text>{notice}</Text>}
      {tab === 'language' && <Box flexDirection="column">
        <Select key="enabled" label="自动翻译" value={draft.enabled ? 'on' : 'off'} options={[{ value: 'on', label: '开启' }, { value: 'off', label: '关闭' }]} onSelect={value => { set('enabled', value === 'on'); redraw($) }} />
        <Select key="incomingLanguage" label="Agent 接收" value={String(draft.incomingLanguage)} options={languageOptions(String(draft.incomingLanguage))} onSelect={value => { set('incomingLanguage', value); redraw($) }} />
        <Select key="outgoingLanguage" label="我的阅读" value={String(draft.outgoingLanguage)} options={languageOptions(String(draft.outgoingLanguage))} onSelect={value => { set('outgoingLanguage', value); redraw($) }} />
        {field('incomingLanguage', '自定义接收代码', 'en / zh / ja')}
        {field('outgoingLanguage', '自定义阅读代码', 'en / zh / ja')}
        <Select key="detection" label="语言检测" value={String(draft.detection)} options={[{ value: 'script', label: '本地脚本' }, { value: 'llm', label: 'LLM（如 Gemini）' }, { value: 'jev', label: 'Jev' }]} onSelect={value => { set('detection', value); redraw($) }} />
        {draft.detection === 'llm' && field('detectionModel', '检测模型', '留空复用翻译模型；也可填写 Gemini 型号')}
        <Text dimColor>脚本在本机判断，无检测接口等待。LLM 检测使用「模型接口」的地址和密钥，检测模型可以单独填写；Jev 有独立接口。</Text>
        <Text dimColor>发送前译文不会另占一行；右侧译文保留左侧原回复。</Text>
      </Box>}
      {tab === 'llm' && <Box flexDirection="column">
        <Text bold>翻译模型 · Chat Completions</Text>
        <Text dimColor>这些值保存在本机，不在插件代码中；新安装不预填你的接口和模型。</Text>
        {sourcePicker('llmConfigSource')}
        <Text>{'当前生效：' + (cfg.effectiveModel || '未配置') + ' · ' + sourceName(cfg.sources?.model)}</Text>
        {keySummary('apiKey', 'apiKeyEnv')}
        {draft.llmConfigSource === 'env' ? environmentFields('llm') : <Box flexDirection="column">
          {field('baseUrl', '接口 Base URL', 'https://provider.example/v1')}
          {field('model', '翻译模型名', '填写你的服务商提供的型号')}
          {field('apiKey', '新的 API Key', cfg.hasApiKey ? '留空不更换本机已保存的密钥' : '填入密钥')}
          <Button key="clear-api-key" plain label="清除已保存密钥" onPress={() => { set('clearApiKey', true); set('apiKey', ''); notice = '保存后清除密钥'; redraw($) }} />
          {field('postUrl', '完整 POST URL（可选）', '填写时替代 Base URL')}
          <Text dimColor>本机没有保存密钥时才读取绑定变量。输入框留空不会清除已存密钥。新输入的密钥会显示；保存后仅显示末四位。</Text>
        </Box>}
      </Box>}
      {tab === 'env' && <Box flexDirection="column">
        <Text bold>环境变量绑定</Text>
        <Text dimColor>这里填写变量的名字，不是 URL 或密钥本身。变量由启动 Claude 的终端提供。</Text>
        <Text bold>{'翻译接口 · ' + (draft.llmConfigSource === 'env' ? '读取环境变量' : '本机填写优先')}</Text>
        {environmentFields('llm')}
        <Text bold>{'Jev 检测 · ' + (draft.jevConfigSource === 'env' ? '读取环境变量' : '本机填写优先')}</Text>
        {environmentFields('jev')}
        <Button key="suggest-env-names" label="填入推荐变量名" onPress={() => { for (const [key, name] of Object.entries(envNames)) if (!draft[key]) set(key, name); redraw($) }} />
        <Text dimColor>绑定名字不会自动创建变量，也不会切换配置来源。请在模型接口或 Jev 页选择「读取环境变量」。</Text>
        <Text dimColor>例：export OPENAI_MODEL="服务商模型名"。修改终端环境后，需重启 Claude。</Text>
      </Box>}
      {tab === 'jev' && <Box flexDirection="column">
        <Text bold>Jev · 只判断语言，不生成译文</Text>
        <Text>{draft.detection === 'jev' ? '当前启用 Jev 检测。' : '当前未启用；在「语言检测」中选 Jev 后才会调用。'}</Text>
        {sourcePicker('jevConfigSource')}
        <Text dimColor>{'当前模型来源：' + sourceName(cfg.sources?.jevModel)}</Text>
        {keySummary('jevKey', 'jevKeyEnv')}
        {draft.jevConfigSource === 'env' ? environmentFields('jev') : <Box flexDirection="column">
          {field('jevUrl', 'Jev POST URL', 'https://api.typesafe.ai/v1/systemone')}
          {field('jevModel', 'Jev 模型名', 'jev-latest（官方示例）')}
          {field('jevKey', '新的 Jev API Key', cfg.hasJevKey ? '留空不更换本机已保存的密钥' : '填入密钥')}
          <Button key="clear-jev-key" plain label="清除已保存 Jev 密钥" onPress={() => { set('clearJevKey', true); set('jevKey', ''); notice = '保存后清除密钥'; redraw($) }} />
          <Text dimColor>默认地址和 jev-latest 是官方公开示例；你的网关配置只保存在本机。环境变量请在「环境变量」页绑定。</Text>
        </Box>}
      </Box>}
      {tab === 'prompt' && <Box flexDirection="column">
        <Text dimColor>分别设置两个方向的系统提示词。变量：{'{target_language}'}、{'{source_language}'}。</Text>
        {field('incomingPrompt', '发送前')}
        {field('outgoingPrompt', '回复')}
        <Text dimColor>代码与链接占位符必须保留；不要在 Prompt 中填写密钥。</Text>
      </Box>}
      </Box>
      {settingsHeader}
    </Box>
    const translating = !!job && (job.cursor < job.source.length || !job.done) && cfg.enabled
    const text = job ? job.pieces.join('') + job.pending : ''
    const content = text || (cfg.enabled ? '等待 Agent 回复…' : '翻译已关闭，点击设置配置并开启。')
    // Let Claude measure and scroll its own Markdown. A header placed at the
    // native offset stays pinned without guessing the rendered line heights.
    return <Box key="translation-pane" flexDirection="column" width={e.props.bodyColumns} minHeight={e.props.scroll.bodyRows}>
      <Box key="translation-body" flexDirection="column" paddingTop={4}>
        {markdownParts(content, e.props.bodyColumns).map((part, i) => part.plain
          ? <Text key={`markdown-${i}`}>{part.text}</Text>
          : <Markdown key={`markdown-${i}`} text={part.text} />)}
        <Text dimColor>{job?.error || notice || '滚轮翻阅'}</Text>
      </Box>
      <Box key="sticky-header" position="absolute" top={e.props.scroll.offset} left={0} width={e.props.bodyColumns} height={4} flexDirection="column" backgroundColor="background">
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
          <Button key="retry" plain label={job?.error ? '重试' : '回到底部'} onPress={() => { if (job?.error) reset(job.source, job.done); follow = true; needsFollow = true; redraw($) }} />
        </Box>
      </Box>
    </Box>
  })
}
