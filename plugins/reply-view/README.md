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

- **Pasted images:** thumbnails for `[Image #n]` tags in the current draft. Removing a tag or sending the draft removes that draft thumbnail.
- **Reply media:** images and video posters referenced in the most recent main-agent final answer. They stay visible while you compose your next message. Click the caption below a picture to open the original file or URL.
- **Links:** an **Open** button for each website or local file link, including `localhost:3000`, `127.0.0.1`, IPv6 loopback, and Markdown links. No modifier-click is needed.
- **Copy reply:** copies all visible assistant text from the most recently ended turn, in order, with Markdown and newlines preserved. It excludes user prompts, thinking, tool output, and other agents' turns. Media and links are extracted from the final answer only.

The strip has a fixed toolbar and **one horizontal row**, at most six terminal rows high, even with 1,000 items. **Start** stays at the far left and **Copy reply** stays at the far right. Use **< / >** to move one item left or right, or move the mouse wheel over the cards to scroll them sideways. At most four cards are drawn at once, depending on terminal width. **Hide** collapses the strip to its single toolbar row.

Only visible media is prepared. Scrolling brings the next item into view without adding rows; hidden items are not downloaded. A conversion already in progress may finish after you scroll or collapse. Very short bands keep the toolbar; enlarge the terminal to see the cards. Failed media keeps an Open action; a pasted image whose cached file is missing is marked unavailable. Copy failures show a toast.

Previous replies are restored from the session transcript when the mod loads or a session resumes. `/clear` clears the old preview. Plain-text replies still get the copy button. An interrupted turn retains whatever visible response text Claude reports; a turn with no visible response clears the reply area.

## Requirements

- Claude Code **2.1.287+**; validated on **2.1.288**.
- macOS or Linux, with **Python 3** for reply-media preparation and Open actions.
- **FFmpeg** for video posters and broad image-format support. Without it, macOS uses `sips` for supported images; Linux can still preview PNG files.
- Ghostty and kitty use native image thumbnails. Other terminals use **low-resolution color-block previews** when FFmpeg is installed, so a pasted image is still recognizable without the kitty graphics protocol. Without FFmpeg, these terminals show **Open to view**; Open and Copy still work.

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

Reply previews fetch referenced HTTP(S) media automatically **when visible in the expanded strip**, including localhost media. Offscreen items wait until you scroll to them. Requests go directly from your computer to that URL, with no cookies or authentication headers. Query parameters in the original URL are preserved. Ordinary web links are opened only when you click **Open**. Downloads are limited to 64 MiB and bounded by timeouts; video pages or larger downloads fall back to an Open action.

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

The mod tests exercise parsing, session state, UI element validation, copy/open callbacks, horizontal scrolling with 1,000 items, visible-only loading, native and color-block previews, and failure cases without model calls. The Python suite converts real local and HTTP-served images/videos; it mocks desktop opening so tests do not launch applications. Terminal painting and physical mouse clicks require a manual check in your own terminal.

## Attribution

The pasted-image cache discovery and aspect-ratio layout derive from [jarrodwatts/claude-image-view](https://github.com/jarrodwatts/claude-image-view). Its copyright and MIT license are retained in [LICENSE](LICENSE).
