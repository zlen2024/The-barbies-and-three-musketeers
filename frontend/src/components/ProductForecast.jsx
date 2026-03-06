import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Layout from './Layout';
import { Card, Title, Text, Button, Select, SelectItem, TextInput, Textarea, Metric, Callout } from "@tremor/react";
import { Search, Loader2, TrendingUp, TrendingDown, AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import axios from 'axios';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush
} from 'recharts';

const ProductForecast = () => {
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('ALL');
  const [selectedProduct, setSelectedProduct] = useState('ALL');

  const [locationSearchTerm, setLocationSearchTerm] = useState('');
  const [productSearchTerm, setProductSearchTerm] = useState('');

  const [chartData, setChartData] = useState([]);
  const [kpi, setKpi] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [timeInterval, setTimeInterval] = useState('daily');

  // Projection controls state
  const [sampleSize, setSampleSize] = useState('30');
  const [projectionSize, setProjectionSize] = useState('1');
  const [analysisPrompt, setAnalysisPrompt] = useState('');
  const [visibleMAs, setVisibleMAs] = useState({
      MA3: true,
      MA7: false,
      MA14: false
  });

  const locationSearch = useLocation();
  const navigate = useNavigate();

  // Parse URL params initially
  useEffect(() => {
    const params = new URLSearchParams(locationSearch.search);
    const locId = params.get('location');
    const sku = params.get('sku');

    if (locId) setSelectedLocation(locId);
    if (sku) setSelectedProduct(sku);
  }, [locationSearch.search]);

  // Fetch Locations
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const res = await axios.get('/api/forecast/locations');
        setLocations(res.data);
      } catch (err) {
        console.error("Failed to load locations", err);
      }
    };
    fetchLocations();
  }, []);

  // Fetch Products when location changes
  useEffect(() => {
    if (!selectedLocation) {
        setProducts([]);
        return;
    }
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`/api/forecast/products?location_id=${selectedLocation}`);
        setProducts(res.data);
      } catch (err) {
        console.error("Failed to load products", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, [selectedLocation]);

  // Fetch Forecast Data when location, product, or interval change
  useEffect(() => {
      if (!selectedLocation || !selectedProduct) {
          setChartData([]);
          setKpi(null);
          setAlerts([]);
          return;
      }
      const fetchData = async () => {
          setDataLoading(true);
          try {
              const res = await axios.get(`/api/forecast/data?location_id=${selectedLocation}&product_id=${selectedProduct}&interval=${timeInterval}`);
              // API now returns { chartData, kpi, alerts }
              if (res.data.chartData) {
                  setChartData(res.data.chartData);
                  setKpi(res.data.kpi || {});
                  setAlerts(res.data.alerts || []);
              } else if (Array.isArray(res.data)) {
                  // Fallback if old format returns
                  setChartData(res.data);
                  setKpi(null);
                  setAlerts([]);
              } else {
                  setChartData([]);
                  setKpi(null);
                  setAlerts([]);
              }

              // Update URL to reflect current selection
              navigate(`/forecast?location=${selectedLocation}&sku=${selectedProduct}`, { replace: true });
          } catch (err) {
              console.error("Failed to load forecast data", err);
          } finally {
              setDataLoading(false);
          }
      };
      fetchData();
  }, [selectedLocation, selectedProduct, timeInterval, navigate]);

  const filteredLocations = locations.filter(loc =>
      (loc.description || '').toLowerCase().includes(locationSearchTerm.toLowerCase()) ||
      (loc.loc_code || '').toLowerCase().includes(locationSearchTerm.toLowerCase())
  );

  const filteredProducts = products.filter(prod =>
      (prod.product_name || '').toLowerCase().includes(productSearchTerm.toLowerCase()) ||
      (prod.sku_id || '').toLowerCase().includes(productSearchTerm.toLowerCase())
  );

  const toggleMA = (ma) => {
      setVisibleMAs(prev => ({...prev, [ma]: !prev[ma]}));
  };

  const handleProject = () => {
      alert(`Projecting forecast using:\nSample Size: ${sampleSize} days\nProjection: ${projectionSize} month(s)\nPrompt: ${analysisPrompt}`);
  };

  // Helper to render KPI value and handle nulls
  const renderValue = (value, isPercent = false) => {
      if (value === null || value === undefined) return 'N/A';
      return isPercent ? `${(value * 100).toFixed(1)}%` : value;
  };

  return (
    <Layout isFixed={true} isDark={true}>
      <div className="flex h-[calc(100vh-64px)] overflow-hidden">

        {/* Left Sidebar - Markets / Products */}
        <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col flex-none">
            {/* Locations Section */}
            <div className="p-4 border-b border-gray-800 flex-1 overflow-y-auto">
                <h2 className="text-gray-400 text-xs font-semibold mb-3 uppercase tracking-wider">Markets (Locations)</h2>

                <div className="relative mb-4">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search locations..."
                        className="w-full bg-gray-800 border-gray-700 text-sm text-gray-200 rounded-md pl-9 pr-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                        value={locationSearchTerm}
                        onChange={(e) => setLocationSearchTerm(e.target.value)}
                    />
                </div>

                <div className="space-y-1">
                    <div
                        onClick={() => setSelectedLocation('ALL')}
                        className={`p-2 rounded cursor-pointer text-sm flex items-center justify-between ${selectedLocation === 'ALL' ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
                    >
                        <span>All Assigned Locations</span>
                    </div>
                    {filteredLocations.map(loc => (
                        <div
                            key={loc.id}
                            onClick={() => { setSelectedLocation(loc.id.toString()); }}
                            className={`p-2 rounded cursor-pointer text-sm flex items-center justify-between ${selectedLocation === loc.id.toString() ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
                        >
                            <span>{loc.description}</span>
                            <span className="text-xs opacity-50">{loc.loc_code}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Products Section */}
            <div className="p-4 flex-1 overflow-y-auto border-t border-gray-800">
                <h2 className="text-gray-400 text-xs font-semibold mb-3 uppercase tracking-wider">Products</h2>

                <div className="relative mb-4">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search products..."
                        className="w-full bg-gray-800 border-gray-700 text-sm text-gray-200 rounded-md pl-9 pr-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                        value={productSearchTerm}
                        onChange={(e) => setProductSearchTerm(e.target.value)}
                    />
                </div>

                {loading ? (
                    <div className="flex items-center justify-center p-4"><Loader2 className="animate-spin text-indigo-500 h-6 w-6" /></div>
                ) : products.length === 0 ? (
                    <div className="text-gray-500 text-sm text-center mt-4">
                        {selectedLocation ? "No products found for this location." : "Select a location first."}
                    </div>
                ) : (
                    <div className="space-y-1">
                        <div className="grid grid-cols-12 gap-2 px-2 pb-2 text-xs text-gray-500 font-semibold border-b border-gray-800">
                            <div className="col-span-8">Product</div>
                            <div className="col-span-4 text-right">SKU</div>
                        </div>
                        <div
                            onClick={() => setSelectedProduct('ALL')}
                            className={`grid grid-cols-12 gap-2 p-2 rounded cursor-pointer text-sm items-center ${selectedProduct === 'ALL' ? 'bg-gray-800 border-l-2 border-indigo-500 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
                        >
                            <div className="col-span-8 truncate font-medium">All Products</div>
                            <div className="col-span-4 text-right text-xs opacity-75">--</div>
                        </div>
                        {filteredProducts.map(prod => (
                            <div
                                key={prod.id}
                                onClick={() => setSelectedProduct(prod.id.toString())}
                                className={`grid grid-cols-12 gap-2 p-2 rounded cursor-pointer text-sm items-center ${selectedProduct === prod.id.toString() ? 'bg-gray-800 border-l-2 border-indigo-500 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
                            >
                                <div className="col-span-8 truncate font-medium">{prod.product_name}</div>
                                <div className="col-span-4 text-right text-xs opacity-75">{prod.sku_id}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>

        {/* Main Content Area - Charts and Controls */}
        <div className="flex-1 bg-gray-950 flex flex-col overflow-y-auto relative">

            {/* Header / Info Bar */}
            <div className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 flex-none">
                <div className="flex items-center space-x-6">
                    <div>
                        <span className="text-gray-400 text-xs uppercase tracking-wider">Selected Location</span>
                        <div className="text-white font-bold text-lg">
                            {selectedLocation === 'ALL' ? 'All Assigned Locations' : (locations.find(l => l.id.toString() === selectedLocation)?.description || 'Loading...')}
                        </div>
                    </div>
                    <div className="h-8 w-px bg-gray-700"></div>
                    <div>
                        <span className="text-gray-400 text-xs uppercase tracking-wider">Selected Product</span>
                        <div className="text-white font-bold text-lg">
                            {selectedProduct === 'ALL' ? 'All Products' : (products.find(p => p.id.toString() === selectedProduct)?.product_name || 'Loading...')}
                        </div>
                    </div>
                    {selectedProduct !== 'ALL' && (
                        <>
                            <div className="h-8 w-px bg-gray-700"></div>
                            <div>
                                <span className="text-gray-400 text-xs uppercase tracking-wider">SKU</span>
                                <div className="text-gray-300">
                                    {products.find(p => p.id.toString() === selectedProduct)?.sku_id || '--'}
                                </div>
                            </div>
                        </>
                    )}
                </div>
                <div className="flex items-center">
                    <span className="text-gray-400 text-xs uppercase tracking-wider mr-3">Time Interval</span>
                    <Select value={timeInterval} onValueChange={setTimeInterval} className="w-36 dark-theme-select text-sm">
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="biweekly">Bi-weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                    </Select>
                </div>
            </div>

            <div className="p-6 flex flex-col min-h-0 space-y-6 flex-1">
                {dataLoading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <Loader2 className="animate-spin text-indigo-500 h-8 w-8" />
                    </div>
                ) : chartData.length > 0 ? (
                    <>
                        {/* KPI Cards Row */}
                        {kpi && Object.keys(kpi).length > 0 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <Card decoration="top" decorationColor="indigo" className="bg-gray-900 border-gray-800">
                                    <Text className="text-gray-400 uppercase text-xs font-semibold mb-1 tracking-wider">Demand Momentum</Text>
                                    <Metric className="text-white font-bold">{renderValue(kpi.DemandMomentum, true)}</Metric>
                                    <div className="mt-2 text-sm text-gray-500">Growth: {renderValue(kpi.GrowthRate, true)}</div>
                                </Card>

                                <Card decoration="top" decorationColor={kpi.TrendLogic === 'Uptrend' ? 'emerald' : kpi.TrendLogic === 'Downtrend' ? 'rose' : 'gray'} className="bg-gray-900 border-gray-800">
                                    <Text className="text-gray-400 uppercase text-xs font-semibold mb-1 tracking-wider">Trend & Volatility</Text>
                                    <div className="flex items-center">
                                        {kpi.TrendLogic === 'Uptrend' && <TrendingUp className="h-6 w-6 text-emerald-500 mr-2" />}
                                        {kpi.TrendLogic === 'Downtrend' && <TrendingDown className="h-6 w-6 text-rose-500 mr-2" />}
                                        <Metric className="text-white font-bold">{kpi.TrendLogic}</Metric>
                                    </div>
                                    <div className="mt-2 text-sm text-gray-500">Volatility: {renderValue(kpi.Volatility)} | Range: {renderValue(kpi.Range)}</div>
                                </Card>

                                <Card decoration="top" decorationColor="amber" className="bg-gray-900 border-gray-800">
                                    <Text className="text-gray-400 uppercase text-xs font-semibold mb-1 tracking-wider">Inventory Health</Text>
                                    <Metric className="text-white font-bold">{renderValue(kpi.StockCoverage)} <span className="text-sm font-normal text-gray-500">periods</span></Metric>
                                    <div className="mt-2 text-sm text-gray-500">Stock: {renderValue(kpi.CurrentStock)} | MA7: {renderValue(kpi.MA7)}</div>
                                </Card>

                                <Card decoration="top" decorationColor="blue" className="bg-gray-900 border-gray-800">
                                    <Text className="text-gray-400 uppercase text-xs font-semibold mb-1 tracking-wider">Volume (Last 7 Periods)</Text>
                                    <Metric className="text-white font-bold">{renderValue(kpi.RollingSum7)}</Metric>
                                    <div className="mt-2 text-sm text-gray-500">Net Demand: {renderValue(kpi.NetDemand)}</div>
                                </Card>
                            </div>
                        )}

                        {/* Chart Area */}
                        <Card className="bg-gray-900 border-gray-800 shrink-0 h-[500px] flex flex-col">
                            <div className="flex justify-between items-center mb-4 flex-none">
                                <Title className="text-gray-200">Sales Volume & Moving Averages</Title>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => toggleMA('MA3')}
                                        className={`px-3 py-1 text-xs rounded-full border ${visibleMAs.MA3 ? 'bg-indigo-900/50 border-indigo-500 text-indigo-400' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
                                    >
                                        MA3
                                    </button>
                                    <button
                                        onClick={() => toggleMA('MA7')}
                                        className={`px-3 py-1 text-xs rounded-full border ${visibleMAs.MA7 ? 'bg-emerald-900/50 border-emerald-500 text-emerald-400' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
                                    >
                                        MA7
                                    </button>
                                    <button
                                        onClick={() => toggleMA('MA14')}
                                        className={`px-3 py-1 text-xs rounded-full border ${visibleMAs.MA14 ? 'bg-amber-900/50 border-amber-500 text-amber-400' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
                                    >
                                        MA14
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 min-h-0 w-full relative">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart
                                        data={chartData}
                                        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                        <XAxis
                                            dataKey="date"
                                            stroke="#94a3b8"
                                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                                            tickMargin={10}
                                            minTickGap={30}
                                        />
                                        <YAxis
                                            yAxisId="left"
                                            stroke="#94a3b8"
                                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                                        />
                                        <YAxis
                                            yAxisId="right"
                                            orientation="right"
                                            stroke="#94a3b8"
                                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                                            hide // Hide right axis, scale lines together
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                            itemStyle={{ color: '#f8fafc' }}
                                        />
                                        <Legend wrapperStyle={{ paddingTop: '20px' }}/>

                                        {/* Volume Bars */}
                                        <Bar yAxisId="left" dataKey="volume" name={`${timeInterval.charAt(0).toUpperCase() + timeInterval.slice(1)} Sales`} fill="#3b82f6" opacity={0.3} barSize={20} />

                                        {/* MA Lines */}
                                        {visibleMAs.MA3 && <Line yAxisId="left" type="monotone" dataKey="MA3" stroke="#818cf8" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />}
                                        {visibleMAs.MA7 && <Line yAxisId="left" type="monotone" dataKey="MA7" stroke="#34d399" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />}
                                        {visibleMAs.MA14 && <Line yAxisId="left" type="monotone" dataKey="MA14" stroke="#fbbf24" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />}

                                        {/* Brush for zooming/resizing X-axis */}
                                        <Brush
                                            dataKey="date"
                                            height={30}
                                            stroke="#475569"
                                            fill="#0f172a"
                                            travellerWidth={10}
                                        />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        </Card>

                        {/* Alerts Section */}
                        {alerts && alerts.length > 0 && (
                            <div className="space-y-4">
                                <Title className="text-gray-200">Smart Alerts</Title>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {alerts.map((alert, idx) => {
                                        let icon = <Info className="h-5 w-5 text-blue-500" />;
                                        let color = "blue";
                                        if (alert.type === 'error') {
                                            icon = <AlertTriangle className="h-5 w-5 text-rose-500" />;
                                            color = "rose";
                                        } else if (alert.type === 'warning') {
                                            icon = <AlertCircle className="h-5 w-5 text-amber-500" />;
                                            color = "amber";
                                        } else if (alert.type === 'success') {
                                            icon = <CheckCircle className="h-5 w-5 text-emerald-500" />;
                                            color = "emerald";
                                        }

                                        return (
                                            <Callout
                                                key={idx}
                                                title={alert.message}
                                                icon={() => icon}
                                                color={color}
                                                className="bg-gray-900 border-gray-800 text-gray-300"
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {alerts && alerts.length === 0 && (
                            <div className="space-y-4">
                                <Title className="text-gray-200">Smart Alerts</Title>
                                <Callout
                                    title="No alerts triggered for the current period."
                                    icon={() => <CheckCircle className="h-5 w-5 text-emerald-500" />}
                                    color="emerald"
                                    className="bg-gray-900 border-gray-800 text-gray-300"
                                />
                            </div>
                        )}

                        {/* Bottom Control Panel for AI Projection */}
                        <div className="bg-gray-900 border border-gray-800 p-6 flex-none rounded-lg">
                            <div className="max-w-4xl">
                                <h3 className="text-gray-300 font-medium mb-4 flex items-center">
                                    <span className="bg-indigo-500/20 text-indigo-400 p-1 rounded mr-2">
                                        <Search className="h-4 w-4" />
                                    </span>
                                    AI Forecast Projection
                                </h3>

                                <div className="grid grid-cols-12 gap-6">
                                    <div className="col-span-4 space-y-4">
                                        <div>
                                            <label className="block text-xs font-medium text-gray-400 mb-1">Sample Size (Historical Data)</label>
                                            <Select value={sampleSize} onValueChange={setSampleSize} className="dark-theme-select">
                                                <SelectItem value="10">Last 10 Days</SelectItem>
                                                <SelectItem value="30">Last 30 Days</SelectItem>
                                                <SelectItem value="60">Last 60 Days</SelectItem>
                                            </Select>
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-400 mb-1">Projection Horizon</label>
                                            <Select value={projectionSize} onValueChange={setProjectionSize} className="dark-theme-select">
                                                <SelectItem value="1">1 Month</SelectItem>
                                                <SelectItem value="2">2 Months</SelectItem>
                                            </Select>
                                        </div>
                                    </div>

                                    <div className="col-span-8 flex flex-col">
                                        <label className="block text-xs font-medium text-gray-400 mb-1">Fundamental Analysis Prompt</label>
                                        <Textarea
                                            placeholder="Enter context for the reasoning model (e.g., 'Upcoming marketing campaign next week', 'Holiday season approaching', 'Competitor stockout')..."
                                            className="flex-1 min-h-[80px] bg-gray-950 border-gray-700 text-gray-200 placeholder-gray-600 focus:ring-indigo-500 focus:border-indigo-500 rounded-md shadow-sm"
                                            value={analysisPrompt}
                                            onChange={(e) => setAnalysisPrompt(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="mt-4 flex justify-end">
                                    <Button
                                        color="indigo"
                                        onClick={handleProject}
                                        disabled={!selectedProduct || dataLoading}
                                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-8"
                                    >
                                        Project Forecast
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-gray-800 rounded-lg h-full">
                        <Line className="h-12 w-12 text-gray-700 mb-4" />
                        <p>No data available. Please select a location and product.</p>
                    </div>
                )}
            </div>

        </div>
      </div>
    </Layout>
  );
};

export default ProductForecast;