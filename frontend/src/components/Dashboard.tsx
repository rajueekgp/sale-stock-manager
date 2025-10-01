import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  TrendingDown,
  Package,
  ShoppingCart,
  DollarSign,
  AlertTriangle,
  Users,
  BarChart3
} from "lucide-react";
import heroImage from "@/assets/pos-hero.jpg";

// Mock data - in real app, this would come from JSON files
const dashboardStats = {
  todaySales: { amount: 12500, change: +12 },
  totalProducts: { count: 1250, lowStock: 15 },
  totalCustomers: { count: 890, new: 5 },
  monthlyRevenue: { amount: 185000, change: +8 }
};

const recentSales = [
  { id: "TXN001", customer: "John Doe", amount: 330, time: "2:30 PM" },
  { id: "TXN002", customer: "Jane Smith", amount: 150, time: "2:15 PM" },
  { id: "TXN003", customer: "Mike Johnson", amount: 89, time: "1:45 PM" },
];

const lowStockItems = [
  { name: "Milk 1L", stock: 5, minStock: 10 },
  { name: "Bread Loaf", stock: 8, minStock: 15 },
  { name: "Sugar 1kg", stock: 12, minStock: 20 },
];

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Hero Section */}
      <div className="relative rounded-2xl overflow-hidden">
        <img 
          src={heroImage} 
          alt="POS Dashboard" 
          className="w-full h-48 object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/80 to-accent/60 flex items-center justify-center">
          <div className="text-center text-white">
            <h1 className="text-3xl font-bold mb-2">Welcome to RetailPOS</h1>
            <p className="text-lg opacity-90">Complete Point of Sale & Inventory Management</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-success to-success/80 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">Today's Sales</CardTitle>
            <DollarSign className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{dashboardStats.todaySales.amount.toLocaleString()}</div>
            <p className="text-xs opacity-80 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              +{dashboardStats.todaySales.change}% from yesterday
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-primary to-primary/80 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">Total Products</CardTitle>
            <Package className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.totalProducts.count}</div>
            <p className="text-xs opacity-80 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {dashboardStats.totalProducts.lowStock} low stock alerts
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-accent to-accent/80 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">Customers</CardTitle>
            <Users className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats.totalCustomers.count}</div>
            <p className="text-xs opacity-80">
              +{dashboardStats.totalCustomers.new} new this week
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-warning to-warning/80 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">Monthly Revenue</CardTitle>
            <BarChart3 className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{dashboardStats.monthlyRevenue.amount.toLocaleString()}</div>
            <p className="text-xs opacity-80 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              +{dashboardStats.monthlyRevenue.change}% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Sales */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-success" />
              Recent Sales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentSales.map((sale) => (
                <div key={sale.id} className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                  <div>
                    <p className="font-medium">{sale.customer}</p>
                    <p className="text-sm text-muted-foreground">{sale.id}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-success">₹{sale.amount}</p>
                    <p className="text-xs text-muted-foreground">{sale.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              View All Sales
            </Button>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-warning" />
              Low Stock Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {lowStockItems.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-warning/10 rounded-lg">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">Min: {item.minStock}</p>
                  </div>
                  <Badge variant="destructive">
                    {item.stock} left
                  </Badge>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              Manage Inventory
            </Button>
          </CardContent>        
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button className="h-20 flex-col gap-2 bg-gradient-to-br from-primary to-primary-hover">
              <ShoppingCart className="h-6 w-6" />
              <span>New Sale</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Package className="h-6 w-6" />
              <span>Add Product</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <TrendingUp className="h-6 w-6" />
              <span>View Reports</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Users className="h-6 w-6" />
              <span>Customers</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}