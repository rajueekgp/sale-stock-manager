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
  ShoppingBag,
  Truck,
  Package,
  Eye,
  Edit,
  FileText
} from "lucide-react";
import { toast } from "sonner";

import purchasesData from "@/data/purchases.json";
import productsData from "@/data/products.json";

interface PurchaseItem {
  productId: string;
  name: string;
  quantity: number;
  purchasePrice: number;
  total: number;
}

interface Purchase {
  id: string;
  billNumber: string;
  date: string;
  supplierName: string;
  supplierContact: string;
  items: PurchaseItem[];
  subtotal: number;
  totalTax: number;
  grandTotal: number;
  status: string;
}

export default function Purchase() {
  const [purchases, setPurchases] = useState<Purchase[]>(purchasesData);
  const [products] = useState(productsData);
  const [searchTerm, setSearchTerm] = useState("");
  const [isNewPurchaseDialogOpen, setIsNewPurchaseDialogOpen] = useState(false);
  const [currentPurchase, setCurrentPurchase] = useState<Partial<Purchase>>({
    supplierName: "",
    supplierContact: "",
    items: []
  });
  const [selectedProduct, setSelectedProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [purchasePrice, setPurchasePrice] = useState(0);

  const filteredPurchases = purchases.filter(purchase => 
    purchase.billNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    purchase.supplierName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    purchase.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const generateBillNumber = () => {
    const today = new Date();
    const year = today.getFullYear();
    const lastPurchase = purchases[purchases.length - 1];
    const lastNumber = lastPurchase ? parseInt(lastPurchase.billNumber.split('-')[2]) : 0;
    return `BILL-${year}-${String(lastNumber + 1).padStart(3, '0')}`;
  };

  const addItemToPurchase = () => {
    const product = products.find(p => p.id === selectedProduct);
    if (!product) {
      toast.error("Please select a product");
      return;
    }

    if (quantity <= 0 || purchasePrice <= 0) {
      toast.error("Please enter valid quantity and price");
      return;
    }

    const existingItemIndex = currentPurchase.items?.findIndex(item => item.productId === product.id);
    
    if (existingItemIndex !== undefined && existingItemIndex >= 0) {
      const updatedItems = [...(currentPurchase.items || [])];
      updatedItems[existingItemIndex].quantity += quantity;
      updatedItems[existingItemIndex].total = updatedItems[existingItemIndex].quantity * updatedItems[existingItemIndex].purchasePrice;
      
      setCurrentPurchase(prev => ({ ...prev, items: updatedItems }));
    } else {
      const newItem: PurchaseItem = {
        productId: product.id,
        name: product.name,
        quantity,
        purchasePrice,
        total: quantity * purchasePrice
      };

      setCurrentPurchase(prev => ({
        ...prev,
        items: [...(prev.items || []), newItem]
      }));
    }

    setSelectedProduct("");
    setQuantity(1);
    setPurchasePrice(0);
    toast.success("Item added to purchase");
  };

  const removeItemFromPurchase = (productId: string) => {
    setCurrentPurchase(prev => ({
      ...prev,
      items: prev.items?.filter(item => item.productId !== productId) || []
    }));
  };

  const calculateTotals = () => {
    const items = currentPurchase.items || [];
    const subtotal = items.reduce((sum, item) => sum + item.total, 0);
    const totalTax = subtotal * 0.18; // Assuming 18% tax
    const grandTotal = subtotal + totalTax;
    
    return { subtotal, totalTax, grandTotal };
  };

  const completePurchase = () => {
    if (!currentPurchase.items?.length) {
      toast.error("Please add items to the purchase");
      return;
    }

    if (!currentPurchase.supplierName) {
      toast.error("Please enter supplier name");
      return;
    }

    const { subtotal, totalTax, grandTotal } = calculateTotals();
    
    const newPurchase: Purchase = {
      id: `PUR${String(purchases.length + 1).padStart(3, '0')}`,
      billNumber: generateBillNumber(),
      date: new Date().toISOString(),
      supplierName: currentPurchase.supplierName || "",
      supplierContact: currentPurchase.supplierContact || "",
      items: currentPurchase.items || [],
      subtotal,
      totalTax,
      grandTotal,
      status: "Received"
    };

    setPurchases(prev => [...prev, newPurchase]);
    setCurrentPurchase({
      supplierName: "",
      supplierContact: "",
      items: []
    });
    setIsNewPurchaseDialogOpen(false);
    toast.success("Purchase order created successfully!");
  };

  const totals = calculateTotals();
  const thisMonthPurchases = purchases.filter(purchase => {
    const purchaseDate = new Date(purchase.date);
    const currentDate = new Date();
    return purchaseDate.getMonth() === currentDate.getMonth() && 
           purchaseDate.getFullYear() === currentDate.getFullYear();
  });
  const thisMonthTotal = thisMonthPurchases.reduce((sum, purchase) => sum + purchase.grandTotal, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Purchase Orders</h1>
          <p className="text-muted-foreground">Manage inward inventory and supplier orders</p>
        </div>
        <Dialog open={isNewPurchaseDialogOpen} onOpenChange={setIsNewPurchaseDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-primary to-primary-hover">
              <Plus className="h-4 w-4 mr-2" />
              New Purchase
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[95vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>New Purchase Order - {generateBillNumber()}</DialogTitle>
            </DialogHeader>
            
            <div className="grid grid-cols-2 gap-6">
              {/* Left Side - Supplier & Items */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="supplierName">Supplier Name *</Label>
                    <Input
                      id="supplierName"
                      value={currentPurchase.supplierName}
                      onChange={(e) => setCurrentPurchase(prev => ({ ...prev, supplierName: e.target.value }))}
                      placeholder="Enter supplier name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="supplierContact">Supplier Contact</Label>
                    <Input
                      id="supplierContact"
                      value={currentPurchase.supplierContact}
                      onChange={(e) => setCurrentPurchase(prev => ({ ...prev, supplierContact: e.target.value }))}
                      placeholder="Enter contact details"
                    />
                  </div>
                </div>

                {/* Add Items */}
                <div className="border rounded-lg p-4 space-y-4">
                  <h3 className="font-semibold">Add Items</h3>
                  
                  <div className="grid grid-cols-4 gap-2">
                    <Select value={selectedProduct} onValueChange={setSelectedProduct}>
                      <SelectTrigger className="col-span-2">
                        <SelectValue placeholder="Select product" />
                      </SelectTrigger>
                      <SelectContent>
                        {products.map(product => (
                          <SelectItem key={product.id} value={product.id}>
                            {product.name}
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
                    <Input
                      type="number"
                      value={purchasePrice}
                      onChange={(e) => setPurchasePrice(parseFloat(e.target.value) || 0)}
                      placeholder="Price"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  
                  <Button onClick={addItemToPurchase} className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Item
                  </Button>
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
                      {currentPurchase.items?.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{item.name}</TableCell>
                          <TableCell>{item.quantity}</TableCell>
                          <TableCell>₹{item.purchasePrice}</TableCell>
                          <TableCell>₹{item.total}</TableCell>
                          <TableCell>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => removeItemFromPurchase(item.productId)}
                            >
                              Remove
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Right Side - Order Summary */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Order Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span>Subtotal:</span>
                      <span>₹{totals.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tax (18%):</span>
                      <span>₹{totals.totalTax.toFixed(2)}</span>
                    </div>
                    <hr />
                    <div className="flex justify-between text-lg font-bold">
                      <span>Grand Total:</span>
                      <span>₹{totals.grandTotal.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setIsNewPurchaseDialogOpen(false)} className="flex-1">
                    Cancel
                  </Button>
                  <Button onClick={completePurchase} className="flex-1">
                    Create Purchase Order
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
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <ShoppingBag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{thisMonthTotal.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{thisMonthPurchases.length} orders</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{purchases.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Truck className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">
              {purchases.filter(p => p.status === 'Pending').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Order Value</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{purchases.length > 0 ? (purchases.reduce((sum, p) => sum + p.grandTotal, 0) / purchases.length).toFixed(0) : '0'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Purchase Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase Orders</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by bill number, supplier, or order ID..."
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
                <TableHead>Bill Number</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Supplier</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPurchases.map((purchase) => (
                <TableRow key={purchase.id}>
                  <TableCell className="font-mono">{purchase.billNumber}</TableCell>
                  <TableCell>{new Date(purchase.date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{purchase.supplierName}</div>
                      <div className="text-sm text-muted-foreground">{purchase.supplierContact}</div>
                    </div>
                  </TableCell>
                  <TableCell>{purchase.items.length} items</TableCell>
                  <TableCell className="font-bold">₹{purchase.grandTotal.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge variant={purchase.status === 'Received' ? 'default' : 'secondary'}>
                      {purchase.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
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