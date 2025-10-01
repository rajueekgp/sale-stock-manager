import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Plus,
  Search,
  ShoppingCart,
  Printer,
  Eye,
  Calendar,
  DollarSign,
  CreditCard,
  Scan,
  Minus
} from "lucide-react";
import { toast } from "sonner";

// Import sample data
import salesData from "@/data/sales.json";
import productsData from "@/data/products.json";

interface SaleItem {
  productId: string;
  name: string;
  quantity: number;
  mrp: number;
  salePrice: number;
  discount: number;
  taxRate: number;
  total: number;
}

interface Sale {
  id: string;
  invoiceNumber: string;
  date: string;
  customerName: string;
  customerPhone: string;
  items: SaleItem[];
  subtotal: number;
  totalDiscount: number;
  totalTax: number;
  grandTotal: number;
  paymentMethod: string;
  status: string;
}

export default function Sales() {
  const [sales, setSales] = useState<Sale[]>(salesData);
  const [products] = useState(productsData);
  const [searchTerm, setSearchTerm] = useState("");
  const [isNewSaleDialogOpen, setIsNewSaleDialogOpen] = useState(false);
  const [currentSale, setCurrentSale] = useState<Partial<Sale>>({
    customerName: "",
    customerPhone: "",
    items: [],
    paymentMethod: "Cash"
  });
  const [selectedProduct, setSelectedProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [barcodeScan, setBarcodeScan] = useState("");

  const filteredSales = sales.filter(sale => 
    sale.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sale.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sale.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const generateInvoiceNumber = () => {
    const today = new Date();
    const year = today.getFullYear();
    const lastSale = sales[sales.length - 1];
    const lastNumber = lastSale ? parseInt(lastSale.invoiceNumber.split('-')[2]) : 0;
    return `INV-${year}-${String(lastNumber + 1).padStart(3, '0')}`;
  };

  const addItemToSale = () => {
    const product = products.find(p => p.id === selectedProduct || p.barcode === barcodeScan);
    if (!product) {
      toast.error("Product not found");
      return;
    }

    const existingItemIndex = currentSale.items?.findIndex(item => item.productId === product.id);
    
    if (existingItemIndex !== undefined && existingItemIndex >= 0) {
      // Update existing item quantity
      const updatedItems = [...(currentSale.items || [])];
      updatedItems[existingItemIndex].quantity += quantity;
      updatedItems[existingItemIndex].total = updatedItems[existingItemIndex].quantity * updatedItems[existingItemIndex].salePrice;
      
      setCurrentSale(prev => ({ ...prev, items: updatedItems }));
    } else {
      // Add new item
      const newItem: SaleItem = {
        productId: product.id,
        name: product.name,
        quantity,
        mrp: product.mrp,
        salePrice: product.salePrice,
        discount: 0,
        taxRate: product.taxRate,
        total: quantity * product.salePrice
      };

      setCurrentSale(prev => ({
        ...prev,
        items: [...(prev.items || []), newItem]
      }));
    }

    setSelectedProduct("");
    setBarcodeScan("");
    setQuantity(1);
    toast.success("Item added to sale");
  };

  const removeItemFromSale = (productId: string) => {
    setCurrentSale(prev => ({
      ...prev,
      items: prev.items?.filter(item => item.productId !== productId) || []
    }));
  };

  const calculateTotals = () => {
    const items = currentSale.items || [];
    const subtotal = items.reduce((sum, item) => sum + item.total, 0);
    const totalDiscount = items.reduce((sum, item) => sum + (item.discount * item.quantity), 0);
    const totalTax = items.reduce((sum, item) => sum + ((item.total * item.taxRate) / (100 + item.taxRate)), 0);
    const grandTotal = subtotal - totalDiscount;
    
    return { subtotal, totalDiscount, totalTax, grandTotal };
  };

  const completeSale = () => {
    if (!currentSale.items?.length) {
      toast.error("Please add items to the sale");
      return;
    }

    if (!currentSale.customerName) {
      toast.error("Please enter customer name");
      return;
    }

    const { subtotal, totalDiscount, totalTax, grandTotal } = calculateTotals();
    
    const newSale: Sale = {
      id: `TXN${String(sales.length + 1).padStart(3, '0')}`,
      invoiceNumber: generateInvoiceNumber(),
      date: new Date().toISOString(),
      customerName: currentSale.customerName || "",
      customerPhone: currentSale.customerPhone || "",
      items: currentSale.items || [],
      subtotal,
      totalDiscount,
      totalTax,
      grandTotal,
      paymentMethod: currentSale.paymentMethod || "Cash",
      status: "Completed"
    };

    setSales(prev => [...prev, newSale]);
    setCurrentSale({
      customerName: "",
      customerPhone: "",
      items: [],
      paymentMethod: "Cash"
    });
    setIsNewSaleDialogOpen(false);
    toast.success("Sale completed successfully!");
  };

  const printInvoice = (sale: Sale) => {
    // In a real app, this would trigger actual printing
    toast.success("Invoice sent to printer");
  };

  const totals = calculateTotals();
  const todaySales = sales.filter(sale => 
    new Date(sale.date).toDateString() === new Date().toDateString()
  );
  const todayRevenue = todaySales.reduce((sum, sale) => sum + sale.grandTotal, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sales</h1>
          <p className="text-muted-foreground">Manage sales transactions and invoices</p>
        </div>
        <Dialog open={isNewSaleDialogOpen} onOpenChange={setIsNewSaleDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-success to-success/80">
              <Plus className="h-4 w-4 mr-2" />
              New Sale
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[95vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>New Sale - {generateInvoiceNumber()}</DialogTitle>
            </DialogHeader>
            
            <div className="grid grid-cols-2 gap-6">
              {/* Left Side - Customer & Items */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="customerName">Customer Name *</Label>
                    <Input
                      id="customerName"
                      value={currentSale.customerName}
                      onChange={(e) => setCurrentSale(prev => ({ ...prev, customerName: e.target.value }))}
                      placeholder="Enter customer name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="customerPhone">Customer Phone</Label>
                    <Input
                      id="customerPhone"
                      value={currentSale.customerPhone}
                      onChange={(e) => setCurrentSale(prev => ({ ...prev, customerPhone: e.target.value }))}
                      placeholder="Enter phone number"
                    />
                  </div>
                </div>

                {/* Add Items */}
                <div className="border rounded-lg p-4 space-y-4">
                  <h3 className="font-semibold">Add Items</h3>
                  
                  {/* Barcode Scanner */}
                  <div className="space-y-2">
                    <Label htmlFor="barcode">Scan Barcode</Label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Scan className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="barcode"
                          value={barcodeScan}
                          onChange={(e) => setBarcodeScan(e.target.value)}
                          placeholder="Scan or enter barcode"
                          className="pl-10"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              addItemToSale();
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Manual Product Selection */}
                  <div className="grid grid-cols-3 gap-2">
                    <Select value={selectedProduct} onValueChange={setSelectedProduct}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select product" />
                      </SelectTrigger>
                      <SelectContent>
                        {products.map(product => (
                          <SelectItem key={product.id} value={product.id}>
                            {product.name} - ₹{product.salePrice}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      type="number"
                      value={quantity}
                      onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                      placeholder="Qty"
                      min="1"
                    />
                    <Button onClick={addItemToSale}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Items List */}
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead>Qty</TableHead>
                        <TableHead>Price</TableHead>
                        <TableHead>Total</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {currentSale.items?.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{item.name}</TableCell>
                          <TableCell>{item.quantity}</TableCell>
                          <TableCell>₹{item.salePrice}</TableCell>
                          <TableCell>₹{item.total}</TableCell>
                          <TableCell>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => removeItemFromSale(item.productId)}
                            >
                              <Minus className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Right Side - Bill Summary */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Bill Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span>Subtotal:</span>
                      <span>₹{totals.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tax (GST):</span>
                      <span>₹{totals.totalTax.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Discount:</span>
                      <span>₹{totals.totalDiscount.toFixed(2)}</span>
                    </div>
                    <hr />
                    <div className="flex justify-between text-lg font-bold">
                      <span>Grand Total:</span>
                      <span>₹{totals.grandTotal.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>

                <div className="space-y-2">
                  <Label htmlFor="paymentMethod">Payment Method</Label>
                  <Select 
                    value={currentSale.paymentMethod} 
                    onValueChange={(value) => setCurrentSale(prev => ({ ...prev, paymentMethod: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="Card">Card</SelectItem>
                      <SelectItem value="UPI">UPI</SelectItem>
                      <SelectItem value="Net Banking">Net Banking</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setIsNewSaleDialogOpen(false)} className="flex-1">
                    Cancel
                  </Button>
                  <Button onClick={completeSale} className="flex-1 bg-gradient-to-r from-success to-success/80">
                    Complete Sale
                  </Button>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{todayRevenue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{todaySales.length} transactions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Sales</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sales.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Sale Value</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{sales.length > 0 ? (sales.reduce((sum, sale) => sum + sale.grandTotal, 0) / sales.length).toFixed(0) : '0'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{sales.reduce((sum, sale) => sum + sale.grandTotal, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sales Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sales</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by invoice, customer, or transaction ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Payment</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSales.map((sale) => (
                <TableRow key={sale.id}>
                  <TableCell className="font-mono">{sale.invoiceNumber}</TableCell>
                  <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{sale.customerName}</div>
                      <div className="text-sm text-muted-foreground">{sale.customerPhone}</div>
                    </div>
                  </TableCell>
                  <TableCell>{sale.items.length} items</TableCell>
                  <TableCell className="font-bold">₹{sale.grandTotal.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={sale.paymentMethod === 'Cash' ? 'default' : 'secondary'}>
                      {sale.paymentMethod}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="default">{sale.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => printInvoice(sale)}
                      >
                        <Printer className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}