export function getDaysUntilExpiry(expiryDate) {
  if (!expiryDate) return null;
  
  const expiry = new Date(expiryDate);
  const today = new Date();
  
  if (isNaN(expiry.getTime())) return null;
  
  const diffTime = expiry - today;
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export function getCertificationStatus(expiryDate) {
  const daysUntilExpiry = getDaysUntilExpiry(expiryDate);
  
  if (daysUntilExpiry === null) return 'unknown';
  if (daysUntilExpiry < 0) return 'expired';
  if (daysUntilExpiry <= 7) return 'urgent';
  if (daysUntilExpiry <= 30) return 'warning';
  if (daysUntilExpiry <= 60) return 'attention';
  return 'valid';
}

export function processCertificationData(certifications, branchFilter = 'All', criticalityFilter = 'all') {
  let filtered = certifications;
  
  if (branchFilter !== 'All') {
    filtered = filtered.filter(cert => cert.branch === branchFilter);
  }
  
  if (criticalityFilter !== 'all') {
    filtered = filtered.filter(cert => cert.criticality === criticalityFilter);
  }
  
  const processed = filtered.map(cert => ({
    ...cert,
    daysUntilExpiry: getDaysUntilExpiry(cert.expiry_date),
    status: getCertificationStatus(cert.expiry_date)
  }));
  
  const expiryRadar = {
    expired: processed.filter(cert => cert.status === 'expired'),
    urgent: processed.filter(cert => cert.status === 'urgent'),
    warning: processed.filter(cert => cert.status === 'warning'),
    attention: processed.filter(cert => cert.status === 'attention'),
    valid: processed.filter(cert => cert.status === 'valid')
  };
  
  const byBranch = {};
  processed.forEach(cert => {
    if (!byBranch[cert.branch]) {
      byBranch[cert.branch] = {
        expired: 0,
        urgent: 0, 
        warning: 0,
        attention: 0,
        valid: 0,
        total: 0
      };
    }
    byBranch[cert.branch][cert.status]++;
    byBranch[cert.branch].total++;
  });
  
  const byCriticality = {};
  processed.forEach(cert => {
    if (!byCriticality[cert.criticality]) {
      byCriticality[cert.criticality] = {
        expired: 0,
        urgent: 0,
        warning: 0,
        attention: 0,
        valid: 0,
        total: 0
      };
    }
    byCriticality[cert.criticality][cert.status]++;
    byCriticality[cert.criticality].total++;
  });
  
  const upcomingExpirations = processed
    .filter(cert => cert.status === 'urgent' || cert.status === 'warning')
    .sort((a, b) => a.daysUntilExpiry - b.daysUntilExpiry);
  
  return {
    all: processed,
    expiryRadar,
    byBranch,
    byCriticality,
    upcomingExpirations,
    summary: {
      total: processed.length,
      expired: expiryRadar.expired.length,
      urgent: expiryRadar.urgent.length,
      warning: expiryRadar.warning.length,
      attention: expiryRadar.attention.length,
      valid: expiryRadar.valid.length
    }
  };
}

export function getStatusColor(status) {
  const colors = {
    expired: 'bg-red-500',
    urgent: 'bg-red-400',
    warning: 'bg-orange-400',
    attention: 'bg-yellow-400',
    valid: 'bg-green-400',
    unknown: 'bg-gray-400'
  };
  return colors[status] || colors.unknown;
}

export function getStatusLabel(status) {
  const labels = {
    expired: 'Expired',
    urgent: 'Urgent (≤7 days)',
    warning: 'Warning (≤30 days)',
    attention: 'Attention (≤60 days)',
    valid: 'Valid',
    unknown: 'Unknown'
  };
  return labels[status] || labels.unknown;
}

export function getCriticalityColor(criticality) {
  const colors = {
    critical: 'text-red-600 bg-red-50 border-red-200',
    high: 'text-orange-600 bg-orange-50 border-orange-200',
    medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    low: 'text-green-600 bg-green-50 border-green-200'
  };
  return colors[criticality] || colors.medium;
}