import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart3,
  TrendingUp,
  Download,
  Calendar,
  DollarSign,
  Package,
  Users,
  FileText,
  PieChart,
  Filter
} from "lucide-react";

import salesData from "@/data/sales.json";
import productsData from "@/data/products.json";
import purchasesData from "@/data/purchases.json";

export default function Reports() {
  const [dateRange, setDateRange] = useState<{ from: Date; to: Date }>({
    from: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    to: new Date()
  });
  const [reportType, setReportType] = useState("sales");

  // Sales Analytics
  const totalSales = salesData.reduce((sum, sale) => sum + sale.grandTotal, 0);
  const totalTransactions = salesData.length;
  const avgSaleValue = totalTransactions > 0 ? totalSales / totalTransactions : 0;
  
  // Product Analytics
  const totalProducts = productsData.length;
  const totalInventoryValue = productsData.reduce((sum, p) => sum + (p.stock * p.purchasePrice), 0);
  const lowStockCount = productsData.filter(p => p.stock <= p.minStock).length;

  // Purchase Analytics
  const totalPurchases = purchasesData.reduce((sum, purchase) => sum + purchase.grandTotal, 0);
  
  // Top Selling Products (mock data based on random selection)
  const topProducts = productsData.slice(0, 5).map(product => ({
    ...product,
    soldQuantity: Math.floor(Math.random() * 100) + 20,
    revenue: Math.floor(Math.random() * 50000) + 10000
  }));

  // Sales by Category
  const categoryData = productsData.reduce((acc, product) => {
    if (!acc[product.category]) {
      acc[product.category] = { count: 0, value: 0 };
    }
    acc[product.category].count += 1;
    acc[product.category].value += product.stock * product.salePrice;
    return acc;
  }, {} as Record<string, { count: number; value: number }>);

  // Tax Summary (GST Report)
  const taxData = [
    { rate: "5%", sales: 45000, tax: 2250 },
    { rate: "12%", sales: 25000, tax: 3000 },
    { rate: "18%", sales: 85000, tax: 15300 },
    { rate: "28%", sales: 15000, tax: 4200 }
  ];
  const totalTaxCollected = taxData.reduce((sum, item) => sum + item.tax, 0);

  const exportReport = () => {
    // Mock export functionality
    console.log("Exporting report...");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reports & Analytics</h1>
          <p className="text-muted-foreground">Business insights and performance metrics</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
          <Button onClick={exportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Date Range and Report Type */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Date Range</label>
              <div className="flex gap-2">
                <Input type="date" defaultValue={dateRange.from.toISOString().split('T')[0]} />
                <Input type="date" defaultValue={dateRange.to.toISOString().split('T')[0]} />
              </div>
            </div>
            <div className="w-full md:w-64">
              <label className="text-sm font-medium mb-2 block">Report Type</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">Sales Report</SelectItem>
                  <SelectItem value="inventory">Inventory Report</SelectItem>
                  <SelectItem value="tax">Tax Report</SelectItem>
                  <SelectItem value="profit">Profit & Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{totalSales.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              +12.5% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Transactions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTransactions}</div>
            <p className="text-xs text-muted-foreground">Avg: ₹{avgSaleValue.toFixed(0)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inventory Value</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{totalInventoryValue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{totalProducts} products</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tax Collected</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{totalTaxCollected.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">GST this month</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sales" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="sales">Sales Analysis</TabsTrigger>
          <TabsTrigger value="products">Product Performance</TabsTrigger>
          <TabsTrigger value="tax">Tax Reports</TabsTrigger>
          <TabsTrigger value="inventory">Inventory Reports</TabsTrigger>
        </TabsList>

        {/* Sales Analysis */}
        <TabsContent value="sales" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Sales by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(categoryData).map(([category, data]) => (
                    <div key={category} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{category}</div>
                        <div className="text-sm text-muted-foreground">{data.count} products</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">₹{data.value.toLocaleString()}</div>
                        <div className="text-sm text-muted-foreground">
                          {((data.value / totalInventoryValue) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {salesData.slice(0, 5).map((sale) => (
                      <TableRow key={sale.id}>
                        <TableCell className="font-mono text-xs">{sale.invoiceNumber}</TableCell>
                        <TableCell>{sale.customerName}</TableCell>
                        <TableCell>₹{sale.grandTotal}</TableCell>
                        <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Product Performance */}
        <TabsContent value="products" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Selling Products</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Qty Sold</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Stock Left</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topProducts.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{product.name}</div>
                          <div className="text-sm text-muted-foreground">{product.brand}</div>
                        </div>
                      </TableCell>
                      <TableCell>{product.category}</TableCell>
                      <TableCell>{product.soldQuantity} {product.unit}</TableCell>
                      <TableCell>₹{product.revenue.toLocaleString()}</TableCell>
                      <TableCell>
                        <span className={product.stock <= product.minStock ? "text-warning" : ""}>
                          {product.stock}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tax Reports */}
        <TabsContent value="tax" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>GST Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tax Rate</TableHead>
                    <TableHead>Taxable Sales</TableHead>
                    <TableHead>Tax Amount</TableHead>
                    <TableHead>Percentage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {taxData.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{item.rate}</TableCell>
                      <TableCell>₹{item.sales.toLocaleString()}</TableCell>
                      <TableCell>₹{item.tax.toLocaleString()}</TableCell>
                      <TableCell>
                        {((item.tax / totalTaxCollected) * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="border-t-2">
                    <TableCell className="font-bold">Total</TableCell>
                    <TableCell className="font-bold">
                      ₹{taxData.reduce((sum, item) => sum + item.sales, 0).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-bold">₹{totalTaxCollected.toLocaleString()}</TableCell>
                    <TableCell className="font-bold">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Inventory Reports */}
        <TabsContent value="inventory" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Stock Status Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>In Stock</span>
                    <span className="font-bold text-success">
                      {productsData.filter(p => p.stock > p.minStock).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Low Stock</span>
                    <span className="font-bold text-warning">{lowStockCount}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Out of Stock</span>
                    <span className="font-bold text-destructive">
                      {productsData.filter(p => p.stock === 0).length}
                    </span>
                  </div>
                  <hr />
                  <div className="flex justify-between items-center">
                    <span className="font-semibold">Total Products</span>
                    <span className="font-bold">{totalProducts}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Inventory Value by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(categoryData).map(([category, data]) => (
                    <div key={category} className="flex justify-between items-center">
                      <span>{category}</span>
                      <span className="font-bold">₹{data.value.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}