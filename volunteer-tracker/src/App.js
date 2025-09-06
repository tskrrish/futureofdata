import { useState } from 'react';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [volunteerData, setVolunteerData] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    setError('');
    setVolunteerData(null);

    try {
      const response = await fetch(`http://localhost:8080/volunteer_by_email?email=${searchTerm}`);
      if (!response.ok) throw new Error('Not found');
      const data = await response.json();
      setVolunteerData(data);
    } catch (e) {
      setError('Volunteer not found or server error');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Volunteer Hours Lookup</h1>
      <input 
        type="text" 
        value={searchTerm} 
        onChange={(e) => setSearchTerm(e.target.value)} 
        placeholder="Enter your email" 
        style={{ padding: '10px', width: '100%', marginBottom: '10px' }}
      />
      <button onClick={handleSearch} style={{ padding: '10px', background: 'blue', color: 'white' }}>Search</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {volunteerData && (
        <div style={{ marginTop: '20px' }}>
          <h2>{volunteerData.first_name} {volunteerData.last_name}</h2>
          <p>Total Hours: {volunteerData.hours_total}</p>
          <p>Milestones: {volunteerData.milestones.join(', ') || 'None yet'}</p>
        </div>
      )}
    </div>
  );
}

export default App;
