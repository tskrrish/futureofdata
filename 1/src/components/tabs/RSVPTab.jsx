import React, { useState, useEffect } from "react";
import { Calendar, Plus, RefreshCw, Filter } from "lucide-react";
import { RSVPCard } from "../RSVPCard";

export function RSVPTab() {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [branchFilter, setBranchFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Sample branches for filtering
  const branches = ["All", "Blue Ash YMCA", "M.E. Lyons YMCA", "Campbell County YMCA", "Clippard YMCA"];
  const categories = ["All", "Youth Development", "Fitness & Wellness", "Special Events", "Community Service"];

  // Fetch events from API
  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/events?upcoming_only=true');
      const data = await response.json();
      
      if (response.ok && data.success) {
        setEvents(data.events || []);
        setError("");
      } else {
        setError("Failed to load events");
        setEvents([]);
      }
    } catch (err) {
      console.error("Error fetching events:", err);
      setError("Network error loading events");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter events based on selected filters
  useEffect(() => {
    let filtered = events;

    if (branchFilter !== "All") {
      filtered = filtered.filter(event => event.branch === branchFilter);
    }

    if (categoryFilter !== "All") {
      filtered = filtered.filter(event => event.category === categoryFilter);
    }

    // Sort by event date
    filtered.sort((a, b) => new Date(a.event_date) - new Date(b.event_date));

    setFilteredEvents(filtered);
  }, [events, branchFilter, categoryFilter]);

  // Load events on component mount
  useEffect(() => {
    fetchEvents();
  }, []);

  // Handle successful RSVP
  const handleRSVP = (rsvp) => {
    // Refresh events to get updated RSVP counts
    fetchEvents();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 mt-6">
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
          <span className="ml-3 text-gray-600">Loading volunteer events...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 mt-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Calendar className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Volunteer Events</h2>
            <p className="text-sm text-gray-600">Find and RSVP to upcoming volunteer opportunities</p>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={fetchEvents}
            className="flex items-center px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="flex items-center px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Event
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6 pb-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filter by:</span>
        </div>

        <select
          value={branchFilter}
          onChange={(e) => setBranchFilter(e.target.value)}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {branches.map(branch => (
            <option key={branch} value={branch}>{branch}</option>
          ))}
        </select>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>

        {(branchFilter !== "All" || categoryFilter !== "All") && (
          <button
            onClick={() => {
              setBranchFilter("All");
              setCategoryFilter("All");
            }}
            className="px-3 py-1 text-xs text-blue-600 hover:text-blue-800 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Create Event Form */}
      {showCreateForm && <CreateEventForm onEventCreated={fetchEvents} onCancel={() => setShowCreateForm(false)} />}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
          <button
            onClick={fetchEvents}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {events.length === 0 ? "No events available" : "No events match your filters"}
          </h3>
          <p className="text-gray-600 mb-4">
            {events.length === 0 
              ? "Check back later for new volunteer opportunities" 
              : "Try adjusting your filters or check back later"}
          </p>
          {events.length === 0 && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create First Event
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="text-sm text-gray-600 mb-4">
            Showing {filteredEvents.length} of {events.length} events
          </div>
          
          {filteredEvents.map((event) => (
            <RSVPCard
              key={event.id}
              event={event}
              onRSVP={handleRSVP}
              showRSVPForm={true}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Simple Create Event Form Component
function CreateEventForm({ onEventCreated, onCancel }) {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    event_date: "",
    end_date: "",
    location: "",
    branch: "",
    category: "",
    max_participants: "",
    contact_email: "",
    contact_phone: ""
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError("");

    try {
      // Clean up form data
      const eventData = { ...formData };
      if (eventData.max_participants) {
        eventData.max_participants = parseInt(eventData.max_participants);
      }

      const response = await fetch('/api/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        onEventCreated();
        onCancel();
      } else {
        setError(result.detail || "Failed to create event");
      }
    } catch (err) {
      console.error("Error creating event:", err);
      setError("Network error creating event");
    } finally {
      setCreating(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  // Get current datetime for min date input
  const currentDateTime = new Date().toISOString().slice(0, 16);

  return (
    <div className="bg-gray-50 rounded-lg p-6 mb-6 border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Volunteer Event</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Event Title *
            </label>
            <input
              type="text"
              name="title"
              required
              value={formData.title}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Community Garden Volunteer Day"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Branch
            </label>
            <select
              name="branch"
              value={formData.branch}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select branch</option>
              <option value="Blue Ash YMCA">Blue Ash YMCA</option>
              <option value="M.E. Lyons YMCA">M.E. Lyons YMCA</option>
              <option value="Campbell County YMCA">Campbell County YMCA</option>
              <option value="Clippard YMCA">Clippard YMCA</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Describe what volunteers will be doing..."
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date & Time *
            </label>
            <input
              type="datetime-local"
              name="event_date"
              required
              min={currentDateTime}
              value={formData.event_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date & Time
            </label>
            <input
              type="datetime-local"
              name="end_date"
              min={formData.event_date || currentDateTime}
              value={formData.end_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="YMCA Blue Ash"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select category</option>
              <option value="Youth Development">Youth Development</option>
              <option value="Fitness & Wellness">Fitness & Wellness</option>
              <option value="Special Events">Special Events</option>
              <option value="Community Service">Community Service</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Participants
            </label>
            <input
              type="number"
              name="max_participants"
              min="1"
              value={formData.max_participants}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="20"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Email
            </label>
            <input
              type="email"
              name="contact_email"
              value={formData.contact_email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="volunteer@ymca.org"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Phone
            </label>
            <input
              type="tel"
              name="contact_phone"
              value={formData.contact_phone}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="(513) 123-4567"
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={creating}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {creating ? "Creating..." : "Create Event"}
          </button>
        </div>
      </form>
    </div>
  );
}