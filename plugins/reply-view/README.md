# Reply View

A Claude Code mod that keeps pasted images, media from the last reply, clickable links, and a copy button above the prompt.

Built on [Claude Image View](https://github.com/jarrodwatts/claude-image-view) by Jarrod Watts, with reply previews and actions by yrzhe. Both are MIT licensed.

## Install

Inside Claude Code:

```text
/plugin marketplace add Yrzhe/claude-skills
/plugin install reply-view@yrzhe-skills
/reload-plugins
```

If you already added the marketplace, refresh it first with `/plugin marketplace update yrzhe-skills`.

From a shell (use `claude-work` instead of `claude` if that is your account wrapper):

```sh
claude plugin marketplace add Yrzhe/claude-skills
claude plugin install reply-view@yrzhe-skills
```

Disable the original `image-view` plugin if you installed it: Reply View includes its pasted-image preview, so running both draws two preview bands.

## What appears

The default strip is **two rows**: a fixed toolbar and one horizontal row of compact actions, such as **Open image #2**, **Play video demo.mp4**, and **Open localhost:3000**. **Start** stays on the far left, **Copy reply** on the far right. Move with **< / >** or the mouse wheel over the strip; **Hide** leaves just the toolbar. Item count never adds rows.

- **Pasted images:** an action for each `[Image #n]` tag in the current draft. Sending the draft or removing a tag removes that action.
- **Last-reply media and links:** the most recent main-agent final answer supplies the images, videos, websites and local files. Click once to open the original target.
- **Copy reply:** all visible main-agent text from the preceding turn, with Markdown and newlines intact. User prompts, thinking, tool output and other agents are excluded.
- **Hover images in supported terminals:** with an enabled image terminal and Claude's fullscreen renderer, move onto an image action to temporarily expand a large native image above the toolbar. Moving away collapses it. Video links show a still frame. There is no separate thumbnail tile or duplicate Open row.

**Maestri:** its terminal contains kitty graphics support, but Claude 2.1.288 does not automatically enable this path for it. Restart Claude with the following session-only flags (use your usual account wrapper):

```sh
CLAUDE_CODE_FORCE_TERMINAL_IMAGES=1 CLAUDE_CODE_NO_FLICKER=1 FORCE_HYPERLINK=1 claude-work --continue
```

This enables native images and mouse hover for that run. Reloading the plugin alone does not change Claude's startup detection. Reply View transmits PNG bytes directly; it does not ask the terminal to read local image files. Native hover requires a terminal that implements kitty graphics, including Unicode placeholders. Do not enable the flag in a terminal that cannot draw them.

Unknown terminals without image support keep compact one-click Open actions. No blocky substitute is drawn. `FORCE_HYPERLINK=1` additionally exposes real file hyperlinks to a terminal application's own link handling; that application's own Quick Look behaviour is separate from this mod's hover preview.

Previous replies are restored from the transcript on load/resume. `/clear` clears old media. Plain-text replies still get Copy. Missing cached pastes are marked unavailable; failed reply-media preparation keeps its Open action.

## Requirements

- Claude Code **2.1.287+**; validated on **2.1.288**.
- macOS or Linux, with **Python 3** for reply-media preparation and Open actions.
- **FFmpeg** for video posters and broad image-format support. Without it, macOS uses `sips` for supported images; Linux can still preview PNG files.
- A terminal with the **kitty graphics protocol**, including Unicode placeholders, plus Claude fullscreen mode, for native hover images. Ghostty/kitty can be detected automatically; see the Maestri startup flags above. Other terminals retain compact Open/Copy actions.

For example, with Homebrew:

```sh
brew install python ffmpeg
```

Videos show a still frame in the terminal; clicking their caption opens the URL or the system's default video player. This does not embed video playback in the terminal. The preview band targets the terminal, not Claude Desktop, VS Code's chat panel, or headless `-p` sessions.

## Recognized references

```text
[Cover](</absolute/path/my cover.png>)
[Video](./output/demo.mp4)
![Chart](https://example.com/render?id=123)
[clip.mp4](https://example.com/download?id=123)
https://example.com/photo.jpg?signature=...
http://localhost:3000
localhost:4321/preview
`./output/chart.webp`
file:///absolute/path/my%20cover.png
```

Slash commands such as `/plugin` and repository names such as `Yrzhe/claude-skills` are not links. Non-media local files must exist before an Open button is shown. Relative paths resolve against the session working directory. Use a Markdown destination in angle brackets or a backtick-wrapped path when a filename contains spaces. File references with `:line` or `#Lline` anchors open the file. Supported image extensions are PNG, JPEG, WebP, GIF, AVIF, BMP, TIFF, HEIC, and SVG; actual decoding depends on your converter build. Videos include MP4, M4V, MOV, WebM, MKV, AVI, and OGV. GIF/video previews use one frame.

Media detection uses the destination extension, a filename label, or Markdown image syntax. An extensionless ordinary link is shown as a link. Video-sharing pages and authenticated downloads are not scraped. A file path must exist on the machine running Claude Code; files inside another host/container are not downloaded automatically.

## Data and permissions

The mod reads the current prompt, the session transcript for restoration, and the files it previews. It never calls an AI model or uploads your files or replies.

On supported fullscreen image terminals, reply previews fetch referenced HTTP(S) media automatically **when their actions are visible in the expanded strip**, including localhost media. Offscreen items wait until you scroll to them. Other terminals do not download media automatically. A conversion already in progress may finish after scrolling or collapsing. Requests go directly from your computer to that URL, with no cookies or authentication headers. Query parameters in the original URL are preserved. Ordinary web links are opened only when you click **Open**. Downloads are limited to 64 MiB and bounded by timeouts; video pages or larger downloads fall back to an Open action.

A Python helper runs FFmpeg (or `sips`) without a shell. It writes PNG thumbnails to the OS temporary directory under `claude-image-view-<uid>`, removes temporary download files after conversion, and prunes its own thumbnails older than seven days when another preview is prepared. Original files are never changed. Opening uses `open` on macOS or `xdg-open` on Linux. Copy uses Claude Code's native `ui.copy` API. No dependencies are installed automatically.

## Development

From this plugin's directory:

```sh
claude-work --plugin-dir .
claude-work plugin validate .claude-plugin/plugin.json
claude-work plugin test .
python3 -m unittest discover -s tests -p 'test_*.py' -v
tsc -p .
```

Claude writes its version-specific TypeScript declarations and `tsconfig.json` when it loads the mod. Type-check after that first load. `claude` works in place of `claude-work`.

The mod tests exercise parsing, session state, UI element validation, copy/open callbacks, horizontal scrolling with 1,000 items, visible-only loading, pointer enter/leave expansion and compact fallback actions, and failure cases without model calls. The Python suite converts real local and HTTP-served images/videos; it mocks desktop opening so tests do not launch applications. The fullscreen expand/collapse path is additionally exercised with terminal pointer events. The Maestri test terminal also receives native inline PNG transmissions. Physical high-resolution painting and host-specific link preview behaviour still require visual confirmation in the actual terminal application.

## Attribution

The pasted-image cache discovery and aspect-ratio layout derive from [jarrodwatts/claude-image-view](https://github.com/jarrodwatts/claude-image-view). Its copyright and MIT license are retained in [LICENSE](LICENSE).
