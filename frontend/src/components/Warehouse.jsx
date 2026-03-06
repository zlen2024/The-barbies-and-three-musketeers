import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, Building2, Package, TrendingUp, DollarSign,
  AlertCircle, ChevronRight, Activity, Calendar, Box
} from 'lucide-react';
import {
  Card, Title, Text, Metric, Flex, Badge,
  BarList, AreaChart, Grid, Col, DonutChart, LineChart
} from '@tremor/react';
import Layout from './Layout';

// Hook to parse query parameters
function useQuery() {
  const { search } = useLocation();
  return React.useMemo(() => new URLSearchParams(search), [search]);
}

const Warehouse = () => {
  const query = useQuery();
  const navigate = useNavigate();
  const locationId = query.get('location');
  const productId = query.get('product');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Data states
  const [summaryData, setSummaryData] = useState(null);
  const [productData, setProductData] = useState(null);

  useEffect(() => {
    if (!locationId) {
      setError('No location specified.');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        if (productId) {
          // Fetch specific product stats at this location
          const res = await fetch(`/api/warehouse/product_stats?location_id=${locationId}&product_id=${productId}`);
          if (!res.ok) throw new Error('Failed to fetch product stats');
          const data = await res.json();
          if (data.success) {
            setProductData(data);
          } else {
            setError(data.message || 'Error fetching data');
          }
        } else {
          // Fetch location summary
          const res = await fetch(`/api/warehouse/summary?location_id=${locationId}`);
          if (!res.ok) throw new Error('Failed to fetch location summary');
          const data = await res.json();
          if (data.success) {
            setSummaryData(data);
          } else {
            setError(data.message || 'Error fetching data');
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [locationId, productId]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
            {error}
          </div>
          <button
            onClick={() => navigate('/inventory')}
            className="mt-4 flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Inventory
          </button>
        </div>
      </Layout>
    );
  }

  // --- Product Specific View ---
  if (productId && productData) {
    const { location, data } = productData;

    return (
      <Layout>
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          {/* Breadcrumb / Header */}
          <div className="mb-6">
            <div className="flex items-center text-sm text-gray-500 mb-2">
              <Link to="/inventory" className="hover:text-blue-600">Inventory</Link>
              <ChevronRight className="w-4 h-4 mx-1" />
              <Link to={`/inventory/warehouse?location=${locationId}`} className="hover:text-blue-600">
                {location.loc_code} Warehouse
              </Link>
              <ChevronRight className="w-4 h-4 mx-1" />
              <span className="text-gray-900 font-medium">{data.sku}</span>
            </div>
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
                <p className="text-gray-500 flex items-center mt-1">
                  <Building2 className="w-4 h-4 mr-1" />
                  Location: {location.loc_code} - {location.description}
                </p>
              </div>
              <Badge color={data.current_stock > 10 ? 'emerald' : data.current_stock > 0 ? 'amber' : 'red'}>
                {data.current_stock > 10 ? 'In Stock' : data.current_stock > 0 ? 'Low Stock' : 'Out of Stock'}
              </Badge>
            </div>
          </div>

          <Grid numItems={1} numItemsSm={2} numItemsLg={4} className="gap-6 mb-6">
            <Card decoration="top" decorationColor="blue">
              <Flex alignItems="start">
                <div>
                  <Text>Current Stock</Text>
                  <Metric>{data.current_stock}</Metric>
                </div>
                <Package className="w-8 h-8 text-blue-500 opacity-20" />
              </Flex>
            </Card>
            <Card decoration="top" decorationColor="amber">
              <Flex alignItems="start">
                <div>
                  <Text>Incoming (POs)</Text>
                  <Metric>{data.incoming_stock}</Metric>
                </div>
                <AlertCircle className="w-8 h-8 text-amber-500 opacity-20" />
              </Flex>
            </Card>
            <Card decoration="top" decorationColor="emerald">
              <Flex alignItems="start">
                <div>
                  <Text>30d Avg Daily Sales</Text>
                  <Metric>{data.avg_daily_sales.toFixed(1)}</Metric>
                </div>
                <TrendingUp className="w-8 h-8 text-emerald-500 opacity-20" />
              </Flex>
            </Card>
            <Card decoration="top" decorationColor="purple">
              <Flex alignItems="start">
                <div>
                  <Text>Reserved Stock</Text>
                  <Metric>{data.reserved_stock}</Metric>
                </div>
                <Box className="w-8 h-8 text-purple-500 opacity-20" />
              </Flex>
            </Card>
          </Grid>

          <Grid numItems={1} numItemsLg={3} className="gap-6">
            <Col numColSpan={1} numColSpanLg={2}>
              <Card
                className="h-full cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => navigate(`/forecast?location=${locationId}&product=${productId}`)}
              >
                <div className="flex justify-between items-center">
                  <Title>Sales History (Last 30 Days) - {location.loc_code}</Title>
                  <Text className="text-xs text-indigo-600 flex items-center">Click for Analysis <ArrowRight className="h-3 w-3 ml-1"/></Text>
                </div>
                <div className="mt-4 h-72">
                  <AreaChart
                    data={data.sales_history}
                    index="date"
                    categories={["sales"]}
                    colors={["blue"]}
                    valueFormatter={(number) => Intl.NumberFormat("en-US").format(number).toString()}
                    showLegend={false}
                    className="h-full"
                  />
                </div>
              </Card>
            </Col>

            <Col numColSpan={1}>
              <Card className="h-full">
                <Title>Recent Activity at {location.loc_code}</Title>
                <div className="mt-4 space-y-4">
                  {data.recent_activities.length > 0 ? (
                    data.recent_activities.map((act, i) => (
                      <div key={i} className="flex items-start">
                        <div className="flex-shrink-0 mt-1">
                          {act.type === 'SALE' ? (
                            <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                              <DollarSign className="w-4 h-4 text-emerald-600" />
                            </div>
                          ) : act.type === 'RESTOCK' ? (
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                              <Package className="w-4 h-4 text-blue-600" />
                            </div>
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                              <Calendar className="w-4 h-4 text-gray-600" />
                            </div>
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{act.description}</p>
                          <p className="text-xs text-gray-500">{act.date}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <Text>No recent activity recorded at this location.</Text>
                  )}
                </div>
              </Card>
            </Col>
          </Grid>
        </div>
      </Layout>
    );
  }

  // --- Location Summary View ---
  if (!productId && summaryData) {
    const { location, data } = summaryData;

    return (
      <Layout>
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          <div className="mb-6 flex justify-between items-end">
            <div>
              <div className="flex items-center text-sm text-gray-500 mb-2">
                <Link to="/inventory" className="hover:text-blue-600">Inventory</Link>
                <ChevronRight className="w-4 h-4 mx-1" />
                <span className="text-gray-900 font-medium">Warehouse Summary</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Building2 className="w-6 h-6 mr-2 text-blue-600" />
                {location.loc_code} Performance
              </h1>
              <p className="text-gray-500">{location.description}</p>
            </div>
            <button
              onClick={() => navigate('/inventory')}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> All Locations
            </button>
          </div>

          <Grid numItems={1} numItemsSm={2} numItemsLg={3} className="gap-6 mb-6">
            <Card decoration="top" decorationColor="blue">
              <Text>Total Stock Units</Text>
              <Metric>{data.total_stock}</Metric>
            </Card>
            <Card decoration="top" decorationColor="emerald">
              <Text>Total Sales Revenue</Text>
              <Metric>${data.total_sales.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</Metric>
            </Card>
            <Card decoration="top" decorationColor="indigo">
              <Text>Total Items Sold</Text>
              <Metric>{data.total_items_sold}</Metric>
            </Card>
          </Grid>

          <Grid numItems={1} numItemsLg={3} className="gap-6 mb-6">
            <Col numColSpan={1}>
              <Card>
                <Title>Stock by Category</Title>
                <div className="mt-4">
                  {data.stock_by_category && data.stock_by_category.length > 0 ? (
                    <DonutChart
                      className="h-60 mt-4"
                      data={data.stock_by_category}
                      category="stock"
                      index="category"
                      colors={["blue", "cyan", "indigo", "violet", "fuchsia"]}
                      valueFormatter={(num) => `${num} units`}
                    />
                  ) : (
                    <Text className="mt-4 text-center">No category data available</Text>
                  )}
                </div>
              </Card>
            </Col>
            <Col numColSpan={1} numColSpanLg={2}>
              <Card className="h-full flex flex-col">
                <Title>Products at Location</Title>
                <div className="mt-4 flex-1 overflow-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Incoming</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.products.map((p) => (
                        <tr key={p.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{p.sku}</div>
                            <div className="text-sm text-gray-500">{p.name}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right">
                            <div className={`text-sm font-medium ${p.current_stock < 10 ? 'text-red-600' : 'text-gray-900'}`}>
                              {p.current_stock}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                            {p.incoming_stock}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button
                              onClick={() => navigate(`/inventory/warehouse?location=${locationId}&product=${p.id}`)}
                              className="text-blue-600 hover:text-blue-900 flex items-center justify-end w-full"
                            >
                              Details <ChevronRight className="w-4 h-4 ml-1" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {data.products.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No products found at this location.
                    </div>
                  )}
                </div>
              </Card>
            </Col>
          </Grid>
        </div>
      </Layout>
    );
  }

  return null;
};

export default Warehouse;
