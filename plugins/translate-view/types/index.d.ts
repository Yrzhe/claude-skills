export type OriginalPrompts = Record<string, string>
declare module 'claude-code' {
  interface PluginState {
    'translate-view': {
      originals: OriginalPrompts; paneRevision: number;
      inputDisplay: { inputTranslation: 'off' | 'left' | 'right' | 'both'; inputLeft: 'off' | 'original' | 'translation' | 'both' }
    }
  }
}
