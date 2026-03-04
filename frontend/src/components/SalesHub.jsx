import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { Card, Title, Text, Button, Table, TableHead, TableRow, TableHeaderCell, TableBody, TableCell, Badge } from "@tremor/react";
import axios from 'axios';
import { Plus } from 'lucide-react';

const SalesHub = () => {
  const [sales, setSales] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [salesRes, invoicesRes] = await Promise.all([
        axios.get('/api/sales'),
        axios.get('/api/invoices')
      ]);
      setSales(salesRes.data.sales);
      setInvoices(invoicesRes.data.invoices);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data", error);
      setLoading(false);
    }
  };

  const handleAddSale = () => {
    // Placeholder for add sale modal/form
    alert("Add Sale functionality coming soon");
  };

  if (loading) {
    return <Layout><div className="p-10 text-center">Loading Sales Data...</div></Layout>;
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Title>Sales Hub</Title>
            <Text>Manage sales and view invoices.</Text>
          </div>
          <Button icon={Plus} onClick={handleAddSale}>
            Add Sale
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
            <Title>Recent Sales</Title>
            <Table className="mt-5">
                <TableHead>
                <TableRow>
                    <TableHeaderCell>ID</TableHeaderCell>
                    <TableHeaderCell>Customer</TableHeaderCell>
                    <TableHeaderCell>Qty</TableHeaderCell>
                    <TableHeaderCell>Date</TableHeaderCell>
                </TableRow>
                </TableHead>
                <TableBody>
                {sales.slice(0, 10).map((item) => (
                    <TableRow key={item.id}>
                    <TableCell>{item.id}</TableCell>
                    <TableCell>
                        <Text>{item.customer_name}</Text>
                    </TableCell>
                    <TableCell>
                        <Text>{item.quantity_sold}</Text>
                    </TableCell>
                    <TableCell>
                        <Text>{item.sale_date}</Text>
                    </TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            </Card>

            <Card>
            <Title>Recent Invoices</Title>
            <Table className="mt-5">
                <TableHead>
                <TableRow>
                    <TableHeaderCell>Invoice #</TableHeaderCell>
                    <TableHeaderCell>Amount</TableHeaderCell>
                    <TableHeaderCell>Date</TableHeaderCell>
                </TableRow>
                </TableHead>
                <TableBody>
                {invoices.slice(0, 10).map((item) => (
                    <TableRow key={item.id}>
                    <TableCell>{item.invoice_number}</TableCell>
                    <TableCell>
                        <Text>${item.total_amount.toFixed(2)}</Text>
                    </TableCell>
                    <TableCell>
                        <Text>{item.generated_date}</Text>
                    </TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
            </Card>
        </div>
      </div>
    </Layout>
  );
};

export default SalesHub;