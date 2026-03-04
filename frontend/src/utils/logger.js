/**
 * A simple logger utility for the frontend that mirrors logs to the console
 * and sends error/warning logs to the backend for centralized monitoring.
 */

const sendLogToBackend = async (level, message, stack = '') => {
  try {
    await fetch('/api/client-logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ level, message, stack }),
    });
  } catch (err) {
    // Failsafe so the logger itself doesn't cause infinite error loops
    console.error('Failed to send log to backend:', err);
  }
};

const logger = {
  info: (message, ...args) => {
    console.log(`[INFO] ${message}`, ...args);
  },
  warn: (message, ...args) => {
    console.warn(`[WARN] ${message}`, ...args);
    sendLogToBackend('warn', message);
  },
  error: (message, stack = '', ...args) => {
    console.error(`[ERROR] ${message}`, ...args);
    sendLogToBackend('error', message, stack);
  }
};

export default logger;
