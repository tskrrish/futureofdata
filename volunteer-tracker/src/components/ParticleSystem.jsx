import React, { useEffect, useRef } from 'react'
import { makeRng } from '../utils/seeded.js'

export default function ParticleSystem({ active, seed, tier }) {
  const canvasRef = useRef(null)
  
  useEffect(() => {
    if (!active) return
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    const rng = makeRng(seed)
    
    // Resize canvas
    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)
    
    const particles = []
    const particleCount = tier === 'legendary' ? 100 : tier === 'special' ? 60 : 40
    
    // Create particles
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: rng() * canvas.width,
        y: rng() * canvas.height,
        vx: (rng() - 0.5) * 4,
        vy: (rng() - 0.5) * 4,
        size: rng() * 4 + 1,
        color: tier === 'legendary' ? `hsl(${rng() * 60 + 15}, 100%, 60%)` :
               tier === 'special' ? `hsl(${rng() * 360}, 80%, 70%)` :
               `hsl(${rng() * 120 + 180}, 60%, 80%)`,
        life: 1,
        decay: rng() * 0.02 + 0.005
      })
    }
    
    let animationId
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      particles.forEach((p, i) => {
        p.x += p.vx
        p.y += p.vy
        p.life -= p.decay
        
        if (p.life <= 0 || p.x < 0 || p.x > canvas.width || p.y < 0 || p.y > canvas.height) {
          p.x = rng() * canvas.width
          p.y = rng() * canvas.height
          p.life = 1
        }
        
        ctx.save()
        ctx.globalAlpha = p.life
        ctx.fillStyle = p.color
        ctx.shadowBlur = 10
        ctx.shadowColor = p.color
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      })
      
      animationId = requestAnimationFrame(animate)
    }
    
    animate()
    
    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationId)
    }
  }, [active, seed, tier])
  
  if (!active) return null
  
  return (
    <canvas 
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 1000
      }}
    />
  )
}
