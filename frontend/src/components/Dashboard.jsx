import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, LineChart, Metric, Flex, Badge, Button, Callout } from "@tremor/react";
import { Link } from 'react-router-dom';
import { ArrowRight, TrendingUp, AlertCircle, ShoppingCart, DollarSign, BrainCircuit } from 'lucide-react';
import axios from 'axios';

const valueFormatter = (number) => `$ ${new Intl.NumberFormat("us").format(number).toString()}`;
const numberFormatter = (number) => `${new Intl.NumberFormat("us").format(number).toString()}`;

const Dashboard = () => {
  const role = localStorage.getItem('userRole') || 'Staff';

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [margin, setMargin] = useState(20); // Default 20% margin
  const [basePrice, setBasePrice] = useState(100);
  const [simulatedProfit, setSimulatedProfit] = useState(0);

  // Mock data for initial render or fallback
  const mockChartData = [
    { date: "Jan", "Actual Sales": 4500, "AI Prediction": 4600 },
    { date: "Feb", "Actual Sales": 5200, "AI Prediction": 5100 },
    { date: "Mar", "Actual Sales": 4800, "AI Prediction": 4900 },
    { date: "Apr", "Actual Sales": 6100, "AI Prediction": 5900 },
    { date: "May", "Actual Sales": 5500, "AI Prediction": 5800 },
    { date: "Jun", "Actual Sales": 6700, "AI Prediction": 6500 },
  ];

  useEffect(() => {
    // Fetch data from API
    const fetchData = async () => {
        try {
            const response = await axios.get('/api/dashboard');
            setData(response.data);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching dashboard data", error);
            setLoading(false);
        }
    };

    fetchData();
  }, []);

  useEffect(() => {
    // Update simulated profit based on margin slider
    // Profit = Price * Margin %
    const price = basePrice * (1 + (margin / 100));
    setSimulatedProfit(price - basePrice);
  }, [margin, basePrice]);

  const handleGeneratePR = async () => {
      try {
          // Ask user for a user location id for now
          const ulId = prompt("Enter your User Location ID (ul_id):", "1");
          if (!ulId) return;

          alert("Generating Purchase Request...");
          await axios.post('/api/generate-pr', { sku_id: 'HT-PLATZ-450-H', quantity: 100, ul_id: parseInt(ulId, 10) });
          alert("Purchase Request Generated Successfully! PDF sent to email.");
      } catch (e) {
          console.error(e);
          alert("Error generating PR: " + (e.response?.data?.message || e.message));
      }
  };

  if (loading) {
      return <div className="p-10 text-center">Loading Dashboard...</div>;
  }

  return (
    <Layout>
      <div className="space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center">
            <div>
                <Title>Procurement & Pricing Intelligence</Title>
                <Text>AI-Driven Insights for Inventory Optimization</Text>
            </div>
            <div className="flex space-x-2">
                 <Badge color="blue" icon={BrainCircuit}>AI Active</Badge>
            </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card decoration="top" decorationColor="blue">
                <Flex justifyContent="start" className="space-x-4">
                    <div className="p-2 bg-blue-100 rounded-full">
                        <DollarSign className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                        <Text>Total Historical Sales</Text>
                        <Metric>{valueFormatter(data?.totalSales)}</Metric>
                    </div>
                </Flex>
            </Card>
            <Card decoration="top" decorationColor="emerald">
                <Flex justifyContent="start" className="space-x-4">
                    <div className="p-2 bg-emerald-100 rounded-full">
                        <TrendingUp className="h-6 w-6 text-emerald-600" />
                    </div>
                    <div>
                        <Text>Predicted Demand (Q3)</Text>
                        <Metric>{numberFormatter(data?.predictedDemand)}</Metric>
                    </div>
                </Flex>
            </Card>
            <Card decoration="top" decorationColor="orange">
                <Flex justifyContent="start" className="space-x-4">
                    <div className="p-2 bg-orange-100 rounded-full">
                        <AlertCircle className="h-6 w-6 text-orange-600" />
                    </div>
                    <div>
                        <Text>Forecast Accuracy</Text>
                        <Metric>{data?.accuracy}</Metric>
                    </div>
                </Flex>
            </Card>
        </div>

        {/* Main Chart */}
        <Card>
            <div className="flex justify-between items-center">
                <div>
                    <Title>Historical Sales vs. AI Predictions</Title>
                    <Text>Comparison of actual sales performance against AI forecasting models.</Text>
                </div>
                <Link to="/forecast">
                    <Button size="xs" variant="secondary" icon={TrendingUp}>Go to Forecast</Button>
                </Link>
            </div>
            <LineChart
                className="mt-6 h-72"
                data={data?.chartData}
                index="date"
                categories={["Actual Sales", "AI Prediction"]}
                colors={["blue", "emerald"]}
                valueFormatter={valueFormatter}
                yAxisWidth={60}
            />
        </Card>

        {/* Intelligence & Simulation Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Smart Why Rationale */}
            <Card>
                <Title className="mb-4 flex items-center">
                    <BrainCircuit className="h-5 w-5 mr-2 text-indigo-500"/>
                    Smart Why Logic
                </Title>
                <Callout
                    title="AI Reasoning"
                    icon={BrainCircuit}
                    color="indigo"
                    className="mb-4"
                >
                    {data?.smartWhy}
                </Callout>
                <Text className="mt-4">
                    The reasoning model analyzes market trends, seasonality, and competitor data to provide this explanation.
                </Text>
            </Card>

            {/* Margin Simulator */}
            <Card>
                <Title className="mb-4">Margin Simulator</Title>
                <Text>Test how price changes impact simulated profit per unit.</Text>

                <div className="mt-6 space-y-4">
                    <Flex>
                        <Text>Target Margin</Text>
                        <Text>{margin}%</Text>
                    </Flex>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={margin}
                        onChange={(e) => setMargin(Number(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />

                    <div className="bg-gray-50 p-4 rounded-md border border-gray-100 mt-4">
                        <Flex className="mb-2">
                            <Text>Base Cost</Text>
                            <Text>{valueFormatter(basePrice)}</Text>
                        </Flex>
                        <Flex className="mb-2">
                            <Text>Simulated Price</Text>
                            <Text className="font-bold text-gray-900">{valueFormatter(basePrice * (1 + margin/100))}</Text>
                        </Flex>
                         <div className="border-t border-gray-200 my-2 pt-2">
                            <Flex>
                                <Text>Projected Profit / Unit</Text>
                                <Metric className="text-emerald-600">{valueFormatter(basePrice * (margin/100))}</Metric>
                            </Flex>
                         </div>
                    </div>
                </div>
            </Card>
        </div>

        {/* Action Bar - Restricted to Warehouse */}
        {role === 'Warehouse' && (
            <Card decoration="left" decorationColor="blue">
                <Flex>
                    <div>
                        <Title>Automated Purchase Request</Title>
                        <Text>Generate a PR based on the current AI recommendation.</Text>
                    </div>
                    <Button
                        icon={ShoppingCart}
                        size="lg"
                        onClick={handleGeneratePR}
                        color="blue"
                    >
                        Generate PR
                    </Button>
                </Flex>
            </Card>
        )}

      </div>
    </Layout>
  );
};

export default Dashboard;
