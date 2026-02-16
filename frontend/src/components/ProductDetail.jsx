import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
  Package
} from 'lucide-react';
import axios from 'axios';

const valueFormatter = (number) => `${new Intl.NumberFormat("us").format(number).toString()}`;

const ProductDetail = () => {
  const { sku } = useParams();
  const [productData, setProductData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatMessage, setChatMessage] = useState('');

  useEffect(() => {
    const fetchProductDetail = async () => {
      try {
        const response = await axios.get(`/api/inventory/products/${sku}`);
        setProductData(response.data);
        setLoading(false);
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

  const { product, stock_health, velocity, incoming, analytics, orders } = productData;

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
    <Layout>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

        {/* Left Column (75% width on large screens) */}
        <div className="col-span-1 lg:col-span-3 space-y-6">

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
                        <Button icon={ShoppingCart} size="lg" color="blue">
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

            {/* Bottom Row: Analytics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* Coverage Gauge */}
                <Card className="flex flex-col items-center justify-center">
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

                {/* Distribution */}
                <Card>
                    <Title>Distribution</Title>
                    <Text>Sales Channel Breakdown</Text>
                    <BarList
                        data={analytics.distribution}
                        className="mt-4"
                        color="blue"
                    />
                </Card>

                {/* Sales Trend */}
                <Card>
                    <Title>Sales Trend</Title>
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
        <div className="col-span-1 lg:col-span-1">
            <Card className="h-full flex flex-col min-h-[600px]">
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
    </Layout>
  );
};

export default ProductDetail;
