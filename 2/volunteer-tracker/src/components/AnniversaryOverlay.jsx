import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { calculateAnniversaryYears } from '../constants.js'

export default function AnniversaryOverlay({ show, firstActivityDate, volunteerName, onComplete }) {
  const [showContent, setShowContent] = useState(false)
  const anniversaryYears = calculateAnniversaryYears(firstActivityDate)

  useEffect(() => {
    if (show) {
      setTimeout(() => setShowContent(true), 600)
      setTimeout(() => {
        setShowContent(false)
        setTimeout(() => onComplete?.(), 500)
      }, 4500)
    }
  }, [show, onComplete])

  const getAnniversaryMessage = (years) => {
    if (years === 1) return "One Amazing Year!"
    if (years === 5) return "Five Years Strong!"
    if (years === 10) return "A Decade of Impact!"
    return `${years} Years of Service!`
  }

  const getAnniversaryIcon = (years) => {
    if (years >= 10) return "🎊"
    if (years >= 5) return "🎂"
    if (years >= 3) return "🎈"
    return "🎉"
  }

  const getAnniversaryColor = (years) => {
    if (years >= 10) return "#FF6B35"
    if (years >= 5) return "#FFD700"
    if (years >= 3) return "#1B9E77"
    return "#E7298A"
  }

  if (!show || anniversaryYears < 1) return null

  const icon = getAnniversaryIcon(anniversaryYears)
  const color = getAnniversaryColor(anniversaryYears)
  const message = getAnniversaryMessage(anniversaryYears)

  return (
    <AnimatePresence>
      {show && (
        <motion.div 
          className="anniversary-overlay-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div 
            className="anniversary-celebration-container"
            initial={{ scale: 0, y: -100 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0, y: 100 }}
            transition={{ type: 'spring', stiffness: 80, damping: 12 }}
          >
            <motion.div 
              className="anniversary-icon-burst"
              initial={{ scale: 0 }}
              animate={{ scale: [0, 1.5, 1] }}
              transition={{ duration: 1, delay: 0.2 }}
            >
              <motion.div
                className="anniversary-icon"
                animate={{ 
                  rotate: [0, 10, -10, 0],
                  scale: [1, 1.1, 1]
                }}
                transition={{ 
                  duration: 0.8,
                  repeat: Infinity,
                  repeatType: 'reverse'
                }}
                style={{ color }}
              >
                {icon}
              </motion.div>
            </motion.div>

            <AnimatePresence mode="wait">
              {showContent && (
                <motion.div 
                  className="anniversary-content"
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -30, opacity: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <motion.h1 
                    className="anniversary-title"
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.6, type: 'spring', stiffness: 150 }}
                  >
                    ANNIVERSARY CELEBRATION!
                  </motion.h1>
                  
                  <motion.h2 
                    className="anniversary-message"
                    initial={{ x: -50, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.8 }}
                    style={{ color }}
                  >
                    {message}
                  </motion.h2>
                  
                  <motion.div 
                    className="anniversary-years"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 1.0, type: 'spring', stiffness: 200 }}
                  >
                    <motion.span 
                      className="years-number"
                      animate={{ 
                        textShadow: [
                          `0 0 20px ${color}`,
                          `0 0 40px ${color}`,
                          `0 0 20px ${color}`
                        ]
                      }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      {anniversaryYears}
                    </motion.span>
                    <span className="years-label">
                      YEAR{anniversaryYears !== 1 ? 'S' : ''}
                    </span>
                  </motion.div>

                  <motion.p 
                    className="anniversary-gratitude"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.2 }}
                  >
                    Thank you for your continued dedication and service!
                  </motion.p>

                  <motion.div 
                    className="anniversary-date-range"
                    initial={{ y: 15, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 1.4 }}
                  >
                    {new Date(firstActivityDate).toLocaleDateString()} - Today
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div 
              className="anniversary-confetti"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.6, repeat: Infinity, repeatDelay: 0.8 }}
            />

            <motion.div 
              className="anniversary-glow"
              animate={{ 
                scale: [1, 1.1, 1],
                opacity: [0.3, 0.6, 0.3]
              }}
              transition={{ duration: 3, repeat: Infinity }}
              style={{ background: `radial-gradient(circle, ${color}30, transparent)` }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}