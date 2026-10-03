import type { ClientModule } from 'claude-code'

type Props = { id: string; text: string; href: string }
const HoverLink: ClientModule<Props, { inside: boolean; pressed: boolean }> = (props, surface) => {
  const { Markdown } = surface.elements
  surface.onPointer(event => {
    const inside = event.type !== 'leave' && event.x >= 0 && event.y >= 0 && event.x < surface.columns && event.y < surface.rows
    const previous = surface.state ?? { inside: false, pressed: false }
    const clicked = inside && previous.pressed && event.type === 'up' && event.button === 'left'
    const pressed = event.type === 'down' && event.button === 'left' ? inside : event.type === 'up' || !inside ? false : previous.pressed
    surface.setState({ inside, pressed })
    if (clicked) surface.post({ action: 'open', id: props.id })
    else if (inside !== previous.inside) surface.post({ action: inside ? 'hover' : 'leave', id: props.id })
  })
  surface.onKey(event => { if (event.key === 'return') surface.post({ action: 'open', id: props.id }) })
  return <Markdown key={`open-${props.id}`} text={props.text} />
}
export default HoverLink
