import React, { useState, useEffect, Fragment } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from './Layout';
import {
  Card,
  Text,
  Metric,
  Title,
  Flex,
  Badge,
  Button,
  Callout,
  BarList,
  DonutChart,
  LineChart,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  TextInput
} from "@tremor/react";
import {
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  ShoppingCart,
  BrainCircuit,
  MessageCircle,
  Send,
  Package,
  X,
  Mail
} from 'lucide-react';
import axios from 'axios';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';

const valueFormatter = (number) => `${new Intl.NumberFormat("en-US").format(number).toString()}`;

const ProductDetail = () => {
  const { sku } = useParams();
  const navigate = useNavigate();
  const [productData, setProductData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatMessage, setChatMessage] = useState('');

  // PO Modal State
  const [isPOModalOpen, setIsPOModalOpen] = useState(false);
  const [poQuantity, setPoQuantity] = useState(100);
  const [poVendorId, setPoVendorId] = useState('');
  const [emailPreview, setEmailPreview] = useState('');
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    const fetchProductDetail = async () => {
      try {
        const response = await axios.get(`/api/inventory/products/${sku}`);
        setProductData(response.data);
        setLoading(false);
        // Set default vendor if available
        if (response.data.vendors && response.data.vendors.length > 0) {
            setPoVendorId(response.data.vendors[0].id);
        }
      } catch (error) {
        console.error("Error fetching product detail", error);
        setLoading(false);
      }
    };

    fetchProductDetail();
  }, [sku]);

  if (loading) {
    return (
      <Layout>
        <div className="text-center mt-10">Loading Product Details...</div>
      </Layout>
    );
  }

  if (!productData) {
      return (
          <Layout>
              <div className="text-center mt-10">Product not found.</div>
          </Layout>
      );
  }

  const { product, stock_health, velocity, incoming, analytics, orders, locations, vendors, pricing } = productData;

  // Combine locations and analytics.distribution
  const stockAndSalesData = locations?.map(loc => {
    const saleData = analytics.distribution.find(d => d.name === loc.location);
    return [
      { name: `${loc.location} - Stock`, value: loc.quantity, color: "blue" },
      { name: `${loc.location} - Sales`, value: saleData ? saleData.value : 0, color: "emerald" }
    ];
  }).flat() || [];

  const handleOpenPOModal = () => {
      setIsPOModalOpen(true);
      setEmailPreview('');
  };

  const handleGenerateEmail = () => {
      const vendor = vendors.find(v => v.id == poVendorId);
      const vendorName = vendor ? vendor.name : "Vendor";
      const emailText = `Subject: Purchase Order Request - ${product.name}

Dear ${vendorName} Sales Team,

Please accept this purchase order for the following items:

Item: ${product.name} (SKU: ${product.sku})
Quantity: ${poQuantity} units
Required Delivery: ASAP

Please confirm receipt and provide an estimated delivery date.

Best regards,
Procurement Manager
InventoryAI System`;
      setEmailPreview(emailText);
  };

  const handleSubmitPO = async () => {
      setIsSending(true);
      try {
          await axios.post('/api/generate-pr', {
              sku_id: product.sku,
              quantity: poQuantity,
              vendor_id: poVendorId
          });
          alert("PR Created Successfully!");
          setIsPOModalOpen(false);
          // Refresh data to show new order?
          // For now just close.
      } catch (e) {
          alert("Error creating PR: " + (e.response?.data?.message || e.message));
      } finally {
          setIsSending(false);
      }
  };

  const getStatusColor = (status) => {
    switch(status) {
        case 'In Stock': return 'emerald';
        case 'Low Stock': return 'yellow';
        case 'Critical': return 'red';
        default: return 'gray';
    }
  };

  const chatHistory = [
      { sender: 'ai', text: `I've analyzed the ${product.name}. Based on the ${velocity.trend_percentage}% sales acceleration this month, we are projecting a stockout in 14 days.` }
  ];

  return (
    <Layout isFixed={true}>
      <div className="h-full overflow-y-auto lg:overflow-hidden grid grid-cols-1 lg:grid-cols-4 gap-6">

        {/* Left Column (75% width on large screens) */}
        <div className="col-span-1 lg:col-span-3 space-y-6 lg:h-full lg:overflow-y-auto lg:pr-2">

            {/* Top Row: Product Summary */}
            <Card decoration="top" decorationColor={getStatusColor(product.status)}>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
                    <div>
                        <Title>{product.name}</Title>
                        <Text className="mt-1">SKU: {product.sku} | Category: {product.category}</Text>
                        <div className="mt-2">
                             <Badge color={getStatusColor(product.status)} icon={AlertTriangle}>
                                {product.status}
                             </Badge>
                        </div>
                    </div>
                    <div className="mt-4 sm:mt-0">
                        <Button icon={ShoppingCart} size="lg" color="blue" onClick={handleOpenPOModal}>
                            Create PO
                        </Button>
                    </div>
                </div>
            </Card>

            {/* Middle Row: KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* Stock Health */}
                <Card decoration="top" decorationColor="blue">
                    <Title>Stock Health</Title>
                    <Flex className="mt-4">
                        <Text>Total Physical</Text>
                        <Metric>{stock_health.total_physical}</Metric>
                    </Flex>
                    <Flex className="mt-2">
                        <Text>Reserved (Proj)</Text>
                        <Text>{stock_health.reserved}</Text>
                    </Flex>
                    <div className="h-px bg-gray-200 my-2" />
                    <Flex>
                        <Text>Free to Sell</Text>
                        <Text className="font-bold text-gray-900">{stock_health.free_to_sell}</Text>
                    </Flex>
                </Card>

                {/* Velocity */}
                <Card decoration="top" decorationColor="emerald">
                    <Title>Velocity</Title>
                    <Flex className="mt-4">
                        <Text>AMS (3-Month)</Text>
                        <Metric>{velocity.ams_3m} /mo</Metric>
                    </Flex>
                    <Flex className="mt-2">
                        <Text>AMS (6-Month)</Text>
                        <Text>{velocity.ams_6m} /mo</Text>
                    </Flex>
                    <div className="mt-4">
                         <Badge color={velocity.trend_percentage >= 0 ? "emerald" : "red"} icon={TrendingUp}>
                            {velocity.trend_percentage}% Trend
                         </Badge>
                         <Text className="mt-2 text-xs">
                             Demand is {velocity.trend_percentage >= 0 ? "accelerating" : "decelerating"} compared to last cycle.
                         </Text>
                    </div>
                </Card>

                {/* Incoming */}
                <Card decoration="top" decorationColor="orange">
                    <Title>Incoming</Title>
                    <Flex className="mt-4">
                        <Text>On the way</Text>
                        <Metric>{incoming.total_incoming} units</Metric>
                    </Flex>
                    <Flex className="mt-2">
                        <Text>Next ETA</Text>
                        <Text className="font-bold">{incoming.next_eta}</Text>
                    </Flex>
                    <Callout
                        className="mt-4"
                        title="Stockout Risk"
                        icon={AlertTriangle}
                        color="red"
                    >
                        {incoming.stockout_risk}
                    </Callout>
                </Card>
            </div>

            {/* New Section: Product Info & Logistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 {/* Pricing & Vendors */}
                 <Card>
                    <Title>Pricing & Vendors</Title>
                    <div className="mt-4">
                        <Text className="font-bold">Regional Pricing</Text>
                        <div className="grid grid-cols-3 gap-2 mt-2">
                             <div className="bg-gray-50 p-2 rounded text-center">
                                 <Text className="text-xs">LSP</Text>
                                 <Metric className="text-lg">${pricing?.lsp}</Metric>
                             </div>
                             <div className="bg-gray-50 p-2 rounded text-center">
                                 <Text className="text-xs">West Msia</Text>
                                 <Metric className="text-lg">${pricing?.wm}</Metric>
                             </div>
                             <div className="bg-gray-50 p-2 rounded text-center">
                                 <Text className="text-xs">East Msia</Text>
                                 <Metric className="text-lg">${pricing?.em}</Metric>
                             </div>
                        </div>
                    </div>
                    <div className="mt-6">
                        <Text className="font-bold">Vendors</Text>
                         <Table className="mt-2">
                            <TableHead>
                                <TableRow>
                                    <TableHeaderCell>Name</TableHeaderCell>
                                    <TableHeaderCell>Cost</TableHeaderCell>
                                    <TableHeaderCell>Lead Time</TableHeaderCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {vendors?.map((v, i) => (
                                    <TableRow key={i}>
                                        <TableCell>{v.name}</TableCell>
                                        <TableCell>${v.cost}</TableCell>
                                        <TableCell>{v.lead_time} days</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                 </Card>

                 {/* Stock & Sales Distribution */}
                 <Card>
                     <Title>Stock & Sales Distribution</Title>
                     <Text>Stock and sales channel breakdown.</Text>
                     <BarList
                         data={stockAndSalesData}
                         className="mt-4"
                         valueFormatter={valueFormatter}
                     />
                 </Card>
            </div>

            {/* Bottom Row: Analytics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* Coverage Gauge */}
                <Card className="flex flex-col items-center justify-center col-span-1">
                    <Title className="w-full text-left">Coverage</Title>
                    <div className="relative mt-4">
                        <DonutChart
                            data={[
                                { name: 'Coverage', value: analytics.coverage },
                                { name: 'Rest', value: Math.max(0, 6 - analytics.coverage) }
                            ]}
                            category="value"
                            index="name"
                            colors={["blue", "slate-100"]}
                            variant="donut"
                            className="h-32 w-32"
                            showLabel={false}
                        />
                         <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                            <Metric>{analytics.coverage}</Metric>
                            <Text className="text-xs">Months</Text>
                        </div>
                    </div>
                </Card>

                {/* Sales Trend */}
                <Card className="col-span-1 md:col-span-2 cursor-pointer hover:shadow-lg transition-shadow" onClick={() => navigate(`/forecast/${product.sku}`)}>
                    <div className="flex justify-between items-center">
                        <Title>Sales Trend</Title>
                        <Text className="text-xs text-indigo-600 flex items-center">Click for Analysis <ArrowRight className="h-3 w-3 ml-1"/></Text>
                    </div>
                    <LineChart
                        className="mt-4 h-40"
                        data={analytics.sales_trend}
                        index="date"
                        categories={["Actual Sales", "Forecast"]}
                        colors={["blue", "emerald"]}
                        valueFormatter={valueFormatter}
                        showLegend={false}
                        yAxisWidth={40}
                    />
                </Card>
            </div>

            {/* Order Table */}
            <Card>
                <Title>Purchase Orders</Title>
                <Table className="mt-4">
                    <TableHead>
                        <TableRow>
                            <TableHeaderCell>PO ID</TableHeaderCell>
                            <TableHeaderCell>Date</TableHeaderCell>
                            <TableHeaderCell>Quantity</TableHeaderCell>
                            <TableHeaderCell>Status</TableHeaderCell>
                            <TableHeaderCell>ETA</TableHeaderCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {orders.map((order) => (
                            <TableRow key={order.id}>
                                <TableCell>PO-{order.id}</TableCell>
                                <TableCell>{order.date}</TableCell>
                                <TableCell>{order.quantity}</TableCell>
                                <TableCell>
                                    <Badge color={order.status === 'Approved' ? 'emerald' : order.status === 'Pending' ? 'yellow' : 'red'}>
                                        {order.status}
                                    </Badge>
                                </TableCell>
                                <TableCell>{order.eta}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Card>

        </div>

        {/* Right Column (25% width on large screens) - Copilot */}
        <div className="col-span-1 lg:col-span-1 lg:h-full flex flex-col">
            <Card className="h-full flex flex-col lg:min-h-0 min-h-[500px]">
                <div className="flex items-center mb-4">
                    <div className="p-2 bg-indigo-100 rounded-lg mr-3">
                         <BrainCircuit className="h-6 w-6 text-indigo-600" />
                    </div>
                    <div>
                        <Title>Procurement Co-pilot</Title>
                        <Text className="text-xs">Analysis & Forecasting</Text>
                    </div>
                </div>

                <div className="flex-1 bg-slate-50 rounded-lg p-4 mb-4 overflow-y-auto">
                    <div className="text-center text-xs text-gray-400 mb-4">TODAY</div>
                    {chatHistory.map((msg, idx) => (
                        <div key={idx} className="flex mb-4">
                            <div className="bg-indigo-600 h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 mr-2">
                                <BrainCircuit className="h-4 w-4 text-white" />
                            </div>
                            <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-100 text-sm">
                                <p>{msg.text}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="relative">
                    <TextInput
                        icon={MessageCircle}
                        placeholder="Ask..."
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                    />
                    <div className="absolute right-1 top-1">
                         <button className="bg-indigo-600 p-1.5 rounded-md text-white hover:bg-indigo-700 transition-colors">
                             <Send className="h-4 w-4" />
                         </button>
                    </div>
                </div>
                <Flex className="mt-2 text-xs text-gray-400">
                    <Text>AI Copilot 1.0</Text>
                    <Text>Secure</Text>
                </Flex>
            </Card>
        </div>

      </div>

      {/* CREATE PO MODAL */}
      <Transition show={isPOModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsPOModalOpen(false)}>
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
                <DialogPanel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <div className="flex justify-between items-center mb-4">
                    <DialogTitle as="h3" className="text-lg font-medium leading-6 text-gray-900">
                      Create Purchase Order
                    </DialogTitle>
                    <button onClick={() => setIsPOModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                      <div>
                          <label className="block text-sm font-medium text-gray-700">Vendor</label>
                          <select
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                            value={poVendorId}
                            onChange={(e) => setPoVendorId(e.target.value)}
                          >
                              {vendors?.map(v => (
                                  <option key={v.id} value={v.id}>{v.name} (Lead Time: {v.lead_time} days)</option>
                              ))}
                          </select>
                      </div>

                      <div>
                          <label className="block text-sm font-medium text-gray-700">Quantity</label>
                          <input
                            type="number"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                            value={poQuantity}
                            onChange={(e) => setPoQuantity(e.target.value)}
                          />
                      </div>

                      {emailPreview && (
                          <div className="mt-4">
                              <label className="block text-sm font-medium text-gray-700 mb-1">Email Preview</label>
                              <div className="bg-gray-50 p-3 rounded-md border text-sm font-mono whitespace-pre-wrap text-gray-600">
                                  {emailPreview}
                              </div>
                          </div>
                      )}

                      <div className="mt-6 flex justify-between">
                          <Button
                            variant="secondary"
                            icon={Mail}
                            onClick={handleGenerateEmail}
                          >
                              Generate Email
                          </Button>

                          <div className="flex space-x-3">
                            <button
                                type="button"
                                onClick={() => setIsPOModalOpen(false)}
                                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={handleSubmitPO}
                                disabled={isSending}
                                className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none"
                            >
                                {isSending ? 'Sending...' : 'Send Request'}
                            </button>
                          </div>
                      </div>
                  </div>

                </DialogPanel>
              </TransitionChild>
            </div>
          </div>
        </Dialog>
      </Transition>

    </Layout>
  );
};

export default ProductDetail;
