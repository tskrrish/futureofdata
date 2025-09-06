import { useState } from 'react'

interface VolunteerData {
  contact_id: number | null
  first_name: string
  last_name: string
  email: string | null
  hours_total: number
  assignments_count: number
  first_activity: string | null
  last_activity: string | null
  milestones: string[]
}

const MILESTONE_TIERS = [
  { threshold: 10, label: "First Impact", color: "bg-green-500" },
  { threshold: 25, label: "Service Star", color: "bg-blue-500" },
  { threshold: 50, label: "Commitment Champion", color: "bg-purple-500" },
  { threshold: 100, label: "Passion In Action Award", color: "bg-orange-500" },
  { threshold: 500, label: "Guiding Light Award", color: "bg-yellow-500" },
]

export default function VolunteerLookup() {
  const [searchTerm, setSearchTerm] = useState('')
  const [volunteer, setVolunteer] = useState<VolunteerData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const searchVolunteer = async () => {
    if (!searchTerm.trim()) {
      setError('Please enter your name or email')
      return
    }

    setLoading(true)
    setError('')
    setVolunteer(null)

    try {
      // Try searching by email first
      if (searchTerm.includes('@')) {
        const response = await fetch(`http://127.0.0.1:8080/volunteer_by_email?email=${encodeURIComponent(searchTerm.trim())}`)
        if (response.ok) {
          const data = await response.json()
          setVolunteer(data)
          return
        }
      }

      // Search by name in the volunteers list
      const response = await fetch('http://127.0.0.1:8080/volunteers?start=2024-01-01')
      if (response.ok) {
        const volunteers = await response.json()
        const searchLower = searchTerm.toLowerCase().trim()
        
        const found = volunteers.find((v: VolunteerData) => {
          const fullName = `${v.first_name} ${v.last_name}`.toLowerCase()
          return fullName.includes(searchLower) || 
                 v.first_name.toLowerCase().includes(searchLower) ||
                 v.last_name.toLowerCase().includes(searchLower)
        })

        if (found) {
          setVolunteer(found)
        } else {
          setError('Volunteer not found. Please check your name or email.')
        }
      } else {
        setError('Failed to search volunteers. Please try again.')
      }
    } catch (err) {
      setError('Network error. Please make sure the server is running.')
    } finally {
      setLoading(false)
    }
  }

  const getNextMilestone = (currentHours: number) => {
    for (const tier of MILESTONE_TIERS) {
      if (currentHours < tier.threshold) {
        return {
          ...tier,
          hoursNeeded: tier.threshold - currentHours
        }
      }
    }
    return null
  }

  const getProgressPercentage = (currentHours: number, targetHours: number) => {
    return Math.min((currentHours / targetHours) * 100, 100)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="mb-4">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
            Enter your name or email
          </label>
          <div className="flex gap-3">
            <input
              id="search"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchVolunteer()}
              placeholder="e.g. John Smith or john@email.com"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={searchVolunteer}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>

      {volunteer && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              {volunteer.first_name} {volunteer.last_name}
            </h2>
            {volunteer.email && (
              <p className="text-gray-600">{volunteer.email}</p>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">Total Hours</h3>
              <p className="text-3xl font-bold text-blue-600">{volunteer.hours_total}</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-green-800 mb-2">Total Activities</h3>
              <p className="text-3xl font-bold text-green-600">{volunteer.assignments_count}</p>
            </div>
          </div>

          {volunteer.first_activity && volunteer.last_activity && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Activity Period</h3>
              <p className="text-gray-600">
                From {volunteer.first_activity} to {volunteer.last_activity}
              </p>
            </div>
          )}

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Your Achievements</h3>
            {volunteer.milestones.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {volunteer.milestones.map((milestone, index) => {
                  const tier = MILESTONE_TIERS.find(t => t.label === milestone)
                  return (
                    <span
                      key={index}
                      className={`px-3 py-1 rounded-full text-white text-sm font-medium ${tier?.color || 'bg-gray-500'}`}
                    >
                      🏆 {milestone}
                    </span>
                  )
                })}
              </div>
            ) : (
              <p className="text-gray-500">No milestones achieved yet. Keep volunteering!</p>
            )}
          </div>

          {(() => {
            const nextMilestone = getNextMilestone(volunteer.hours_total)
            return nextMilestone ? (
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">Next Milestone</h3>
                <p className="text-yellow-700 mb-3">
                  <strong>{nextMilestone.label}</strong> - {nextMilestone.hoursNeeded} more hours needed
                </p>
                <div className="w-full bg-yellow-200 rounded-full h-3">
                  <div
                    className="bg-yellow-500 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${getProgressPercentage(volunteer.hours_total, nextMilestone.threshold)}%` }}
                  ></div>
                </div>
                <p className="text-sm text-yellow-600 mt-2">
                  {volunteer.hours_total} / {nextMilestone.threshold} hours ({getProgressPercentage(volunteer.hours_total, nextMilestone.threshold).toFixed(1)}%)
                </p>
              </div>
            ) : (
              <div className="p-4 bg-purple-50 rounded-lg">
                <h3 className="text-lg font-semibold text-purple-800 mb-2">🌟 All Milestones Achieved!</h3>
                <p className="text-purple-700">
                  Congratulations! You've achieved all milestone levels. Thank you for your incredible dedication!
                </p>
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}
