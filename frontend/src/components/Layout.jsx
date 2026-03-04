import React, { Fragment } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutGrid, Package, ShoppingCart, User, LogOut, Truck, Settings, ChevronDown, LineChart } from 'lucide-react';
import { Menu, Transition } from '@headlessui/react';

const Layout = ({ children, isFixed = false, isDark = false }) => {
  const location = useLocation();
  const username = localStorage.getItem('username') || 'User';
  const role = localStorage.getItem('userRole') || 'Staff';

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutGrid },
    { name: 'Inventory', path: '/inventory', icon: Package },
    { name: 'Forecast', path: '/forecast', icon: LineChart },
    { name: 'Suppliers', path: '/suppliers', icon: Truck },
    { name: 'Orders', path: '/orders', icon: ShoppingCart },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    window.location.href = '/';
  };

  function classNames(...classes) {
    return classes.filter(Boolean).join(' ')
  }

  return (
    <div className={`flex flex-col ${isDark ? 'bg-gray-900 text-gray-100' : 'bg-slate-50'} ${isFixed ? 'h-screen overflow-hidden' : 'min-h-screen'}`}>
      {/* Header */}
      <header className={`${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b sticky top-0 z-50 flex-none`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <div className="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-2">
                    <Package className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">InventoryAI</span>
              </div>
              <nav className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navItems.map((item) => {
                  const isActive = location.pathname.startsWith(item.path);
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? (isDark ? 'border-indigo-400 text-white' : 'border-indigo-500 text-gray-900')
                          : (isDark ? 'border-transparent text-gray-400 hover:border-gray-300 hover:text-gray-200' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700')
                      }`}
                    >
                      <item.icon className={`h-4 w-4 mr-2 ${isActive ? (isDark ? 'text-indigo-400' : 'text-indigo-500') : 'text-gray-400'}`} />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="flex items-center">
              {/* Profile Dropdown */}
              <Menu as="div" className="relative ml-3">
                <div>
                  <Menu.Button className={`flex max-w-xs items-center rounded-full ${isDark ? 'bg-gray-800' : 'bg-white'} text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}>
                    <span className="sr-only">Open user menu</span>
                    <div className={`flex items-center gap-2 px-3 py-1 border ${isDark ? 'border-gray-600 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'} rounded-full transition-colors`}>
                        <div className={`h-8 w-8 rounded-full ${isDark ? 'bg-indigo-900 text-indigo-200' : 'bg-indigo-100 text-indigo-600'} flex items-center justify-center font-bold`}>
                          {username.charAt(0).toUpperCase()}
                        </div>
                        <div className="hidden md:block text-left">
                            <p className={`text-sm font-medium ${isDark ? 'text-gray-200' : 'text-gray-700'} leading-none`}>{username}</p>
                            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'} mt-0.5`}>{role}</p>
                        </div>
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                    </div>
                  </Menu.Button>
                </div>
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <Menu.Item>
                      {({ active }) => (
                        <Link
                          to="/profile"
                          className={classNames(active ? 'bg-gray-100' : '', 'flex px-4 py-2 text-sm text-gray-700 items-center')}
                        >
                          <User className="mr-2 h-4 w-4" />
                          Profile
                        </Link>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="#"
                          className={classNames(active ? 'bg-gray-100' : '', 'flex px-4 py-2 text-sm text-gray-700 items-center')}
                        >
                          <Settings className="mr-2 h-4 w-4" />
                          Settings
                        </a>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleLogout}
                          className={classNames(active ? 'bg-gray-100' : '', 'flex w-full text-left px-4 py-2 text-sm text-gray-700 items-center')}
                        >
                          <LogOut className="mr-2 h-4 w-4" />
                          Logout
                        </button>
                      )}
                    </Menu.Item>
                  </Menu.Items>
                </Transition>
              </Menu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className={`flex-1 w-full ${!isFixed ? 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8' : ''} ${isFixed ? 'overflow-hidden' : ''}`}>
        {children}
      </main>

      {/* Footer */}
      <footer className={`${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t mt-auto flex-none`}>
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <p className={`text-center text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            &copy; {new Date().getFullYear()} InventoryAI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
