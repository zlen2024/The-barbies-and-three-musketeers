import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, Badge, Grid, Select, SelectItem, TextInput, NumberInput, DonutChart, Dialog, DialogPanel } from "@tremor/react";
import axios from 'axios';
import { Plus, Check, FileText, Send, DollarSign, PenTool, CheckCircle, Mail, Loader2, MapPin, Search } from 'lucide-react';
import { toast } from 'react-toastify';

const SalesHub = () => {
  const [sales, setSales] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(null);

  // Quote Form State
  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);
  const [assignedLocations, setAssignedLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [locationProducts, setLocationProducts] = useState([]);
  const [quoteForm, setQuoteForm] = useState({
    customer_name: '',
    client_email: '',
    pl_id: '',
    quantity_sold: 1,
    price: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const uid = localStorage.getItem('userId');
    setUserId(uid ? parseInt(uid) : null);
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [salesRes, invoicesRes, dashboardRes, locsRes] = await Promise.all([
        axios.get('/api/sales'),
        axios.get('/api/invoices'),
        axios.get('/api/sales/dashboard'),
        axios.get('/api/locations')
      ]);
      setSales(salesRes.data || []);
      setInvoices(invoicesRes.data || []);
      setDashboardData(dashboardRes.data);

      const userLocations = Array.isArray(locsRes.data) ? locsRes.data : [];
      setAssignedLocations(userLocations);
      if (userLocations.length > 0 && userLocations[0].id) {
        setSelectedLocation(userLocations[0].id.toString());
        fetchProductsForLocation(userLocations[0].id);
      }
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data", error);
      toast.error("Failed to load sales data");
      setLoading(false);
    }
  };

  const fetchProductsForLocation = async (locId) => {
    try {
      const res = await axios.get(`/api/inventory/location/${locId}`);
      setLocationProducts(res.data);
    } catch (error) {
      console.error("Error fetching products", error);
    }
  };

  const handleLocationChange = (val) => {
    setSelectedLocation(val);
    fetchProductsForLocation(val);
  };

  const handleCreateQuote = async () => {
    if (!quoteForm.pl_id || !quoteForm.customer_name || !quoteForm.quantity_sold) {
      toast.error("Please fill in all required fields (Product, Customer Name, Quantity)");
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await axios.post('/api/sales', quoteForm);
      if (res.data.success) {
        toast.success(res.data.message);
        setIsQuoteModalOpen(false);
        setQuoteForm({
          customer_name: '',
          client_email: '',
          pl_id: '',
          quantity_sold: 1,
          price: ''
        });
        fetchData(); // Refresh data
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.message || "Failed to create quote");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStatus = async (saleId, newStatus) => {
    try {
      const res = await axios.put(`/api/sales/${saleId}/status`, { status: newStatus });
      if (res.data.success) {
        toast.success(res.data.message);
        fetchData();
      } else {
        toast.error(res.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.message || "Failed to update status");
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    switch(status) {
      case 'Quoted': return <Badge color="gray" icon={Mail}>Quoted</Badge>;
      case 'Pending Verification': return <Badge color="yellow" icon={PenTool}>Signed</Badge>;
      case 'Verified': return <Badge color="blue" icon={CheckCircle}>Verified</Badge>;
      case 'Paid': return <Badge color="green" icon={DollarSign}>Paid</Badge>;
      default: return <Badge color="gray">{status}</Badge>;
    }
  };

  if (loading) {
    return <Layout><div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-blue-500 h-10 w-10" /></div></Layout>;
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Title className="text-2xl font-bold">Sales Hub</Title>
            <Text>Your command center for quotes, deals, and performance.</Text>
          </div>
          <Button icon={Plus} onClick={() => setIsQuoteModalOpen(true)} className="bg-blue-600 hover:bg-blue-700">
            Create Quotation
          </Button>
        </div>

        {/* Dashboard Performance metrics */}
        {dashboardData && (
          <>
            <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
              <Card decoration="top" decorationColor="blue">
                <Text>My Personal Sales (Verified)</Text>
                <Title className="text-3xl mt-2">{formatCurrency(dashboardData.personalSales)}</Title>
              </Card>
              <Card decoration="top" decorationColor="purple">
                <Text>Team Sales (Assigned Locations)</Text>
                <Title className="text-3xl mt-2">{formatCurrency(dashboardData.teamSales)}</Title>
              </Card>
            </Grid>

            <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
              <Card>
                <Title>My Sales by Location</Title>
                <div className="h-64 mt-4 flex items-center justify-center">
                  {dashboardData.locationDistribution?.length > 0 ? (
                    <DonutChart
                      data={dashboardData.locationDistribution}
                      category="value"
                      index="name"
                      colors={["blue", "cyan", "indigo", "violet", "fuchsia"]}
                      className="h-full w-full"
                    />
                  ) : (
                    <Text>No data available</Text>
                  )}
                </div>
              </Card>
              <Card>
                <Title>Pipeline Status Breakdown</Title>
                <div className="h-64 mt-4 flex items-center justify-center">
                   {dashboardData.statusDistribution?.length > 0 ? (
                    <DonutChart
                      data={dashboardData.statusDistribution}
                      category="value"
                      index="name"
                      colors={["gray", "yellow", "blue", "green"]}
                      className="h-full w-full"
                    />
                  ) : (
                    <Text>No data available</Text>
                  )}
                </div>
              </Card>
            </Grid>
          </>
        )}

        {/* Deals/Sales Table */}
        <Card>
          <div className="flex justify-between items-center mb-4">
            <Title>Client Orders & Deals</Title>
          </div>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>ID</TableHeaderCell>
                <TableHeaderCell>Client</TableHeaderCell>
                <TableHeaderCell>Product</TableHeaderCell>
                <TableHeaderCell>Amount</TableHeaderCell>
                <TableHeaderCell>Date</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sales.map((sale) => (
                <TableRow key={sale.id}>
                  <TableCell>#{sale.id}</TableCell>
                  <TableCell>
                    <div className="font-medium text-gray-900 dark:text-gray-100">{sale.customer_name}</div>
                    <div className="text-xs text-gray-500">{sale.client_email}</div>
                  </TableCell>
                  <TableCell>
                    {sale.items && sale.items.map((item, idx) => (
                      <div key={idx} className="text-sm">
                        {item.quantity}x {item.product_name}
                      </div>
                    ))}
                  </TableCell>
                  <TableCell className="font-medium">{formatCurrency(sale.total_amount)}</TableCell>
                  <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                  <TableCell>{getStatusBadge(sale.status)}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      {sale.status === 'Quoted' && (
                        <Button size="xs" color="gray" variant="secondary" onClick={() => handleUpdateStatus(sale.id, 'Pending Verification')} title="Simulate Client Signature">
                          Sign
                        </Button>
                      )}
                      {sale.status === 'Pending Verification' && sale.sold_by === userId && (
                        <Button size="xs" color="blue" icon={Check} onClick={() => handleUpdateStatus(sale.id, 'Verified')} title="Verify Signature & Gen Invoice">
                          Verify
                        </Button>
                      )}
                      {sale.status === 'Verified' && (
                        <Button size="xs" color="green" variant="secondary" onClick={() => handleUpdateStatus(sale.id, 'Paid')} title="Simulate Client Payment">
                          Pay
                        </Button>
                      )}
                      {sale.status === 'Paid' && (
                        <Button size="xs" color="green" variant="light" icon={FileText}>
                          Receipt
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {sales.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-4">No deals found.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      </div>

      {/* Create Quote Modal */}
      <Dialog open={isQuoteModalOpen} onClose={(val) => setIsQuoteModalOpen(val)} static={true}>
        <DialogPanel className="max-w-xl">
          <Title className="mb-4 text-xl">Create Quotation</Title>
          <div className="space-y-4">
            <div>
              <Text className="mb-1 font-medium">1. Select Location</Text>
              <Select value={selectedLocation} onValueChange={handleLocationChange} icon={MapPin}>
                {assignedLocations.map(loc => (
                  <SelectItem key={loc.id} value={loc.id.toString()}>{loc.loc_code} - {loc.description}</SelectItem>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Text className="mb-1 font-medium">Client Name *</Text>
                <TextInput
                  placeholder="e.g. Acme Corp"
                  value={quoteForm.customer_name}
                  onChange={(e) => setQuoteForm({...quoteForm, customer_name: e.target.value})}
                />
              </div>
              <div>
                <Text className="mb-1 font-medium">Client Email</Text>
                <TextInput
                  type="email"
                  placeholder="client@example.com"
                  value={quoteForm.client_email}
                  onChange={(e) => setQuoteForm({...quoteForm, client_email: e.target.value})}
                />
              </div>
            </div>

            <div className="p-4 bg-gray-50 border border-gray-100 rounded-lg dark:bg-gray-800 dark:border-gray-700">
              <Text className="font-medium mb-3">Product Details</Text>
              <div className="space-y-3">
                <div>
                  <Text className="mb-1 text-sm">Product *</Text>
                  <Select
                    value={quoteForm.pl_id}
                    onValueChange={(val) => setQuoteForm({...quoteForm, pl_id: val})}
                    placeholder="Select product..."
                  >
                    {locationProducts.map(p => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.sku_id} - Stock: {p.quantity}
                      </SelectItem>
                    ))}
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Text className="mb-1 text-sm">Quantity *</Text>
                    <NumberInput
                      min={1}
                      value={quoteForm.quantity_sold}
                      onValueChange={(val) => setQuoteForm({...quoteForm, quantity_sold: val})}
                    />
                  </div>
                  <div>
                    <Text className="mb-1 text-sm">Unit Price (Optional Override)</Text>
                    <TextInput
                      type="number"
                      placeholder="Leave blank for default"
                      value={quoteForm.price}
                      onChange={(e) => setQuoteForm({...quoteForm, price: e.target.value})}
                      icon={DollarSign}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 flex justify-end space-x-3 border-t border-gray-200 dark:border-gray-800">
              <Button variant="light" color="gray" onClick={() => setIsQuoteModalOpen(false)}>Cancel</Button>
              <Button
                icon={Send}
                onClick={handleCreateQuote}
                loading={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Send Quotation
              </Button>
            </div>
          </div>
        </DialogPanel>
      </Dialog>
    </Layout>
  );
};

export default SalesHub;
