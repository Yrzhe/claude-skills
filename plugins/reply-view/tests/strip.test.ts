import { expect, test } from 'claude-code/testing'
import { stripLayout, pixelCells } from '../hooks/strip'

test('1000 items have the same bounded height and width at every offset', () => {
  for (const width of [20, 30, 50, 80, 120, 240]) for (const maxRows of [1, 3, 6, 20]) {
    const layout = stripLayout(1000, width, maxRows, 9999)
    expect(layout.rows).toBe(Math.min(6, maxRows))
    expect(layout.start).toBe(1000 - layout.visibleCount)
    expect(layout.visibleCount <= 4).toBe(true)
    expect(layout.visibleCount * layout.cardWidth + (layout.visibleCount - 1) * 2 <= width).toBe(true)
  }
})

test('RGB fallback uses actual image colors and letterboxes without overflowing', () => {
  const pixels = btoa(String.fromCharCode(...Array.from({ length: 64 * 32 * 3 }, (_, i) => i % 3 === 0 ? 255 : 0)))
  const cells = Uint8Array.from(atob(pixelCells(pixels, { width: 2, height: 1 }, 4, 1)), c => c.charCodeAt(0))
  const view = new DataView(cells.buffer)
  expect(cells.length).toBe(4 * 12)
  expect(view.getUint32(0, true)).toBe(0x2580)
  expect(view.getUint32(4, true)).toBe(0xff0000)
  expect(view.getUint32(8, true)).toBe(0xff0000)
  const tall = Uint8Array.from(atob(pixelCells(pixels, { width: 1, height: 10 }, 4, 1)), c => c.charCodeAt(0))
  expect(new DataView(tall.buffer).getUint32(0, true)).toBe(0x20)
  expect(new DataView(tall.buffer).getUint32(4, true)).toBe(0x01000000)
  expect(() => pixelCells('YQ==', null, 4, 1)).toThrow()
})
