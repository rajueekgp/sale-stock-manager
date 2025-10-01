import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  Package, 
  DollarSign, 
  ShoppingCart,
  AlertTriangle,
  Eye,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    total_products: 0,
    total_customers: 0,
    today_revenue: 0,
    today_sales_count: 0,
    month_revenue: 0,
    month_sales_count: 0,
    low_stock_products: 0,
    recent_sales: [],
    top_products: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard');
      const result = await response.json();
      if (result.success) {
        setDashboardData(result.data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, change, changeType, color, link }) => (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <div className={`flex items-center mt-2 text-sm ${
              changeType === 'increase' ? 'text-green-600' : 'text-red-600'
            }`}>
              {changeType === 'increase' ? (
                <ArrowUpRight size={16} className="mr-1" />
              ) : (
                <ArrowDownRight size={16} className="mr-1" />
              )}
              {change}
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
      {link && (
        <Link 
          to={link} 
          className="mt-4 inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
        >
          View details <Eye size={16} className="ml-1" />
        </Link>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here's what's happening with your store today.</p>
        </div>
        <Link
          to="/pos"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <ShoppingCart size={20} />
          <span>New Sale</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Today's Revenue"
          value={`$${dashboardData.today_revenue?.toFixed(2) || '0.00'}`}
          icon={DollarSign}
          change="+12.5%"
          changeType="increase"
          color="bg-green-500"
          link="/sales"
        />
        <StatCard
          title="Today's Sales"
          value={dashboardData.today_sales_count || 0}
          icon={ShoppingCart}
          change="+8.2%"
          changeType="increase"
          color="bg-blue-500"
          link="/sales"
        />
        <StatCard
          title="Total Products"
          value={dashboardData.total_products || 0}
          icon={Package}
          color="bg-purple-500"
          link="/products"
        />
        <StatCard
          title="Total Customers"
          value={dashboardData.total_customers || 0}
          icon={Users}
          change="+5.1%"
          changeType="increase"
          color="bg-orange-500"
          link="/customers"
        />
      </div>

      {/* Low Stock Alert */}
      {dashboardData.low_stock_products > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="text-yellow-600 mr-3" size={20} />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-yellow-800">
                Low Stock Alert
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                {dashboardData.low_stock_products} products are running low on stock.
              </p>
            </div>
            <Link
              to="/inventory"
              className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded text-sm"
            >
              View Inventory
            </Link>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Sales */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Recent Sales</h2>
              <Link to="/sales" className="text-blue-600 hover:text-blue-800 text-sm">
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {dashboardData.recent_sales?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.recent_sales.map((sale) => (
                  <div key={sale.id} className="flex items-center justify-between py-2">
                    <div>
                      <p className="font-medium text-gray-900">{sale.sale_number}</p>
                      <p className="text-sm text-gray-600">
                        {sale.customer_name || 'Walk-in Customer'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-gray-900">
                        ${sale.total_amount?.toFixed(2)}
                      </p>
                      <p className="text-sm text-gray-600">
                        {new Date(sale.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No recent sales</p>
            )}
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Top Products</h2>
              <Link to="/reports" className="text-blue-600 hover:text-blue-800 text-sm">
                View report
              </Link>
            </div>
          </div>
          <div className="p-6">
            {dashboardData.top_products?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.top_products.map((product, index) => (
                  <div key={index} className="flex items-center justify-between py-2">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <span className="text-blue-600 font-medium text-sm">{index + 1}</span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-600">
                          {product.total_sold} sold
                        </p>
                      </div>
                    </div>
                    <TrendingUp className="text-green-500" size={16} />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No sales data available</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link
            to="/products/new"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Package className="text-blue-600 mb-2" size={24} />
            <span className="text-sm font-medium text-gray-900">Add Product</span>
          </Link>
          <Link
            to="/customers/new"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Users className="text-green-600 mb-2" size={24} />
            <span className="text-sm font-medium text-gray-900">Add Customer</span>
          </Link>
          <Link
            to="/inventory"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <AlertTriangle className="text-yellow-600 mb-2" size={24} />
            <span className="text-sm font-medium text-gray-900">Check Stock</span>
          </Link>
          <Link
            to="/reports"
            className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <TrendingUp className="text-purple-600 mb-2" size={24} />
            <span className="text-sm font-medium text-gray-900">View Reports</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;