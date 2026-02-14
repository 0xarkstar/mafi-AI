interface PlayerAvatarProps {
  name: string
  color: string
  isAlive: boolean
  size?: number
}

// CSS art avatars for each agent
export function PlayerAvatar({ name, color, isAlive, size = 64 }: PlayerAvatarProps) {
  const filter = isAlive ? '' : 'grayscale(100%) opacity(50%)'

  // Common styles
  const containerStyle = {
    width: size,
    height: size,
    filter,
  }

  // Viktor (blue): Diamond/chess piece - sharp, geometric
  if (name === 'Viktor') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
            border: `2px solid ${color}`,
          }}
        />
        <div
          className="absolute inset-[30%]"
          style={{
            background: 'rgba(255, 255, 255, 0.3)',
            clipPath: 'polygon(50% 20%, 80% 50%, 50% 80%, 20% 50%)',
          }}
        />
      </div>
    )
  }

  // Luna (pink): Crescent moon - round, gentle
  if (name === 'Luna') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            border: `2px solid ${color}`,
          }}
        />
        <div
          className="absolute top-[10%] right-[10%] w-[70%] h-[70%] rounded-full"
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
          }}
        />
      </div>
    )
  }

  // Rex (red): Angular pentagon with horn - aggressive
  if (name === 'Rex') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            clipPath: 'polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%)',
            border: `2px solid ${color}`,
          }}
        />
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[20%] h-[30%]"
          style={{
            background: `${color}`,
            clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
          }}
        />
      </div>
    )
  }

  // Sage (purple): Circle with halo ring - wise, calm
  if (name === 'Sage') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-[15%] rounded-full"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            border: `2px solid ${color}`,
          }}
        />
        <div
          className="absolute inset-0 rounded-full"
          style={{
            border: `3px solid ${color}`,
            opacity: 0.4,
          }}
        />
      </div>
    )
  }

  // Nova (amber): Star/burst - chaotic energy
  if (name === 'Nova') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            clipPath:
              'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)',
            border: `2px solid ${color}`,
          }}
        />
      </div>
    )
  }

  // Iris (cyan): Eye shape - observing
  if (name === 'Iris') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
            borderRadius: '50% / 40%',
            border: `2px solid ${color}`,
          }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40%] h-[40%] rounded-full"
          style={{
            background: 'rgba(255, 255, 255, 0.9)',
            border: '2px solid rgba(0, 0, 0, 0.3)',
          }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[20%] h-[20%] rounded-full"
          style={{
            background: 'rgba(0, 0, 0, 0.8)',
          }}
        />
      </div>
    )
  }

  // Blaze (orange): Flame shape - dynamic, fiery
  if (name === 'Blaze') {
    return (
      <div style={containerStyle} className="relative">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(to top, ${color} 0%, ${color}dd 50%, ${color}88 100%)`,
            clipPath:
              'polygon(50% 0%, 65% 20%, 80% 15%, 70% 35%, 85% 50%, 70% 65%, 80% 85%, 50% 100%, 20% 85%, 30% 65%, 15% 50%, 30% 35%, 20% 15%, 35% 20%)',
            border: `2px solid ${color}`,
          }}
        />
      </div>
    )
  }

  // Fallback: simple circle
  return (
    <div style={containerStyle} className="relative">
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
          border: `2px solid ${color}`,
        }}
      />
    </div>
  )
}
