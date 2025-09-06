import React, { useState, useCallback } from 'react';
import { Delete, Hash } from 'lucide-react';

export const PINEntry = ({ onPinSubmit, maxLength = 6, isActive }) => {
  const [pin, setPin] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNumberClick = useCallback((number) => {
    if (pin.length < maxLength) {
      setPin(prev => prev + number);
    }
  }, [pin.length, maxLength]);

  const handleBackspace = useCallback(() => {
    setPin(prev => prev.slice(0, -1));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (pin.length >= 4) {
      setIsSubmitting(true);
      try {
        await onPinSubmit(pin);
        setPin('');
      } catch (error) {
        console.error('PIN submission error:', error);
      } finally {
        setIsSubmitting(false);
      }
    }
  }, [pin, onPinSubmit]);

  const handleClear = useCallback(() => {
    setPin('');
  }, []);

  if (!isActive) return null;

  const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Hash className="w-8 h-8 mx-auto mb-2 text-gray-400" />
        <h3 className="text-lg font-semibold text-gray-700">Enter Your PIN</h3>
        <p className="text-sm text-gray-500 mt-1">4-6 digit PIN</p>
      </div>

      {/* PIN Display */}
      <div className="flex justify-center space-x-2">
        {Array.from({ length: maxLength }).map((_, index) => (
          <div
            key={index}
            className={`w-4 h-4 rounded-full border-2 ${
              index < pin.length
                ? 'bg-blue-500 border-blue-500'
                : 'bg-gray-100 border-gray-200'
            }`}
          />
        ))}
      </div>

      {/* Number Pad */}
      <div className="grid grid-cols-3 gap-4 max-w-xs mx-auto">
        {numbers.slice(0, 9).map((number) => (
          <button
            key={number}
            onClick={() => handleNumberClick(number.toString())}
            disabled={pin.length >= maxLength || isSubmitting}
            className="h-16 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 
                     disabled:cursor-not-allowed text-xl font-semibold transition-colors
                     active:bg-gray-300"
          >
            {number}
          </button>
        ))}
        
        {/* Bottom row: Clear, 0, Backspace */}
        <button
          onClick={handleClear}
          disabled={pin.length === 0 || isSubmitting}
          className="h-16 rounded-lg bg-red-100 hover:bg-red-200 disabled:opacity-50 
                   disabled:cursor-not-allowed transition-colors flex items-center justify-center
                   active:bg-red-300"
        >
          <span className="text-sm font-medium text-red-700">Clear</span>
        </button>
        
        <button
          onClick={() => handleNumberClick('0')}
          disabled={pin.length >= maxLength || isSubmitting}
          className="h-16 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 
                   disabled:cursor-not-allowed text-xl font-semibold transition-colors
                   active:bg-gray-300"
        >
          0
        </button>
        
        <button
          onClick={handleBackspace}
          disabled={pin.length === 0 || isSubmitting}
          className="h-16 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 
                   disabled:cursor-not-allowed transition-colors flex items-center justify-center
                   active:bg-gray-300"
        >
          <Delete className="w-6 h-6" />
        </button>
      </div>

      {/* Submit Button */}
      <div className="text-center">
        <button
          onClick={handleSubmit}
          disabled={pin.length < 4 || isSubmitting}
          className="px-8 py-3 bg-blue-500 text-white rounded-lg font-medium
                   hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed
                   transition-colors"
        >
          {isSubmitting ? 'Checking...' : 'Check In'}
        </button>
      </div>
    </div>
  );
};