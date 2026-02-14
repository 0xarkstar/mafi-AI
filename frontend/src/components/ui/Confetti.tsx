import { useEffect, useRef } from 'react'
import { AGENTS } from '../../lib/constants'

interface ConfettiProps {
  active: boolean
  colors?: string[]
}

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  color: string
  size: number
  rotation: number
  rotationSpeed: number
}

const DEFAULT_COLORS = AGENTS.map((a) => a.color)

export function Confetti({ active, colors = DEFAULT_COLORS }: ConfettiProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const animationFrameRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    if (!active) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      particlesRef.current = []
      return
    }

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    // Create particles
    particlesRef.current = Array.from({ length: 50 }, () => ({
      x: Math.random() * canvas.width,
      y: -20,
      vx: (Math.random() - 0.5) * 4,
      vy: Math.random() * 3 + 2,
      color: colors[Math.floor(Math.random() * colors.length)] ?? '#ffffff',
      size: Math.random() * 8 + 4,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10,
    }))

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      particlesRef.current.forEach((p, i) => {
        p.x += p.vx
        p.y += p.vy
        p.vy += 0.1 // gravity
        p.rotation += p.rotationSpeed

        ctx.save()
        ctx.translate(p.x, p.y)
        ctx.rotate((p.rotation * Math.PI) / 180)
        ctx.fillStyle = p.color
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size)
        ctx.restore()

        // Remove if off screen
        if (p.y > canvas.height + 20) {
          particlesRef.current.splice(i, 1)
        }
      })

      if (particlesRef.current.length > 0) {
        animationFrameRef.current = requestAnimationFrame(animate)
      }
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [active, colors])

  if (!active) return null

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-50"
      style={{ mixBlendMode: 'screen' }}
    />
  )
}
