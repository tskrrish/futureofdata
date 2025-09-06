import React, { useState } from "react";
import { Calendar, MapPin, Users, Clock, CheckCircle, AlertCircle } from "lucide-react";

export function RSVPCard({ event, onRSVP, showRSVPForm = true }) {
  const [isRSVPing, setIsRSVPing] = useState(false);
  const [rsvpSuccess, setRsvpSuccess] = useState(false);
  const [rsvpError, setRsvpError] = useState("");
  const [formData, setFormData] = useState({
    email: "",
    firstName: "",
    lastName: "",
    notes: ""
  });

  // Format date for display
  const formatEventDate = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      }),
      time: date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
    };
  };

  const { date, time } = formatEventDate(event.event_date);
  const spotsRemaining = event.spots_remaining;
  const isFull = spotsRemaining === 0;

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleRSVP = async (e) => {
    e.preventDefault();
    
    if (!formData.email || !formData.firstName) {
      setRsvpError("Please fill in required fields");
      return;
    }

    setIsRSVPing(true);
    setRsvpError("");

    try {
      const rsvpData = {
        event_id: event.id,
        email: formData.email,
        first_name: formData.firstName,
        last_name: formData.lastName,
        notes: formData.notes
      };

      const response = await fetch('/api/rsvp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rsvpData)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setRsvpSuccess(true);
        if (onRSVP) {
          onRSVP(result.rsvp);
        }
      } else {
        setRsvpError(result.detail || "Failed to RSVP. Please try again.");
      }
    } catch (error) {
      console.error("RSVP error:", error);
      setRsvpError("Network error. Please check your connection and try again.");
    } finally {
      setIsRSVPing(false);
    }
  };

  if (rsvpSuccess) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
        <div className="flex items-center space-x-3 mb-4">
          <CheckCircle className="w-8 h-8 text-green-500" />
          <div>
            <h3 className="text-xl font-semibold text-gray-900">RSVP Confirmed!</h3>
            <p className="text-gray-600">Calendar invite sent to {formData.email}</p>
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-md">
          <p className="text-green-800">
            Thank you for volunteering with us! You'll receive:
          </p>
          <ul className="mt-2 text-sm text-green-700 space-y-1">
            <li>• A calendar invite with event details</li>
            <li>• Reminder emails 24 hours and 2 hours before the event</li>
            <li>• Contact information if you need to make changes</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      {/* Event Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-xl font-semibold text-gray-900">{event.title}</h3>
          {event.branch && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
              {event.branch}
            </span>
          )}
        </div>
        
        {event.description && (
          <p className="text-gray-600 mb-4">{event.description}</p>
        )}
      </div>

      {/* Event Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="flex items-center space-x-3">
          <Calendar className="w-5 h-5 text-gray-400" />
          <div>
            <p className="font-medium text-gray-900">{date}</p>
            <p className="text-sm text-gray-600">{time}</p>
          </div>
        </div>

        {event.location && (
          <div className="flex items-center space-x-3">
            <MapPin className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">Location</p>
              <p className="text-sm text-gray-600">{event.location}</p>
            </div>
          </div>
        )}

        {event.max_participants && (
          <div className="flex items-center space-x-3">
            <Users className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">Capacity</p>
              <p className="text-sm text-gray-600">
                {event.rsvp_count || 0} / {event.max_participants} signed up
                {spotsRemaining !== null && (
                  <span className={`ml-2 ${isFull ? 'text-red-600' : 'text-green-600'}`}>
                    ({isFull ? 'Full' : `${spotsRemaining} spots left`})
                  </span>
                )}
              </p>
            </div>
          </div>
        )}

        {event.category && (
          <div className="flex items-center space-x-3">
            <Clock className="w-5 h-5 text-gray-400" />
            <div>
              <p className="font-medium text-gray-900">Category</p>
              <p className="text-sm text-gray-600">{event.category}</p>
            </div>
          </div>
        )}
      </div>

      {/* RSVP Form */}
      {showRSVPForm && !isFull && (
        <div className="border-t pt-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">
            One-Click RSVP
          </h4>
          
          <form onSubmit={handleRSVP} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="your.email@example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name *
                </label>
                <input
                  type="text"
                  name="firstName"
                  required
                  value={formData.firstName}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your first name"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Last Name
              </label>
              <input
                type="text"
                name="lastName"
                value={formData.lastName}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Your last name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes (Optional)
              </label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Any questions or special requirements?"
              />
            </div>

            {rsvpError && (
              <div className="flex items-center space-x-2 text-red-600 text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>{rsvpError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isRSVPing}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRSVPing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </span>
              ) : (
                "Confirm RSVP & Get Calendar Invite"
              )}
            </button>
          </form>

          <div className="mt-4 text-xs text-gray-500">
            * By submitting, you'll receive a calendar invite and reminder emails
          </div>
        </div>
      )}

      {/* Full Event Message */}
      {isFull && (
        <div className="border-t pt-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
              <span className="text-yellow-800 font-medium">This event is full</span>
            </div>
            <p className="text-sm text-yellow-700 mt-1">
              Check back later or look for similar volunteer opportunities.
            </p>
          </div>
        </div>
      )}

      {/* Contact Info */}
      {(event.contact_email || event.contact_phone) && (
        <div className="border-t pt-4 mt-6">
          <h5 className="text-sm font-medium text-gray-900 mb-2">Questions?</h5>
          <div className="text-sm text-gray-600 space-y-1">
            {event.contact_email && (
              <p>
                Email: <a href={`mailto:${event.contact_email}`} className="text-blue-600 hover:underline">
                  {event.contact_email}
                </a>
              </p>
            )}
            {event.contact_phone && (
              <p>
                Phone: <a href={`tel:${event.contact_phone}`} className="text-blue-600 hover:underline">
                  {event.contact_phone}
                </a>
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}