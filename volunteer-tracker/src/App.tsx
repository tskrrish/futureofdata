import { useState } from 'react'
import VolunteerLookup from './components/VolunteerLookup'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            YMCA Volunteer Hours Tracker
          </h1>
          <p className="text-lg text-gray-600">
            Check your volunteer hours and milestone achievements
          </p>
        </div>
        <VolunteerLookup />
      </div>
    </div>
  )
}

export default App