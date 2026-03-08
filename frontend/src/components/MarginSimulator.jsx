import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Metric, Flex, Badge, Button, LineChart } from "@tremor/react";
import { BrainCircuit, DollarSign, Package, AlertCircle, MessageSquare } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-toastify';
import html2canvas from 'html2canvas';

const valueFormatter = (number) => `$ ${new Intl.NumberFormat("en-US").format(number).toString()}`;
const numberFormatter = (number) => `${new Intl.NumberFormat("en-US").format(number).toString()}`;

const MarginSimulator = () => {
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [loadingProducts, setLoadingProducts] = useState(true);

    const [proposedPrice, setProposedPrice] = useState(100);
    const [volumeDiscount, setVolumeDiscount] = useState(0);

    const [simulating, setSimulating] = useState(false);
    const [simulationData, setSimulationData] = useState(null);

    const [chatPrompt, setChatPrompt] = useState('');
    const [chatResponse, setChatResponse] = useState('');
    const [isChatting, setIsChatting] = useState(false);

    // We can assume a base cost of 50 for the sake of the simulation UI if not provided
    const baseCost = 50;

    useEffect(() => {
        // Fetch products for sidebar
        const fetchProducts = async () => {
            try {
                // Borrowing the forecast/products endpoint since it gets available products
                const response = await axios.get('/api/forecast/products?location_id=ALL');
                setProducts(response.data);
                if (response.data.length > 0) {
                    const firstProduct = response.data[0];
                    setSelectedProduct(firstProduct);
                    if (firstProduct.price) {
                        setProposedPrice(firstProduct.price);
                    }
                }
            } catch (err) {
                console.error("Error fetching products", err);
                toast.error("Failed to load products");
            } finally {
                setLoadingProducts(false);
            }
        };
        fetchProducts();
    }, []);

    const runSimulation = async () => {
        if (!selectedProduct) return;

        setSimulating(true);
        setSimulationData(null);

        try {
            const response = await axios.post('/api/margin-simulator/forecast', {
                product_id: selectedProduct.id,
                proposed_price: proposedPrice,
                volume_discount: volumeDiscount
            });

            const data = response.data;

            // Transform data for chart
            const chartData = [];

            // Add actuals (last 12 weeks for cleaner view)
            const recentActuals = data.actuals.slice(-12);
            recentActuals.forEach(a => {
                chartData.push({
                    date: a.date,
                    'Historical Quantity': a.quantity,
                    'Historical Price': a.price,
                    'Historical Subtotal (k)': a.subtotal / 1000,
                    'Forecasted Quantity': null,
                    'Forecasted Price': null,
                    'Forecasted Subtotal (k)': null
                });
            });

            // Tie the last actual to the first forecast for continuity
            if (recentActuals.length > 0 && data.forecast.length > 0) {
                 const lastActual = recentActuals[recentActuals.length - 1];
                 chartData[chartData.length - 1]['Forecasted Quantity'] = lastActual.quantity;
                 chartData[chartData.length - 1]['Forecasted Price'] = lastActual.price;
                 chartData[chartData.length - 1]['Forecasted Subtotal (k)'] = lastActual.subtotal / 1000;
            }

            // Add forecasts
            data.forecast.forEach(f => {
                chartData.push({
                    date: f.date,
                    'Historical Quantity': null,
                    'Historical Price': null,
                    'Historical Subtotal (k)': null,
                    'Forecasted Quantity': f.quantity,
                    'Forecasted Price': f.price,
                    'Forecasted Subtotal (k)': f.subtotal / 1000
                });
            });

            setSimulationData({
                chartData,
                totalVolume: data.total_predicted_volume,
                finalPrice: data.proposed_price
            });

            toast.success("Simulation complete!");

        } catch (err) {
            console.error("Simulation error", err);
            toast.error(err.response?.data?.message || "Failed to run simulation");
        } finally {
            setSimulating(false);
        }
    };

    const handleChat = async () => {
        if (!chatPrompt || !simulationData) return;

        setIsChatting(true);
        setChatResponse('');

        try {
            // Capture chart image
            const chartElement = document.getElementById('simulation-chart-container');
            if (!chartElement) throw new Error("Chart element not found");

            const canvas = await html2canvas(chartElement);
            const imageBase64 = canvas.toDataURL("image/png");

            // Send to agent
            const res = await axios.post('/api/margin-simulator/chat', {
                prompt: chatPrompt,
                image_base64: imageBase64
            });

            setChatResponse(res.data.rationale);

        } catch (err) {
            console.error("Chat error", err);
            toast.error(err.response?.data?.message || "Failed to process question");
        } finally {
            setIsChatting(false);
        }
    };

    return (
        <Layout>
            <div className="flex flex-col md:flex-row gap-6">
                {/* Sidebar */}
                <Card className="w-full md:w-1/4 flex-shrink-0 self-start sticky top-6">
                    <Title className="mb-4">Select Product</Title>
                    {loadingProducts ? (
                        <div className="text-center py-4 text-gray-500">Loading products...</div>
                    ) : (
                        <div className="space-y-2">
                            {products.map(product => (
                                <div
                                    key={product.id}
                                    onClick={() => {
                                        setSelectedProduct(product);
                                        setSimulationData(null);
                                        setChatResponse('');
                                        setChatPrompt('');
                                        setProposedPrice(product.price || 100);
                                        setVolumeDiscount(0);
                                    }}
                                    className={`p-3 rounded-lg cursor-pointer border transition-colors ${selectedProduct?.id === product.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:bg-gray-50'}`}
                                >
                                    <div className="font-medium text-gray-900">{product.product_name}</div>
                                    <div className="text-xs text-gray-500">{product.sku_id}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>

                {/* Main Content */}
                <div className="w-full md:w-3/4 flex flex-col gap-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <Title>Margin Simulator {selectedProduct && `- ${selectedProduct.product_name}`}</Title>
                            <Text>Simulate pricing scenarios and analyze impact on forecasted volume and margin.</Text>
                        </div>
                        <Badge color="blue" icon={BrainCircuit}>AI Powered</Badge>
                    </div>

                    {/* Control Panel & Results */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Simulation Controls */}
                        <Card>
                            <Title className="mb-4">Dynamic Inputs</Title>
                            <div className="space-y-6">
                                <div>
                                    <Flex className="mb-2">
                                        <Text>Current Price</Text>
                                        <Text className="font-bold text-gray-500">{selectedProduct ? valueFormatter(selectedProduct.price) : '-'}</Text>
                                    </Flex>
                                    <Flex className="mb-2 mt-4">
                                        <Text>Proposed Price</Text>
                                        <Text className="font-bold">{valueFormatter(proposedPrice)}</Text>
                                    </Flex>
                                    <input
                                        type="range"
                                        min="10"
                                        max={selectedProduct ? Math.max(500, selectedProduct.price * 2) : 500}
                                        step="1"
                                        value={proposedPrice}
                                        onChange={(e) => setProposedPrice(Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                    />
                                </div>

                                <div>
                                    <Flex className="mb-2">
                                        <Text>Volume Discount %</Text>
                                        <Text className="font-bold">{volumeDiscount}%</Text>
                                    </Flex>
                                    <input
                                        type="range"
                                        min="0"
                                        max="50"
                                        step="1"
                                        value={volumeDiscount}
                                        onChange={(e) => setVolumeDiscount(Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                    />
                                </div>

                                <Button
                                    className="w-full"
                                    onClick={runSimulation}
                                    loading={simulating}
                                >
                                    Run Simulation
                                </Button>
                            </div>
                        </Card>

                        {/* Simulation Results (Goldilocks Area approximation) */}
                        <Card decoration="top" decorationColor={simulationData ? "emerald" : "gray"}>
                            <Title className="mb-4">Simulation Results (4-Week Projection)</Title>
                            {simulationData ? (
                                <div className="space-y-4">
                                    <Flex className="items-center border-b pb-2">
                                        <Text>Final Target Price</Text>
                                        <Metric className="text-lg">{valueFormatter(simulationData.finalPrice)}</Metric>
                                    </Flex>
                                    <Flex className="items-center border-b pb-2">
                                        <Text>Forecasted Volume</Text>
                                        <Metric className="text-lg">{numberFormatter(simulationData.totalVolume)} units</Metric>
                                    </Flex>
                                    <Flex className="items-center pt-2">
                                        <Text>Total Predicted Profit <br/><span className="text-xs text-gray-400">(assuming ${baseCost} base cost)</span></Text>
                                        <Metric className="text-emerald-600">
                                            {valueFormatter((simulationData.finalPrice - baseCost) * simulationData.totalVolume)}
                                        </Metric>
                                    </Flex>
                                </div>
                            ) : (
                                <div className="h-32 flex flex-col items-center justify-center text-gray-400">
                                    <AlertCircle className="h-8 w-8 mb-2" />
                                    <Text>Run simulation to see results.</Text>
                                </div>
                            )}
                        </Card>
                    </div>

                    {/* Charts */}
                    <Card className="flex-1">
                        <div id="simulation-chart-container" className="p-4 bg-white rounded-lg flex flex-col gap-6">
                            <div>
                                <Title>Demand Volume Projection</Title>
                                <Text>Historical actuals vs simulated forecast based on your price inputs.</Text>
                            </div>

                            {simulating ? (
                                 <div className="h-72 flex items-center justify-center">
                                     <Text className="text-indigo-500 animate-pulse">Running AI Simulation...</Text>
                                 </div>
                            ) : simulationData ? (
                                <>
                                    <div>
                                        <Text className="font-semibold mb-2">Subtotal (k)</Text>
                                        <LineChart
                                            className="h-72"
                                            data={simulationData.chartData}
                                            index="date"
                                            categories={[
                                                "Historical Subtotal (k)", "Forecasted Subtotal (k)"
                                            ]}
                                            colors={["blue", "blue-500"]}
                                            valueFormatter={numberFormatter}
                                            yAxisWidth={60}
                                        />
                                    </div>
                                    <div className="border-t pt-4">
                                        <Text className="font-semibold mb-2">Quantity</Text>
                                        <LineChart
                                            className="h-72"
                                            data={simulationData.chartData}
                                            index="date"
                                            categories={[
                                                "Historical Quantity", "Forecasted Quantity"
                                            ]}
                                            colors={["emerald", "emerald-500"]}
                                            valueFormatter={numberFormatter}
                                            yAxisWidth={60}
                                        />
                                    </div>
                                    <div className="border-t pt-4">
                                        <Text className="font-semibold mb-2">Price</Text>
                                        <LineChart
                                            className="h-72"
                                            data={simulationData.chartData}
                                            index="date"
                                            categories={[
                                                "Historical Price", "Forecasted Price"
                                            ]}
                                            colors={["amber", "amber-500"]}
                                            valueFormatter={numberFormatter}
                                            yAxisWidth={60}
                                        />
                                    </div>
                                </>
                            ) : (
                                <div className="h-72 flex items-center justify-center text-gray-400">
                                    <Text>Waiting for simulation.</Text>
                                </div>
                            )}
                        </div>
                    </Card>

                    {/* Agentic Smart Why Chat */}
                    {simulationData && (
                        <Card>
                            <Title className="flex items-center gap-2 mb-4">
                                <MessageSquare className="h-5 w-5 text-indigo-500" />
                                Smart Why Analysis
                            </Title>
                            <Text className="mb-4">Ask the AI Pricing Strategist to interpret the simulation results.</Text>

                            <div className="flex gap-2 mb-4">
                                <input
                                    type="text"
                                    className="flex-1 border rounded-md p-2"
                                    placeholder="E.g., Does this proposed price clear stock efficiently without hurting margin?"
                                    value={chatPrompt}
                                    onChange={(e) => setChatPrompt(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                                />
                                <Button onClick={handleChat} loading={isChatting} icon={BrainCircuit}>Ask AI</Button>
                            </div>

                            {chatResponse && (
                                <div className="mt-4 p-4 bg-indigo-50 rounded-md border border-indigo-100">
                                    <Text className="text-gray-900 leading-relaxed whitespace-pre-wrap">
                                        {chatResponse}
                                    </Text>
                                </div>
                            )}
                        </Card>
                    )}
                </div>
            </div>
        </Layout>
    );
};

export default MarginSimulator;
