import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, TextInput, Select, SelectItem, Badge } from "@tremor/react";
import { User, Users, Mail, Settings, LogOut, UserPlus, Send, Archive, Inbox, MessageSquarePlus } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';

const Workspace = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const role = localStorage.getItem('userRole') || 'Staff';

  return (
    <Layout>
      <div className="flex flex-col md:flex-row gap-6 min-h-[calc(100vh-8rem)]">
        {/* Sidebar */}
        <div className="w-full md:w-64 flex-none bg-white border border-gray-200 rounded-lg shadow-sm p-4 h-fit">
          <div className="space-y-1">
            <button
              onClick={() => setActiveTab('profile')}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'profile' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <User className="h-4 w-4" />
              My Profile
            </button>
            <button
              onClick={() => setActiveTab('team')}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'team' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Users className="h-4 w-4" />
              My Team
            </button>
            <button
              onClick={() => setActiveTab('mail')}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'mail' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Mail className="h-4 w-4" />
              Mail
            </button>
            <button
              onClick={() => {
                setActiveTab('settings');
                toast.info("Settings are coming soon!");
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'settings' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>

            <div className="pt-4 mt-4 border-t border-gray-200">
              <button
                onClick={() => {
                  localStorage.clear();
                  window.location.href = '/';
                }}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 min-w-0">
          {activeTab === 'profile' && <ProfileTab />}
          {activeTab === 'team' && <TeamTab role={role} setActiveTab={setActiveTab} />}
          {activeTab === 'mail' && <MailTab />}
          {activeTab === 'settings' && (
            <Card>
                <Title>Settings</Title>
                <Text>Coming Soon...</Text>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
};

// --- Sub-components ---

const ProfileTab = () => {
  const username = localStorage.getItem('username') || 'User';
  const role = localStorage.getItem('userRole') || 'Staff';
  const email = localStorage.getItem('userEmail') || `${username}@chinhinforcast.com`;

  return (
    <Card className="p-8 max-w-2xl">
      <Title className="mb-6">My Profile</Title>
      <div className="flex flex-col md:flex-row items-center gap-8">
         <div className="h-32 w-32 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-5xl font-bold flex-shrink-0">
            {username.charAt(0).toUpperCase()}
         </div>
         <div className="flex-1 space-y-4 w-full">
            <div>
                <label className="block text-sm font-medium text-gray-500">Username</label>
                <div className="mt-1 text-lg font-semibold text-gray-900">{username}</div>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-500">Email Address</label>
                <div className="mt-1 text-lg text-gray-900">{email}</div>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-500">Role</label>
                <div className="mt-1">
                    <Badge color="indigo" size="lg">{role}</Badge>
                </div>
            </div>
         </div>
      </div>
      <div className="mt-8 pt-6 border-t border-gray-200">
         <Button
            variant="secondary"
            icon={User}
            onClick={() => toast.info('Edit Profile functionality coming soon!')}
         >
            Edit Profile
         </Button>
      </div>
    </Card>
  );
};

const TeamTab = ({ role, setActiveTab }) => {
  const [teamData, setTeamData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Manager assignment state
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");
  const [usersList, setUsersList] = useState([]);
  const [locationsList, setLocationsList] = useState([]);

  useEffect(() => {
    fetchTeam();
    if (role === 'Manager') {
        fetchManagerData();
    }
  }, [role]);

  const fetchTeam = async () => {
    try {
      const res = await axios.get('/api/workspace/team');
      setTeamData(res.data);
    } catch (err) {
      toast.error('Failed to load team data');
    } finally {
      setLoading(false);
    }
  };

  const fetchManagerData = async () => {
    try {
      const [uRes, lRes] = await Promise.all([
          axios.get('/api/workspace/users'),
          axios.get('/api/locations')
      ]);
      setUsersList(uRes.data?.users || []);
      setLocationsList(Array.isArray(lRes.data) ? lRes.data : (lRes.data?.locations || []));
    } catch (err) {
        console.error("Failed to load users/locations for manager", err);
    }
  };


  const [newUser, setNewUser] = useState({ username: '', email: '', password: '', role: 'Staff' });
  const [creatingUser, setCreatingUser] = useState(false);

  const handleCreateUser = async () => {
      if (!newUser.username || !newUser.email || !newUser.password || !newUser.role) {
          alert('Please fill in all fields.');
          return;
      }
      setCreatingUser(true);
      try {
          await axios.post('/api/users', newUser);
          alert('User created successfully');
          setNewUser({ username: '', email: '', password: '', role: 'Staff' });
          fetchWorkspaceData(); // Refresh the users list
      } catch (e) {
          alert('Error creating user: ' + (e.response?.data?.error || e.message));
      } finally {
          setCreatingUser(false);
      }
  };

  const handleAssignLocation = async () => {
    if (!selectedUser || !selectedLocation) {
        toast.warning("Please select both a user and a location.");
        return;
    }

    try {
      await axios.post('/api/assign-location', {
          uid: parseInt(selectedUser),
          location_id: parseInt(selectedLocation)
      });
      toast.success("Location assigned successfully!");
      setSelectedUser("");
      setSelectedLocation("");
      fetchTeam(); // Refresh team view
    } catch (error) {
      toast.error("Failed to assign location: " + (error.response?.data?.message || error.message));
    }
  };

  const openMessage = (user) => {
      // Small hack: store recipient info temporarily so Mail tab can pick it up
      window.sessionStorage.setItem('composeTo', JSON.stringify({id: user.id, name: user.username}));
      setActiveTab('mail');
  };

  if (loading) return <Card><Text>Loading team...</Text></Card>;

  return (
    <div className="space-y-6">
      {role === 'Manager' && (
          <Card>
            <Title>Team Management</Title>
            <Text>Assign users to locations.</Text>

            <div className="mt-4 flex flex-col md:flex-row gap-4 items-end">
                <div className="w-full md:w-1/3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Select User</label>
                    <Select value={selectedUser} onValueChange={setSelectedUser} placeholder="Select User">
                        {usersList.map(u => (
                            <SelectItem key={u.id} value={u.id.toString()}>{u.username} ({u.role})</SelectItem>
                        ))}
                    </Select>
                </div>
                <div className="w-full md:w-1/3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Select Location</label>
                    <Select value={selectedLocation} onValueChange={setSelectedLocation} placeholder="Select Location">
                        {locationsList.map(l => (
                            <SelectItem key={l.id} value={l.id.toString()}>{l.loc_code} - {l.description}</SelectItem>
                        ))}
                    </Select>
                </div>
                <Button icon={UserPlus} onClick={handleAssignLocation} className="w-full md:w-auto shrink-0">
                    Assign Location
                </Button>
                <Button variant="secondary" onClick={() => toast.warning("Role changes are not available.")} className="w-full md:w-auto shrink-0">
                    Change Role
                </Button>
            </div>
          </Card>
      )}

      {role === 'Admin' && (
          <Card>
            <Title>Add New User</Title>
            <Text>Create a new system user account.</Text>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <TextInput value={newUser.username} onChange={e => setNewUser({...newUser, username: e.target.value})} placeholder="Username" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <TextInput value={newUser.email} onChange={e => setNewUser({...newUser, email: e.target.value})} placeholder="Email" type="email" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <TextInput value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})} placeholder="Password" type="password" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                    <Select value={newUser.role} onValueChange={val => setNewUser({...newUser, role: val})} placeholder="Select Role">
                        {['Admin', 'Manager', 'Warehouse', 'Procurement', 'Sales', 'Staff'].map(r => (
                            <SelectItem key={r} value={r}>{r}</SelectItem>
                        ))}
                    </Select>
                </div>
            </div>
            <div className="mt-4 flex justify-end">
                <Button icon={UserPlus} onClick={handleCreateUser} disabled={creatingUser}>
                    {creatingUser ? 'Creating...' : 'Create User'}
                </Button>
            </div>
          </Card>
      )}


      <Card>
          <Title>My Team</Title>
          <Text className="mb-4">Members of your assigned location(s).</Text>

          {(role === 'Manager' || role === 'Admin') && teamData?.team_grouped ? (
              <div className="space-y-6">
                  {teamData.team_grouped.map((group) => (
                      <div key={group.location_id} className="border rounded-lg overflow-hidden">
                          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                              <h3 className="font-semibold text-gray-900">{group.location_name}</h3>
                          </div>
                          <Table>
                              <TableHead>
                                <TableRow>
                                    <TableHeaderCell>Name</TableHeaderCell>
                                    <TableHeaderCell>Role</TableHeaderCell>
                                    <TableHeaderCell>Email</TableHeaderCell>
                                    <TableHeaderCell className="text-right">Action</TableHeaderCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                  {group.members.map(member => (
                                      <TableRow key={member.id}>
                                          <TableCell className="font-medium text-gray-900">{member.username}</TableCell>
                                          <TableCell><Badge size="xs" color="gray">{member.role}</Badge></TableCell>
                                          <TableCell>{member.email}</TableCell>
                                          <TableCell className="text-right">
                                              <Button size="xs" variant="light" icon={Send} onClick={() => openMessage(member)}>Message</Button>
                                          </TableCell>
                                      </TableRow>
                                  ))}
                                  {group.members.length === 0 && (
                                      <TableRow><TableCell colSpan="4" className="text-center text-gray-500 py-4">No members assigned.</TableCell></TableRow>
                                  )}
                              </TableBody>
                          </Table>
                      </div>
                  ))}
              </div>
          ) : (
              <Table>
                  <TableHead>
                    <TableRow>
                        <TableHeaderCell>Name</TableHeaderCell>
                        <TableHeaderCell>Role</TableHeaderCell>
                        <TableHeaderCell>Email</TableHeaderCell>
                        <TableHeaderCell className="text-right">Action</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                      {teamData?.team?.map(member => (
                          <TableRow key={member.id}>
                              <TableCell className="font-medium text-gray-900">{member.username}</TableCell>
                              <TableCell><Badge size="xs" color="gray">{member.role}</Badge></TableCell>
                              <TableCell>{member.email}</TableCell>
                              <TableCell className="text-right">
                                  <Button size="xs" variant="light" icon={Send} onClick={() => openMessage(member)}>Message</Button>
                              </TableCell>
                          </TableRow>
                      ))}
                      {!teamData?.team?.length && (
                          <TableRow><TableCell colSpan="4" className="text-center text-gray-500 py-4">No team members found.</TableCell></TableRow>
                      )}
                  </TableBody>
              </Table>
          )}
      </Card>
    </div>
  );
};

const MailTab = () => {
  const [view, setView] = useState('inbox'); // 'inbox', 'sent', 'compose'
  const [mails, setMails] = useState([]);
  const [loading, setLoading] = useState(false);

  // Compose state
  const [usersList, setUsersList] = useState([]);
  const [composeTo, setComposeTo] = useState("");
  const [composeSubject, setComposeSubject] = useState("");
  const [composeBody, setComposeBody] = useState("");

  useEffect(() => {
      // Check if we came from "Message" button
      const prefill = window.sessionStorage.getItem('composeTo');
      if (prefill) {
          const u = JSON.parse(prefill);
          setComposeTo(u.id.toString());
          setView('compose');
          window.sessionStorage.removeItem('composeTo');
      }

      if (view === 'inbox') fetchInbox();
      if (view === 'sent') fetchSent();
      if (view === 'compose') fetchUsers();
  }, [view]);

  const fetchInbox = async () => {
      setLoading(true);
      try {
          const res = await axios.get('/api/workspace/mail/inbox');
          setMails(res.data.mails || []);
      } catch (e) {
          toast.error("Failed to fetch inbox");
      }
      setLoading(false);
  };

  const fetchSent = async () => {
      setLoading(true);
      try {
          const res = await axios.get('/api/workspace/mail/sent');
          setMails(res.data.mails || []);
      } catch (e) {
          toast.error("Failed to fetch sent mail");
      }
      setLoading(false);
  };

  const fetchUsers = async () => {
      try {
          // Re-using manager endpoint but we can just use the team endpoint to get people to mail
          // Actually, let's just fetch all users for simplicity in internal mail, or create a specific endpoint.
          // Since /api/workspace/users requires Manager role, we should use team members if non-manager.
          // For this hackathon scope, let's try calling team endpoint to get valid recipients.
          const res = await axios.get('/api/workspace/team');
          let validUsers = [];
          if (res.data.team_grouped) {
             res.data.team_grouped.forEach(g => validUsers.push(...g.members));
          } else if (res.data.team) {
             validUsers = res.data.team;
          }

          // Deduplicate users
          const uniqueUsers = Array.from(new Map(validUsers.map(u => [u.id, u])).values());
          setUsersList(uniqueUsers);

      } catch (e) {
          console.error("Error fetching recipients", e);
      }
  };

  const handleSend = async () => {
      if (!composeTo || !composeSubject || !composeBody) {
          toast.error("Please fill in all fields");
          return;
      }
      try {
          await axios.post('/api/workspace/mail/send', {
              receiver_id: parseInt(composeTo),
              subject: composeSubject,
              body: composeBody
          });
          toast.success("Mail sent!");
          setComposeTo("");
          setComposeSubject("");
          setComposeBody("");
          setView('inbox');
      } catch (e) {
          toast.error("Failed to send mail");
      }
  };

  const markRead = async (id) => {
      try {
          await axios.post(`/api/workspace/mail/${id}/read`);
          fetchInbox();
      } catch (e) {}
  };

  return (
      <Card className="h-full min-h-[500px] flex flex-col">
          <div className="flex justify-between items-center mb-6 pb-4 border-b">
              <div className="flex space-x-2">
                  <Button variant={view === 'inbox' ? 'primary' : 'light'} icon={Inbox} onClick={() => setView('inbox')}>Inbox</Button>
                  <Button variant={view === 'sent' ? 'primary' : 'light'} icon={Send} onClick={() => setView('sent')}>Sent</Button>
              </div>
              <Button icon={MessageSquarePlus} onClick={() => setView('compose')}>Compose</Button>
          </div>

          <div className="flex-1 overflow-auto">
              {loading && <Text>Loading...</Text>}

              {!loading && (view === 'inbox' || view === 'sent') && (
                  <div className="space-y-4">
                      {mails.length === 0 ? (
                          <div className="text-center py-10 text-gray-500">No messages found.</div>
                      ) : (
                          mails.map(m => (
                              <div key={m.id} className={`p-4 border rounded-lg ${view === 'inbox' && !m.is_read ? 'bg-indigo-50 border-indigo-100' : 'bg-white'}`}>
                                  <div className="flex justify-between mb-2">
                                      <div className="font-semibold text-gray-900">
                                          {view === 'inbox' ? `From: ${m.sender_name}` : `To: ${m.receiver_name}`}
                                      </div>
                                      <div className="text-xs text-gray-500">{new Date(m.timestamp).toLocaleString()}</div>
                                  </div>
                                  <div className="font-medium text-gray-800 mb-2">{m.subject}</div>
                                  <div className="text-gray-600 text-sm whitespace-pre-wrap">{m.body}</div>

                                  {view === 'inbox' && !m.is_read && (
                                      <div className="mt-3 flex justify-end">
                                          <Button size="xs" variant="light" icon={Archive} onClick={() => markRead(m.id)}>Mark as Read</Button>
                                      </div>
                                  )}
                              </div>
                          ))
                      )}
                  </div>
              )}

              {view === 'compose' && (
                  <div className="space-y-4 max-w-2xl">
                      <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
                          <Select value={composeTo} onValueChange={setComposeTo} placeholder="Select team member">
                              {usersList.map(u => (
                                  <SelectItem key={u.id} value={u.id.toString()}>{u.username} ({u.role})</SelectItem>
                              ))}
                          </Select>
                      </div>
                      <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                          <TextInput value={composeSubject} onChange={(e) => setComposeSubject(e.target.value)} placeholder="Enter subject" />
                      </div>
                      <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                          <textarea
                              className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                              value={composeBody}
                              onChange={(e) => setComposeBody(e.target.value)}
                              placeholder="Write your message here..."
                          />
                      </div>
                      <Button icon={Send} onClick={handleSend}>Send Message</Button>
                  </div>
              )}
          </div>
      </Card>
  );
};

export default Workspace;