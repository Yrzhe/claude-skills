export type OriginalPrompts = Record<string, string>
declare module 'claude-code' {
  interface PluginState {
    'translate-view': { originals: OriginalPrompts }
  }
}
