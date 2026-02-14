import { motion, useSpring, useTransform } from 'framer-motion'
import { useEffect } from 'react'

interface AnimatedNumberProps {
  value: number
  format?: (n: number) => string
}

export function AnimatedNumber({ value, format = (n) => n.toString() }: AnimatedNumberProps) {
  const spring = useSpring(value, { stiffness: 100, damping: 30 })
  const display = useTransform(spring, (current) => format(Math.round(current)))

  useEffect(() => {
    spring.set(value)
  }, [spring, value])

  return <motion.span>{display}</motion.span>
}
