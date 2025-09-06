import { useState, useEffect } from 'react';

const GiftCardStore = ({ volunteer }) => {
  const [giftCardOptions, setGiftCardOptions] = useState([]);
  const [pointsInfo, setPointsInfo] = useState(null);
  const [redemptions, setRedemptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [redeeming, setRedeeming] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (volunteer?.contact_id) {
      loadGiftCardData();
    }
  }, [volunteer]);

  const loadGiftCardData = async () => {
    try {
      setLoading(true);
      
      // Load gift card options
      const optionsResponse = await fetch('http://localhost:8080/gift-cards/options');
      const options = await optionsResponse.json();
      setGiftCardOptions(options);

      // Load volunteer points
      const pointsResponse = await fetch(`http://localhost:8080/volunteers/${volunteer.contact_id}/points`);
      const points = await pointsResponse.json();
      setPointsInfo(points);

      // Load redemption history
      const redemptionsResponse = await fetch(`http://localhost:8080/volunteers/${volunteer.contact_id}/redemptions`);
      const redemptionHistory = await redemptionsResponse.json();
      setRedemptions(redemptionHistory);

    } catch (err) {
      setError('Failed to load gift card data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRedeem = async (provider, denomination) => {
    try {
      setRedeeming(`${provider}-${denomination}`);
      setError('');

      const response = await fetch('http://localhost:8080/gift-cards/redeem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          volunteer_contact_id: volunteer.contact_id,
          provider: provider,
          denomination: denomination
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Redemption failed');
      }

      const redemption = await response.json();
      
      // Refresh data
      await loadGiftCardData();
      
      // Show success message
      setError(''); // Clear any previous errors
      
    } catch (err) {
      setError(err.message);
    } finally {
      setRedeeming(null);
    }
  };

  const getProviderColor = (provider) => {
    const colors = {
      amazon: '#FF9900',
      starbucks: '#00704A',
      target: '#CC0000',
      walmart: '#0071CE',
      visa: '#1A1F71'
    };
    return colors[provider] || '#666';
  };

  const getProviderLogo = (provider) => {
    const logos = {
      amazon: '📦',
      starbucks: '☕',
      target: '🎯',
      walmart: '🏪',
      visa: '💳'
    };
    return logos[provider] || '🎁';
  };

  if (loading) {
    return (
      <div className="gift-card-store loading">
        <div className="loading-spinner">Loading Gift Card Store...</div>
      </div>
    );
  }

  return (
    <div className="gift-card-store">
      <div className="store-header">
        <h2>🎁 Reward Store</h2>
        <div className="points-balance">
          <div className="points-info">
            <span className="points-label">Available Points:</span>
            <span className="points-value">{pointsInfo?.available_points || 0}</span>
          </div>
          <div className="points-subtext">
            Earned from {pointsInfo?.total_hours || 0} volunteer hours
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="gift-card-grid">
        {giftCardOptions.map((option) => {
          const canAfford = pointsInfo?.available_points >= option.points_required;
          const isRedeeming = redeeming === `${option.provider}-${option.denomination}`;
          
          return (
            <div 
              key={`${option.provider}-${option.denomination}`}
              className={`gift-card-option ${!canAfford ? 'insufficient-points' : ''}`}
            >
              <div className="card-header">
                <div 
                  className="provider-logo"
                  style={{ backgroundColor: getProviderColor(option.provider) }}
                >
                  {getProviderLogo(option.provider)}
                </div>
                <div className="card-value">${option.denomination}</div>
              </div>
              
              <div className="card-details">
                <h3>{option.name}</h3>
                <p>{option.description}</p>
                
                <div className="points-cost">
                  <span className="cost-label">Cost:</span>
                  <span className="cost-value">{option.points_required} points</span>
                </div>
              </div>
              
              <button
                className={`redeem-button ${canAfford ? 'available' : 'disabled'}`}
                disabled={!canAfford || isRedeeming}
                onClick={() => handleRedeem(option.provider, option.denomination)}
              >
                {isRedeeming ? 'Redeeming...' : canAfford ? 'Redeem' : 'Insufficient Points'}
              </button>
            </div>
          );
        })}
      </div>

      {redemptions.length > 0 && (
        <div className="redemption-history">
          <h3>🎟️ Your Redemption History</h3>
          <div className="history-list">
            {redemptions.slice(0, 5).map((redemption) => (
              <div key={redemption.id} className="history-item">
                <div className="history-card">
                  <span className="provider-logo-small">
                    {getProviderLogo(redemption.provider)}
                  </span>
                  <div className="redemption-details">
                    <div className="redemption-name">
                      {redemption.provider.charAt(0).toUpperCase() + redemption.provider.slice(1)} 
                      ${redemption.denomination} Gift Card
                    </div>
                    <div className="redemption-date">
                      {new Date(redemption.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="redemption-status">
                    <span className={`status-badge ${redemption.status}`}>
                      {redemption.status}
                    </span>
                    {redemption.status === 'fulfilled' && redemption.redemption_code && (
                      <div className="redemption-code">
                        Code: {redemption.redemption_code}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GiftCardStore;