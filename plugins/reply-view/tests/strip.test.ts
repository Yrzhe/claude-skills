import { expect, test } from 'claude-code/testing'
import { stripLayout, linkHref, hoverLayout } from '../hooks/strip'

test('1000 items have the same bounded height and width at every offset', () => {
  for (const width of [20, 30, 50, 80, 120, 240]) for (const maxRows of [1, 3, 6, 20]) {
    const layout = stripLayout(1000, width, maxRows, 9999)
    expect(layout.rows).toBe(Math.min(2, maxRows))
    expect(layout.start).toBe(1000 - layout.visibleCount)
    expect(layout.visibleCount <= 4).toBe(true)
    expect(layout.visibleCount * layout.cardWidth + (layout.visibleCount - 1) * 2 <= width).toBe(true)
  }
})

test('file links preserve spaces, Unicode and URL punctuation for native previews', () => {
  const target = '/tmp/图片 #1 (copy) 50%.png'
  expect(decodeURIComponent(new URL(linkHref(target)!).pathname)).toBe(target)
  expect(linkHref('https://example.com/image.png?q=1')).toBe('https://example.com/image.png?q=1')
  expect(linkHref('~/unresolved.png')).toBeUndefined()
})

test('hover images use a large aspect-correct box within the terminal width', () => {
  const popup = hoverLayout({ width: 800, height: 400 }, 120, 22)
  expect(popup).toEqual({ columns: 88, rows: 22 })
  expect(hoverLayout({ width: 400, height: 800 }, 40, 10)).toEqual({ columns: 10, rows: 10 })
})
