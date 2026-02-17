import React, { useState, useEffect } from 'react';
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
} from "@tremor/react";
import axios from 'axios';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const response = await axios.get('/api/orders');
        setOrders(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching orders", error);
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  const handleRowClick = (id) => {
    navigate(`/orders/${id}`);
  };

  const getStatusColor = (status) => {
      switch(status) {
          case 'Ordered': return 'blue';
          case 'Shipped': return 'purple';
          case 'Received': return 'emerald';
          case 'Pending': return 'yellow';
          default: return 'gray';
      }
  };

  return (
    <Layout>
      <Card>
        <Title>Purchase Orders Dashboard</Title>
        <Text>Manage all purchase orders and requests.</Text>

        {loading ? (
            <div className="mt-6 text-center">Loading Orders...</div>
        ) : (
            <Table className="mt-6">
                <TableHead>
                    <TableRow>
                        <TableHeaderCell>Reference</TableHeaderCell>
                        <TableHeaderCell>Product</TableHeaderCell>
                        <TableHeaderCell>Vendor</TableHeaderCell>
                        <TableHeaderCell>Quantity</TableHeaderCell>
                        <TableHeaderCell>Date</TableHeaderCell>
                        <TableHeaderCell>Status</TableHeaderCell>
                        <TableHeaderCell>ETA</TableHeaderCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {orders.map((order) => (
                        <TableRow
                            key={order.id}
                            className="cursor-pointer hover:bg-gray-50"
                            onClick={() => handleRowClick(order.id)}
                        >
                            <TableCell className="font-medium text-gray-900">{order.po_reference}</TableCell>
                            <TableCell>{order.product_name}</TableCell>
                            <TableCell>{order.vendor_name}</TableCell>
                            <TableCell>{order.quantity}</TableCell>
                            <TableCell>{order.created_at}</TableCell>
                            <TableCell>
                                <Badge color={getStatusColor(order.status)}>
                                    {order.status}
                                </Badge>
                                {order.confirmation_status === 'Pending' && (
                                     <span className="ml-2 text-xs text-yellow-600 font-bold">(Draft)</span>
                                )}
                            </TableCell>
                            <TableCell>{order.eta}</TableCell>
                        </TableRow>
                    ))}
                    {orders.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={7} className="text-center text-gray-500 py-4">
                                No orders found.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        )}
      </Card>
    </Layout>
  );
};

export default Orders;
