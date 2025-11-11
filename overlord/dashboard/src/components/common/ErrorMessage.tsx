/**
 * Error Message Component - Displays error messages
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ title = 'Error', message, onRetry }: ErrorMessageProps) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="max-w-md w-full">
        <div className="alert alert-danger">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold mb-1">{title}</h3>
              <p className="text-sm">{message}</p>
              {onRetry && (
                <button onClick={onRetry} className="btn btn-sm btn-danger mt-3">
                  Try Again
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
