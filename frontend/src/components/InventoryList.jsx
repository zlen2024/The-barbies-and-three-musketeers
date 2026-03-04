import React, { useState, useEffect, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Plus, X, ChevronRight, ChevronDown, Search, ExternalLink } from 'lucide-react';
import axios from 'axios';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';

const InventoryList = () => {
  const role = localStorage.getItem('userRole') || 'Staff';

  // Global Products State
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedProductIds, setExpandedProductIds] = useState(new Set());
  const [locationsData, setLocationsData] = useState({}); // productId -> locations array

  // Location-Oriented State
  const [userLocations, setUserLocations] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [locationProducts, setLocationProducts] = useState([]);
  const [locationLoading, setLocationLoading] = useState(false);

  const [newProduct, setNewProduct] = useState({
    model_code: '',
    product_name: '',
    category: '',
    brand: '',
    status: 'Active'
  });
  const navigate = useNavigate();

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      // Fetch both user locations and all products
      const [locationsRes, productsRes] = await Promise.all([
        axios.get('/api/locations'),
        axios.get('/api/inventory')
      ]);

      setUserLocations(locationsRes.data);
      setProducts(productsRes.data);

      // Select the first location by default if available
      if (locationsRes.data.length > 0) {
        setSelectedLocationId(locationsRes.data[0].id.toString());
      }
    } catch (error) {
      console.error("Error fetching initial data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    const fetchLocationProducts = async () => {
      if (!selectedLocationId) return;
      setLocationLoading(true);
      try {
        const response = await axios.get(`/api/inventory/location/${selectedLocationId}`);
        setLocationProducts(response.data);
      } catch (error) {
        console.error("Error fetching location products", error);
      } finally {
        setLocationLoading(false);
      }
    };
    fetchLocationProducts();
  }, [selectedLocationId]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewProduct(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/products', newProduct);
      setIsModalOpen(false);
      setNewProduct({
        model_code: '',
        product_name: '',
        category: '',
        brand: '',
        status: 'Active'
      });
      fetchInitialData();
    } catch (error) {
      console.error("Error adding product", error);
      alert("Failed to add product (ensure Model Code is unique)");
    }
  };

  const handleRowClick = (sku) => {
    // Encode the SKU to handle slashes correctly
    navigate(`/inventory/product/${encodeURIComponent(sku)}`);
  };

  const toggleExpand = async (e, productId) => {
    e.stopPropagation(); // Prevent row click navigation

    const newExpanded = new Set(expandedProductIds);
    if (newExpanded.has(productId)) {
        newExpanded.delete(productId);
    } else {
        newExpanded.add(productId);
        // Fetch locations if not already cached
        if (!locationsData[productId]) {
            try {
                const res = await axios.get(`/api/inventory/${productId}/locations`);
                setLocationsData(prev => ({ ...prev, [productId]: res.data }));
            } catch (err) {
                console.error("Failed to fetch locations", err);
            }
        }
    }
    setExpandedProductIds(newExpanded);
  };

  const getStatusColor = (status) => {
      switch(status) {
          case 'In Stock': return 'emerald';
          case 'Low Stock': return 'yellow';
          case 'Critical': return 'red';
          default: return 'gray';
      }
  };

  const selectedLocationDetails = userLocations.find(l => l.id.toString() === selectedLocationId);
  const filteredProducts = products.filter(p =>
    p.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.sku_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      {/* Top Section: Location-Oriented View */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <Title>Location Inventory</Title>
            <Text>Select a location to view its specific inventory.</Text>
          </div>
          <div className="flex items-center gap-4 w-full md:w-auto">
            <select
              value={selectedLocationId}
              onChange={(e) => setSelectedLocationId(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
            >
              {userLocations.map(loc => (
                <option key={loc.id} value={loc.id}>
                  {loc.loc_code} - {loc.description}
                </option>
              ))}
            </select>
            {selectedLocationDetails && (
              <Button
                icon={ExternalLink}
                variant="secondary"
                onClick={() => navigate(`/inventory/warehouse?location=${selectedLocationDetails.id}`)}
              >
                Manage Warehouse
              </Button>
            )}
          </div>
        </div>

        {selectedLocationDetails && (
          <div className="bg-gray-50 p-4 rounded-md mb-6 border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="block text-sm font-medium text-gray-500">Address</span>
                <span className="block text-sm text-gray-900 mt-1">{selectedLocationDetails.address || 'N/A'}</span>
              </div>
              <div>
                <span className="block text-sm font-medium text-gray-500">Region</span>
                <span className="block text-sm text-gray-900 mt-1">{selectedLocationDetails.region || 'N/A'}</span>
              </div>
            </div>
          </div>
        )}

        {locationLoading ? (
          <div className="mt-6 text-center">Loading Location Products...</div>
        ) : (
          <Table className="mt-4">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Model / SKU</TableHeaderCell>
                <TableHeaderCell>Product Name</TableHeaderCell>
                <TableHeaderCell>Location Stock</TableHeaderCell>
                <TableHeaderCell>AMS (3-Month)</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {locationProducts.length > 0 ? (
                locationProducts.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-medium text-gray-900">
                      {product.sku_id}
                    </TableCell>
                    <TableCell>{product.product_name}</TableCell>
                    <TableCell>{product.quantity}</TableCell>
                    <TableCell>{product.ams_3m}</TableCell>
                    <TableCell>
                      <Badge color={getStatusColor(product.status)}>
                        {product.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-gray-500 py-4">
                    No products found in this location.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Bottom Section: All Products Overview */}
      <Card>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <div>
                <Title>All Products Overview</Title>
                <Text>A consolidated view of all products across all locations.</Text>
            </div>
            <div className="flex items-center gap-4 w-full md:w-auto">
                <div className="relative w-full md:w-64">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search products..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                </div>
                {role === 'Manager' && (
                    <Button icon={Plus} onClick={() => setIsModalOpen(true)}>Add Product</Button>
                )}
            </div>
        </div>

        {loading ? (
           <div className="mt-6 text-center">Loading Inventory...</div>
        ) : (
            <Table className="mt-6">
            <TableHead>
                <TableRow>
                <TableHeaderCell className="w-10"></TableHeaderCell>
                <TableHeaderCell>Model / SKU</TableHeaderCell>
                <TableHeaderCell>Product Name</TableHeaderCell>
                <TableHeaderCell>Total Stock (In Hand)</TableHeaderCell>
                <TableHeaderCell>AMS (3-Month)</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {filteredProducts.map((product) => {
                    const isExpanded = expandedProductIds.has(product.id);
                    return (
                        <Fragment key={product.id}>
                            <TableRow
                                className="cursor-pointer hover:bg-gray-50"
                                onClick={() => handleRowClick(product.sku_id)}
                            >
                                <TableCell>
                                    <button
                                        onClick={(e) => toggleExpand(e, product.id)}
                                        className="p-1 hover:bg-gray-200 rounded text-gray-500"
                                    >
                                        {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                    </button>
                                </TableCell>
                                <TableCell className="font-medium text-gray-900">
                                    {product.sku_id}
                                </TableCell>
                                <TableCell>
                                    {product.product_name}
                                </TableCell>
                                <TableCell>
                                    {product.total_stock}
                                </TableCell>
                                <TableCell>
                                    {product.ams_3m}
                                </TableCell>
                                <TableCell>
                                    <Badge color={getStatusColor(product.status)}>
                                        {product.status}
                                    </Badge>
                                </TableCell>
                            </TableRow>
                            {isExpanded && (
                                <TableRow>
                                    <TableCell colSpan={6} className="bg-gray-50 p-4 shadow-inner">
                                        <div className="px-4 py-2">
                                            <h4 className="text-sm font-semibold text-gray-700 mb-2">Location Breakdown</h4>
                                            {locationsData[product.id] ? (
                                                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                                    {locationsData[product.id].map((loc, idx) => (
                                                        <div key={idx} className="bg-white p-3 rounded border border-gray-200 flex justify-between items-center">
                                                            <div>
                                                                <div className="text-sm font-medium text-gray-900">{loc.location_name}</div>
                                                                <div className="text-xs text-gray-500">{loc.type}</div>
                                                            </div>
                                                            <div className="text-lg font-bold text-blue-600">{loc.quantity}</div>
                                                        </div>
                                                    ))}
                                                    {locationsData[product.id].length === 0 && (
                                                        <div className="text-gray-500 text-sm italic">No stock in any location.</div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="flex items-center space-x-2 text-sm text-gray-500">
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                                                    <span>Loading locations...</span>
                                                </div>
                                            )}
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )}
                        </Fragment>
                    );
                })}
            </TableBody>
            </Table>
        )}
      </Card>

      {/* Add Product Modal */}
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
                      Add New Product
                    </DialogTitle>
                    <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-500">
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Model Code (SKU)</label>
                      <input
                        type="text"
                        name="model_code"
                        required
                        value={newProduct.model_code}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Product Name</label>
                      <input
                        type="text"
                        name="product_name"
                        required
                        value={newProduct.product_name}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <input
                        type="text"
                        name="category"
                        value={newProduct.category}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Brand</label>
                      <input
                        type="text"
                        name="brand"
                        value={newProduct.brand}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Status</label>
                      <select
                        name="status"
                        value={newProduct.status}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                      >
                        <option value="Active">Active</option>
                        <option value="Discontinued">Discontinued</option>
                      </select>
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
                        Add Product
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

export default InventoryList;
