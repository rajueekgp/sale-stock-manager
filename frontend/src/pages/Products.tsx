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
  Edit,
  Trash2,
  Package,
  AlertTriangle,
  Barcode,
  Download
} from "lucide-react";
import { toast } from "sonner";

// Import sample data
import productsData from "@/data/products.json";

interface Product {
  id: string;
  name: string;
  barcode: string;
  hsnCode: string;
  category: string;
  brand: string;
  mrp: number;
  salePrice: number;
  purchasePrice: number;
  taxRate: number;
  stock: number;
  minStock: number;
  unit: string;
  createdAt: string;
  updatedAt: string;
}

export default function Products() {
  const [products, setProducts] = useState<Product[]>(productsData);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newProduct, setNewProduct] = useState<Partial<Product>>({
    name: "",
    category: "",
    brand: "",
    mrp: 0,
    salePrice: 0,
    purchasePrice: 0,
    taxRate: 18,
    stock: 0,
    minStock: 5,
    unit: "pcs",
    hsnCode: ""
  });

  const categories = ["all", ...Array.from(new Set(products.map(p => p.category)))];
  
  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.barcode.includes(searchTerm) ||
                         product.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || product.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const generateBarcode = () => {
    const barcode = "890" + Math.random().toString().substr(2, 10);
    setNewProduct(prev => ({ ...prev, barcode }));
    toast.success("Barcode generated successfully!");
  };

  const generateProductId = () => {
    const lastProduct = products[products.length - 1];
    const lastId = lastProduct ? parseInt(lastProduct.id.replace('PRD', '')) : 0;
    return `PRD${String(lastId + 1).padStart(3, '0')}`;
  };

  const handleAddProduct = () => {
    if (!newProduct.name || !newProduct.category) {
      toast.error("Please fill in required fields");
      return;
    }

    const product: Product = {
      id: generateProductId(),
      barcode: newProduct.barcode || generateProductId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ...newProduct
    } as Product;

    setProducts(prev => [...prev, product]);
    setNewProduct({
      name: "",
      category: "",
      brand: "",
      mrp: 0,
      salePrice: 0,
      purchasePrice: 0,
      taxRate: 18,
      stock: 0,
      minStock: 5,
      unit: "pcs",
      hsnCode: ""
    });
    setIsAddDialogOpen(false);
    toast.success("Product added successfully!");
  };

  const handleDeleteProduct = (id: string) => {
    setProducts(prev => prev.filter(p => p.id !== id));
    toast.success("Product deleted successfully!");
  };

  const lowStockProducts = products.filter(p => p.stock <= p.minStock);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Products</h1>
          <p className="text-muted-foreground">Manage your inventory and product catalog</p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-primary to-primary-hover">
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Product</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter product name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Input
                  id="category"
                  value={newProduct.category}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, category: e.target.value }))}
                  placeholder="Enter category"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="brand">Brand</Label>
                <Input
                  id="brand"
                  value={newProduct.brand}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, brand: e.target.value }))}
                  placeholder="Enter brand"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hsnCode">HSN Code</Label>
                <Input
                  id="hsnCode"
                  value={newProduct.hsnCode}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, hsnCode: e.target.value }))}
                  placeholder="Enter HSN code"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="barcode">Barcode</Label>
                <div className="flex gap-2">
                  <Input
                    id="barcode"
                    value={newProduct.barcode}
                    onChange={(e) => setNewProduct(prev => ({ ...prev, barcode: e.target.value }))}
                    placeholder="Enter or generate barcode"
                  />
                  <Button type="button" variant="outline" onClick={generateBarcode}>
                    <Barcode className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="unit">Unit</Label>
                <Select value={newProduct.unit} onValueChange={(value) => setNewProduct(prev => ({ ...prev, unit: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs">Pieces</SelectItem>
                    <SelectItem value="kg">Kilograms</SelectItem>
                    <SelectItem value="L">Liters</SelectItem>
                    <SelectItem value="g">Grams</SelectItem>
                    <SelectItem value="ml">Milliliters</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="mrp">MRP (₹)</Label>
                <Input
                  id="mrp"
                  type="number"
                  value={newProduct.mrp}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, mrp: parseFloat(e.target.value) || 0 }))}
                  placeholder="0.00"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="salePrice">Sale Price (₹)</Label>
                <Input
                  id="salePrice"
                  type="number"
                  value={newProduct.salePrice}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, salePrice: parseFloat(e.target.value) || 0 }))}
                  placeholder="0.00"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="purchasePrice">Purchase Price (₹)</Label>
                <Input
                  id="purchasePrice"
                  type="number"
                  value={newProduct.purchasePrice}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, purchasePrice: parseFloat(e.target.value) || 0 }))}
                  placeholder="0.00"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="taxRate">Tax Rate (%)</Label>
                <Select value={newProduct.taxRate?.toString()} onValueChange={(value) => setNewProduct(prev => ({ ...prev, taxRate: parseFloat(value) }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">0%</SelectItem>
                    <SelectItem value="5">5%</SelectItem>
                    <SelectItem value="12">12%</SelectItem>
                    <SelectItem value="18">18%</SelectItem>
                    <SelectItem value="28">28%</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="stock">Current Stock</Label>
                <Input
                  id="stock"
                  type="number"
                  value={newProduct.stock}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, stock: parseInt(e.target.value) || 0 }))}
                  placeholder="0"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="minStock">Minimum Stock</Label>
                <Input
                  id="minStock"
                  type="number"
                  value={newProduct.minStock}
                  onChange={(e) => setNewProduct(prev => ({ ...prev, minStock: parseInt(e.target.value) || 0 }))}
                  placeholder="5"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddProduct}>
                Add Product
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{products.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{lowStockProducts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{categories.length - 1}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{products.reduce((sum, p) => sum + (p.stock * p.purchasePrice), 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Product Catalog</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search products by name, barcode, or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map(category => (
                  <SelectItem key={category} value={category}>
                    {category === "all" ? "All Categories" : category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Barcode</TableHead>
                <TableHead>HSN</TableHead>
                <TableHead>MRP</TableHead>
                <TableHead>Sale Price</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProducts.map((product) => (
                <TableRow key={product.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{product.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {product.brand} • {product.category}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{product.barcode}</TableCell>
                  <TableCell>{product.hsnCode}</TableCell>
                  <TableCell>₹{product.mrp}</TableCell>
                  <TableCell>₹{product.salePrice}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {product.stock} {product.unit}
                      {product.stock <= product.minStock && (
                        <AlertTriangle className="h-4 w-4 text-warning" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={product.stock > product.minStock ? "default" : "destructive"}>
                      {product.stock > product.minStock ? "In Stock" : "Low Stock"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleDeleteProduct(product.id)}
                      >
                        <Trash2 className="h-4 w-4" />
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