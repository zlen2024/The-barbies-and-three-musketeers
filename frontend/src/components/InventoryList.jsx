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

const InventoryList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        const response = await axios.get('/api/inventory');
        setProducts(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching inventory", error);
        setLoading(false);
      }
    };

    fetchInventory();
  }, []);

  const handleRowClick = (sku) => {
    // Encode the SKU to handle slashes correctly
    navigate(`/inventory/product/${encodeURIComponent(sku)}`);
  };

  const getStatusColor = (status) => {
      switch(status) {
          case 'In Stock': return 'emerald';
          case 'Low Stock': return 'yellow';
          case 'Critical': return 'red';
          default: return 'gray';
      }
  };

  return (
    <Layout>
      <Card>
        <Title>Inventory Overview</Title>
        <Text>A list of all products and their current stock status.</Text>

        {loading ? (
           <div className="mt-6 text-center">Loading Inventory...</div>
        ) : (
            <Table className="mt-6">
            <TableHead>
                <TableRow>
                <TableHeaderCell>Model / SKU</TableHeaderCell>
                <TableHeaderCell>Product Name</TableHeaderCell>
                <TableHeaderCell>Total Stock (In Hand)</TableHeaderCell>
                <TableHeaderCell>AMS (3-Month)</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {products.map((product) => (
                <TableRow
                    key={product.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleRowClick(product.sku_id)}
                >
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
                ))}
            </TableBody>
            </Table>
        )}
      </Card>
    </Layout>
  );
};

export default InventoryList;
