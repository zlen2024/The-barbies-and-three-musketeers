import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import InventoryList from './components/InventoryList';
import ProductDetail from './components/ProductDetail';
import Suppliers from './components/Suppliers';
import Orders from './components/Orders';
import OrderDetail from './components/OrderDetail';
import Profile from './components/Profile';
import './index.css';

// Simple Protected Route Component
const ProtectedRoute = ({ children }) => {
  // In a real app, check for token/session validity
  // Here we just check if userRole exists in localStorage for demo
  const userRole = localStorage.getItem('userRole');
  if (!userRole) {
    return <Navigate to="/" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inventory"
          element={
            <ProtectedRoute>
              <InventoryList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inventory/product/:sku"
          element={
            <ProtectedRoute>
              <ProductDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/suppliers"
          element={
            <ProtectedRoute>
              <Suppliers />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders/:orderId"
          element={
            <ProtectedRoute>
              <OrderDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        {/* Redirect unknown routes to Login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
