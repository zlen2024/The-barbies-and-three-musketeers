import React, { useState, useEffect, Fragment } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell } from "@tremor/react";
import { User, LogOut, MapPin, Plus, X } from 'lucide-react';
import axios from 'axios';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';

const Profile = () => {
  const username = localStorage.getItem('username') || 'User';
  const role = localStorage.getItem('userRole') || 'Staff';
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Assign Location Modal State (Manager only)
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [allUsers, setAllUsers] = useState([]);
  const [allLocations, setAllLocations] = useState([]);
  const [assignData, setAssignData] = useState({ user_id: '', location_id: '' });
  const [assigning, setAssigning] = useState(false);

  useEffect(() => {
      const fetchMyLocations = async () => {
          try {
              const res = await axios.get('/api/my-locations');
              setLocations(res.data);
          } catch (e) {
              console.error("Error fetching my locations", e);
          } finally {
              setLoading(false);
          }
      };

      const fetchAdminData = async () => {
          if (role === 'Manager' || role === 'Admin') {
              try {
                  const [usersRes, locsRes] = await Promise.all([
                      axios.get('/api/all-users'),
                      axios.get('/api/all-locations')
                  ]);
                  setAllUsers(usersRes.data);
                  setAllLocations(locsRes.data);
                  if (usersRes.data.length > 0) setAssignData(prev => ({...prev, user_id: usersRes.data[0].id}));
                  if (locsRes.data.length > 0) setAssignData(prev => ({...prev, location_id: locsRes.data[0].id}));
              } catch (e) {
                  console.error("Error fetching admin data", e);
              }
          }
      };

      fetchMyLocations();
      fetchAdminData();
  }, [role]);

  const handleAssignLocation = async (e) => {
      e.preventDefault();
      setAssigning(true);
      try {
          await axios.post('/api/assign-location', assignData);
          alert("Location assigned successfully");
          setIsAssignModalOpen(false);
          // Refresh my locations if assigned to self (simplification)
          const res = await axios.get('/api/my-locations');
          setLocations(res.data);
      } catch (e) {
          alert("Failed to assign location: " + (e.response?.data?.message || e.message));
      } finally {
          setAssigning(false);
      }
  };

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    window.location.href = '/';
  };

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-10">
        <Card className="p-8">
          <div className="flex flex-col items-center">
             <div className="h-24 w-24 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-4xl font-bold mb-6">
                {username.charAt(0).toUpperCase()}
             </div>
             <Title className="text-2xl font-bold text-gray-900 mb-1">{username}</Title>
             <Text className="text-gray-500 mb-8">{role}</Text>

             <div className="w-full space-y-4">
                 <Button
                    size="xl"
                    variant="secondary"
                    className="w-full justify-center"
                    icon={User}
                    onClick={() => alert('Edit Profile functionality coming soon!')}
                 >
                    Edit Profile
                 </Button>

                 <Button
                    size="xl"
                    color="red"
                    className="w-full justify-center"
                    icon={LogOut}
                    onClick={handleLogout}
                 >
                    Logout
                 </Button>
             </div>
          </div>
        </Card>

        {/* Locations Section */}
        <Card className="p-8 mt-6">
            <div className="flex justify-between items-center mb-4">
                <Title>My Assigned Locations</Title>
                {(role === 'Manager' || role === 'Admin') && (
                    <Button icon={Plus} size="xs" onClick={() => setIsAssignModalOpen(true)}>
                        Assign Location to User
                    </Button>
                )}
            </div>
            {loading ? (
                <Text>Loading locations...</Text>
            ) : locations.length > 0 ? (
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableHeaderCell>Code</TableHeaderCell>
                            <TableHeaderCell>Description</TableHeaderCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {locations.map((loc) => (
                            <TableRow key={loc.ul_id}>
                                <TableCell>{loc.loc_code}</TableCell>
                                <TableCell>{loc.location_name}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            ) : (
                <Text>You are not assigned to any locations.</Text>
            )}
        </Card>
      </div>

      {/* Assign Location Modal */}
      <Transition show={isAssignModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsAssignModalOpen(false)}>
          <TransitionChild
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black/30" />
          </TransitionChild>

          <div className="fixed inset-0 w-screen overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <TransitionChild
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <div className="flex justify-between items-center mb-4">
                    <DialogTitle as="h3" className="text-lg font-medium leading-6 text-gray-900">
                      Assign User Location
                    </DialogTitle>
                    <button onClick={() => setIsAssignModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <form onSubmit={handleAssignLocation} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">User</label>
                      <select
                        required
                        value={assignData.user_id}
                        onChange={(e) => setAssignData({...assignData, user_id: e.target.value})}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      >
                          {allUsers.map(u => (
                              <option key={u.id} value={u.id}>{u.username} ({u.role})</option>
                          ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Location</label>
                      <select
                        required
                        value={assignData.location_id}
                        onChange={(e) => setAssignData({...assignData, location_id: e.target.value})}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      >
                          {allLocations.map(l => (
                              <option key={l.id} value={l.id}>{l.description} ({l.loc_code})</option>
                          ))}
                      </select>
                    </div>

                    <div className="mt-6 flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setIsAssignModalOpen(false)}
                        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={assigning}
                        className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none"
                      >
                        {assigning ? 'Assigning...' : 'Assign Location'}
                      </button>
                    </div>
                  </form>
                </DialogPanel>
              </TransitionChild>
            </div>
          </div>
        </Dialog>
      </Transition>
    </Layout>
  );
};

export default Profile;
