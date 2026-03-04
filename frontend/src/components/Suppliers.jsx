import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import {
  Card,
  Title,
  Text,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Badge,
  Button,
} from "@tremor/react";
import { Plus, X } from 'lucide-react';
import axios from 'axios';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { Fragment } from 'react';

const Suppliers = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newVendor, setNewVendor] = useState({
    vendor_name: '',
    contact_person: '',
    phone_number: '',
    is_overseas: false
  });
  const userRole = localStorage.getItem('userRole');

  const fetchVendors = async () => {
    try {
      const response = await axios.get('/api/vendors');
      setVendors(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching vendors", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewVendor(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/vendors', newVendor);
      setIsModalOpen(false);
      setNewVendor({
        vendor_name: '',
        contact_person: '',
        phone_number: '',
        is_overseas: false
      });
      fetchVendors(); // Refresh list
    } catch (error) {
      console.error("Error adding vendor", error);
      alert("Failed to add vendor");
    }
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <div>
          <Title>Suppliers</Title>
          <Text>Manage your vendors and suppliers.</Text>
        </div>
        {(userRole === 'Manager' || userRole === 'Admin') && (
            <Button icon={Plus} onClick={() => setIsModalOpen(true)}>
            Add Vendor
            </Button>
        )}
      </div>

      <Card>
        {loading ? (
           <div className="mt-6 text-center">Loading Vendors...</div>
        ) : (
            <Table className="mt-6">
            <TableHead>
                <TableRow>
                <TableHeaderCell>Vendor Name</TableHeaderCell>
                <TableHeaderCell>Contact Person</TableHeaderCell>
                <TableHeaderCell>Phone Number</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {vendors.map((vendor) => (
                <TableRow key={vendor.id}>
                    <TableCell className="font-medium text-gray-900">
                        {vendor.vendor_name}
                    </TableCell>
                    <TableCell>
                        {vendor.contact_person}
                    </TableCell>
                    <TableCell>
                        {vendor.phone_number}
                    </TableCell>
                    <TableCell>
                        {vendor.is_overseas ? (
                            <Badge color="blue">Overseas</Badge>
                        ) : (
                            <Badge color="gray">Domestic</Badge>
                        )}
                    </TableCell>
                </TableRow>
                ))}
            </TableBody>
            </Table>
        )}
      </Card>

      {/* Add Vendor Modal */}
      <Transition show={isModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsModalOpen(false)}>
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
                      Add New Vendor
                    </DialogTitle>
                    <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Vendor Name</label>
                      <input
                        type="text"
                        name="vendor_name"
                        required
                        value={newVendor.vendor_name}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Contact Person</label>
                      <input
                        type="text"
                        name="contact_person"
                        value={newVendor.contact_person}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                      <input
                        type="text"
                        name="phone_number"
                        value={newVendor.phone_number}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        name="is_overseas"
                        id="is_overseas"
                        checked={newVendor.is_overseas}
                        onChange={handleInputChange}
                        className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <label htmlFor="is_overseas" className="ml-2 block text-sm text-gray-900">
                        Overseas Vendor
                      </label>
                    </div>

                    <div className="mt-6 flex justify-end space-x-3">
                      <button
                        type="button"
                        onClick={() => setIsModalOpen(false)}
                        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                      >
                        Add Vendor
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

export default Suppliers;
