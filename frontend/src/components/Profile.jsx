import React from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button } from "@tremor/react";
import { User, LogOut } from 'lucide-react';

const Profile = () => {
  const username = localStorage.getItem('username') || 'User';
  const role = localStorage.getItem('userRole') || 'Staff';

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
      </div>
    </Layout>
  );
};

export default Profile;
