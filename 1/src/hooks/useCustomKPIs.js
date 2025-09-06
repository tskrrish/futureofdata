import { useState, useEffect } from "react";

const STORAGE_KEY = "ymca-custom-kpis";

export function useCustomKPIs() {
  const [customKPIs, setCustomKPIs] = useState([]);

  // Load KPIs from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setCustomKPIs(Array.isArray(parsed) ? parsed : []);
      }
    } catch (error) {
      console.warn("Failed to load custom KPIs from localStorage:", error);
      setCustomKPIs([]);
    }
  }, []);

  // Save KPIs to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(customKPIs));
    } catch (error) {
      console.warn("Failed to save custom KPIs to localStorage:", error);
    }
  }, [customKPIs]);

  const saveKPI = (kpi, action = 'create') => {
    setCustomKPIs(prevKPIs => {
      switch (action) {
        case 'create':
          return [...prevKPIs, { ...kpi, createdAt: new Date().toISOString() }];
        
        case 'edit':
          return prevKPIs.map(existingKPI => 
            existingKPI.id === kpi.id 
              ? { ...kpi, updatedAt: new Date().toISOString() }
              : existingKPI
          );
        
        case 'delete':
          return prevKPIs.filter(existingKPI => existingKPI.id !== kpi.id);
        
        default:
          return prevKPIs;
      }
    });
  };

  const getKPI = (id) => {
    return customKPIs.find(kpi => kpi.id === id);
  };

  const clearAllKPIs = () => {
    setCustomKPIs([]);
  };

  return {
    customKPIs,
    saveKPI,
    getKPI,
    clearAllKPIs
  };
}