import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ParticleSystem from './ParticleSystem.jsx'
import { makeRng } from '../utils/seeded.js'

export default function CelebrationOverlay({ show, seed, tier }) {
  const rng = makeRng(seed)
  
  useEffect(() => {
    if (!show) return
    const body = document.body
    const prev = body.style.overflow
    body.style.overflow = 'hidden'
    
    // Screen flash effect
    const flash = document.createElement('div')
    flash.style.cssText = `
      position: fixed; inset: 0; background: white; 
      z-index: 9999; pointer-events: none;
      animation: flash-fade 0.3s ease-out forwards;
    `
    document.body.appendChild(flash)
    
    // Add flash animation
    const style = document.createElement('style')
    style.textContent = `
      @keyframes flash-fade {
        0% { opacity: 0.8; }
        100% { opacity: 0; }
      }
    `
    document.head.appendChild(style)
    
    setTimeout(() => {
      flash.remove()
      style.remove()
    }, 300)
    
    return () => { body.style.overflow = prev }
  }, [show])

  const discoColors = ['#FF00FF', '#00FFFF', '#FFFF00', '#FF6B35', '#00FF88']
  const discoColor = discoColors[Math.floor(rng() * discoColors.length)]

  return (
    <AnimatePresence>
      {show && (
        <>
          <motion.div className="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="spotlights">
              <motion.div className="spot spot-a" initial={{ left: '-30%' }} animate={{ left: ['-30%', '15%', '-15%', '25%', '5%'] }} transition={{ duration: 2.5, repeat: Infinity, repeatType: 'mirror' }} />
              <motion.div className="spot spot-b" initial={{ right: '-30%' }} animate={{ right: ['-30%', '15%', '-15%', '25%', '5%'] }} transition={{ duration: 3, repeat: Infinity, repeatType: 'mirror' }} />
              <motion.div className="spot spot-c" initial={{ top: '-15%' }} animate={{ top: ['-15%','5%','-8%','12%','0%'] }} transition={{ duration: 3.5, repeat: Infinity, repeatType: 'mirror' }} />
              <motion.div className="spot spot-d" initial={{ bottom: '-15%' }} animate={{ bottom: ['-15%','5%','-8%','12%','0%'] }} transition={{ duration: 4, repeat: Infinity, repeatType: 'mirror' }} />
            </div>
            
            {/* Multiple disco balls */}
            <motion.div className="disco-container">
              <motion.div 
                className="disco main-disco" 
                style={{ backgroundColor: discoColor }}
                initial={{ y: -200, rotate: 0, scale: 0 }} 
                animate={{ y: 0, rotate: 360, scale: 1 }} 
                transition={{ 
                  duration: 1.5, 
                  type: 'spring', 
                  stiffness: 100, 
                  damping: 10,
                  rotate: { repeat: Infinity, duration: 6, ease: 'linear' } 
                }} 
              />
              <motion.div 
                className="disco mini-disco" 
                initial={{ x: -100, y: -100, scale: 0 }} 
                animate={{ x: 0, y: 0, scale: 1 }} 
                transition={{ delay: 0.3, duration: 1, rotate: { repeat: Infinity, duration: 4, ease: 'linear' } }}
              />
              <motion.div 
                className="disco mini-disco" 
                initial={{ x: 100, y: -100, scale: 0 }} 
                animate={{ x: 0, y: 0, scale: 1 }} 
                transition={{ delay: 0.5, duration: 1, rotate: { repeat: Infinity, duration: 5, ease: 'linear' } }}
              />
            </motion.div>

            {/* Pulsing background */}
            <motion.div 
              className="pulse-bg"
              animate={{ 
                scale: [1, 1.02, 1],
                filter: ['hue-rotate(0deg)', 'hue-rotate(60deg)', 'hue-rotate(0deg)']
              }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          </motion.div>
          
          <ParticleSystem active={show} seed={seed} tier={tier} />
        </>
      )}
    </AnimatePresence>
  )
}


