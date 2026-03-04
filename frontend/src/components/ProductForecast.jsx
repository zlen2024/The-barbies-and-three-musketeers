import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from './Layout';
import { Card, Title, Text, Button } from "@tremor/react";
import { ArrowLeft } from 'lucide-react';

const ProductForecast = () => {
  const { sku } = useParams();
  const navigate = useNavigate();

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="secondary"
            icon={ArrowLeft}
            onClick={() => navigate(`/inventory/product/${sku}`)}
          >
            Back to Product
          </Button>
          <Title>Product Analysis for {sku}</Title>
        </div>

        <Card>
          <Text className="text-center py-20 text-gray-500">
            Fundamental and technical analysis features coming soon.
          </Text>
        </Card>
      </div>
    </Layout>
  );
};

export default ProductForecast;
