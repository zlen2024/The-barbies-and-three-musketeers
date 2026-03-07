import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from './Layout';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Badge,
  Button,
  Callout,
} from "@tremor/react";
import {
    Package,
    ArrowLeft,
    CheckCircle,
    Clock,
    Mail,
    FileText,
    Truck,
    AlertCircle
} from 'lucide-react';
import axios from 'axios';

const OrderDetail = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const navigate = useNavigate();

  const fetchOrderDetail = async () => {
    try {
      const response = await axios.get(`/api/orders/${orderId}`);
      setOrder(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching order detail", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);


  const handleReceiveOrder = async () => {
      if (!window.confirm("Are you sure you want to mark this order as received?")) return;
      setConfirming(true);
      try {
          await axios.post(`/api/orders/${orderId}/receive`);
          alert("Order received successfully!");
          fetchOrderDetail();
      } catch (e) {
          alert("Error receiving order: " + (e.response?.data?.message || e.message));
      } finally {
          setConfirming(false);
      }
  };

  const handleConfirmOrder = async () => {
      if (!window.confirm("Are you sure you want to confirm this order? This will send the PO to the vendor.")) return;

      setConfirming(true);
      try {
          await axios.post(`/api/orders/${orderId}/confirm`);
          alert("Order confirmed successfully!");
          fetchOrderDetail(); // Refresh data
      } catch (e) {
          alert("Error confirming order: " + (e.response?.data?.message || e.message));
      } finally {
          setConfirming(false);
      }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center mt-10">Loading Order Details...</div>
      </Layout>
    );
  }

  if (!order) {
      return (
          <Layout>
              <div className="text-center mt-10">Order not found.</div>
          </Layout>
      );
  }

  const getStatusColor = (status) => {
      switch(status) {
          case 'Ordered': return 'blue';
          case 'Shipped': return 'purple';
          case 'Received': return 'emerald';
          case 'Pending': return 'yellow';
          default: return 'gray';
      }
  };

  const getTimelineIcon = (stage) => {
      switch(stage) {
          case 'Created': return FileText;
          case 'Confirmed': return CheckCircle;
          case 'Shipped': return Truck;
          case 'Received': return Package;
          default: return Clock;
      }
  };

  return (
    <Layout>
      <div className="mb-4">
          <button onClick={() => navigate('/orders')} className="flex items-center text-gray-500 hover:text-gray-700">
              <ArrowLeft size={16} className="mr-1" /> Back to Orders
          </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">

              {/* Header Card */}
              <Card decoration="top" decorationColor={getStatusColor(order.status)}>
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
                      <div>
                          <Title>Order {order.po_reference}</Title>
                          <Text>Created on {order.created_at}</Text>
                          <div className="mt-2 flex items-center space-x-2">
                              <Badge color={getStatusColor(order.status)}>{order.status}</Badge>
                              {(role === 'Manager' || role === 'Admin') && order.confirmation_status === 'Pending' && (
                                  <Badge color="yellow" icon={AlertCircle}>Draft / Pending Approval</Badge>
                              )}
                          </div>
                      </div>
                      <div className="mt-4 sm:mt-0">
                          {(role === 'Manager' || role === 'Admin') && order.confirmation_status === 'Pending' && (
                              <Button
                                size="lg"
                                color="emerald"
                                icon={CheckCircle}
                                onClick={handleConfirmOrder}
                                disabled={confirming}
                              >
                                  {confirming ? 'Confirming...' : 'Confirm Order'}
                              </Button>
                          )}

                          {(role === 'Warehouse' || role === 'Admin') && order.status === 'Shipped' && (
                              <Button
                                size="lg"
                                color="blue"
                                icon={CheckCircle}
                                onClick={handleReceiveOrder}
                                disabled={confirming}
                              >
                                  {confirming ? 'Processing...' : 'Confirm Received'}
                              </Button>
                          )}

                      </div>
                  </div>
              </Card>

              {/* Product & Vendor Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                      <Title>Product Details</Title>
                      <Flex className="mt-4">
                          <Text>Product Name</Text>
                          <Text className="font-medium text-gray-900 text-right">{order.product.name}</Text>
                      </Flex>
                      <Flex className="mt-2">
                          <Text>SKU</Text>
                          <Text className="font-mono text-gray-700">{order.product.sku}</Text>
                      </Flex>
                      <Flex className="mt-2">
                          <Text>Quantity Ordered</Text>
                          <Metric>{order.quantity}</Metric>
                      </Flex>
                  </Card>

                  <Card>
                      <Title>Vendor Information</Title>
                      <Flex className="mt-4">
                          <Text>Vendor Name</Text>
                          <Text className="font-medium text-gray-900">{order.vendor.name}</Text>
                      </Flex>
                      <Flex className="mt-2">
                          <Text>Contact Person</Text>
                          <Text>{order.vendor.contact}</Text>
                      </Flex>
                      <Flex className="mt-2">
                          <Text>Email</Text>
                          <Text className="font-mono text-blue-600">{order.vendor.email}</Text>
                      </Flex>
                  </Card>
              </div>

              {/* Timeline Visualization */}
              <Card>
                  <Title>Order Timeline</Title>
                  <div className="mt-6">
                      <div className="relative flex items-center justify-between w-full">
                            {/* Line connecting items */}
                            <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 -z-10"></div>

                            {order.timeline.map((step, index) => {
                                const Icon = getTimelineIcon(step.stage);
                                return (
                                    <div key={index} className="flex flex-col items-center bg-white px-2">
                                        <div className={`
                                            w-10 h-10 rounded-full flex items-center justify-center border-2
                                            ${step.completed ? 'bg-emerald-100 border-emerald-500 text-emerald-600' : 'bg-gray-50 border-gray-300 text-gray-400'}
                                        `}>
                                            <Icon size={20} />
                                        </div>
                                        <Text className={`mt-2 text-xs font-semibold ${step.completed ? 'text-emerald-700' : 'text-gray-500'}`}>
                                            {step.stage}
                                        </Text>
                                        {step.date && (
                                            <Text className="text-xs text-gray-400">{step.date}</Text>
                                        )}
                                    </div>
                                );
                            })}
                      </div>
                  </div>
              </Card>

              {/* Email Preview */}
              <Card>
                  <div className="flex items-center space-x-2 mb-4">
                      <Mail className="text-gray-500" />
                      <Title>Sent Email Content</Title>
                  </div>
                  <div className="bg-gray-50 p-4 rounded border border-gray-200 text-sm font-mono text-gray-700 whitespace-pre-wrap">
                      {order.email_preview}
                  </div>
              </Card>
          </div>

          {/* Right Column: Forecasting & Insights */}
          <div className="lg:col-span-1 space-y-6">
              <Card className="h-full bg-slate-50 border-dashed border-2 border-slate-300">
                  <div className="flex flex-col items-center justify-center h-full text-center py-10">
                      <Title className="text-slate-400">Forecasting Report</Title>
                      <Text className="mt-2 text-slate-400 text-sm">
                          AI-driven forecasting insights for this order will appear here.
                      </Text>
                      <div className="mt-6 p-4 bg-white rounded shadow-sm w-full text-left">
                          <Text className="font-semibold text-gray-400 text-xs uppercase mb-2">Planned Feature</Text>
                          <Text className="text-gray-500 text-sm">
                              Expected demand vs supplied quantity analysis pending integration with sales velocity model.
                          </Text>
                      </div>
                  </div>
              </Card>
          </div>

      </div>
    </Layout>
  );
};

export default OrderDetail;
