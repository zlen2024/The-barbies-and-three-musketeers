import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, Select, SelectItem } from "@tremor/react";
import axios from 'axios';
import { UserPlus } from 'lucide-react';

const TeamManagement = () => {
  const [users, setUsers] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  // State for assignment form
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // In a real app we'd have dedicated endpoints for users and locations lists
      // Here we'll just mock it or handle a simplified assign location action
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data", error);
      setLoading(false);
    }
  };

  const handleAssignLocation = async () => {
    if (!selectedUser || !selectedLocation) {
        alert("Please select both a user and a location.");
        return;
    }

    try {
      await axios.post('/api/assign-location', {
          user_id: parseInt(selectedUser),
          location_id: parseInt(selectedLocation)
      });
      alert("Location assigned successfully!");
      // Reset form
      setSelectedUser("");
      setSelectedLocation("");
    } catch (error) {
      console.error("Error assigning location", error);
      alert("Failed to assign location: " + (error.response?.data?.message || error.message));
    }
  };

  if (loading) {
    return <Layout><div className="p-10 text-center">Loading Team Data...</div></Layout>;
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Title>Team Management</Title>
            <Text>Manage users and their assigned locations.</Text>
          </div>
        </div>

        <Card>
            <Title>Assign User to Location</Title>
            <Text>Select a user and a location to grant them access to that facility.</Text>

            <div className="mt-4 flex flex-col md:flex-row gap-4 items-end">
                <div className="w-full md:w-1/3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
                    <input
                        type="number"
                        value={selectedUser}
                        onChange={(e) => setSelectedUser(e.target.value)}
                        placeholder="Enter User ID (e.g., 2)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                </div>
                <div className="w-full md:w-1/3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location ID</label>
                    <input
                        type="number"
                        value={selectedLocation}
                        onChange={(e) => setSelectedLocation(e.target.value)}
                        placeholder="Enter Location ID (e.g., 1)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                </div>
                <Button icon={UserPlus} onClick={handleAssignLocation} className="w-full md:w-auto">
                    Assign Location
                </Button>
            </div>
            <div className="mt-4 text-sm text-gray-500">
                <p>Note: In a full implementation, you would select from a dropdown of users and locations.</p>
            </div>
        </Card>
      </div>
    </Layout>
  );
};

export default TeamManagement;