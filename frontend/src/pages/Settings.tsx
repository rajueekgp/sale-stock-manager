import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Settings as SettingsIcon,
  Printer,
  Store,
  Receipt,
  Wifi,
  Barcode,
  Save,
  TestTube
} from "lucide-react";
import { toast } from "sonner";

interface PrinterSettings {
  printerName: string;
  paperSize: string;
  printLogo: boolean;
  printHeader: boolean;
  printFooter: boolean;
  autocut: boolean;
  cashDrawer: boolean;
  copies: number;
}

interface StoreSettings {
  storeName: string;
  address: string;
  phone: string;
  email: string;
  gstNumber: string;
  logo: string;
  currency: string;
  taxRate: number;
}

interface BarcodeSettings {
  format: string;
  width: number;
  height: number;
  displayValue: boolean;
  fontSize: number;
}

export default function Settings() {
  const [storeSettings, setStoreSettings] = useState<StoreSettings>({
    storeName: "RetailPOS Store",
    address: "123 Main Street, City, State - 123456",
    phone: "+91 9876543210",
    email: "store@retailpos.com",
    gstNumber: "29ABCDE1234F1Z5",
    logo: "",
    currency: "INR",
    taxRate: 18
  });

  const [printerSettings, setPrinterSettings] = useState<PrinterSettings>({
    printerName: "Default Printer",
    paperSize: "80mm",
    printLogo: true,
    printHeader: true,
    printFooter: true,
    autocut: true,
    cashDrawer: false,
    copies: 1
  });

  const [barcodeSettings, setBarcodeSettings] = useState<BarcodeSettings>({
    format: "CODE128",
    width: 2,
    height: 100,
    displayValue: true,
    fontSize: 12
  });

  const handleSaveSettings = (section: string) => {
    toast.success(`${section} settings saved successfully!`);
  };

  const testPrint = () => {
    toast.success("Test receipt sent to printer!");
  };

  const generateSampleBarcode = () => {
    toast.success("Sample barcode generated!");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure your POS system settings</p>
        </div>
      </div>

      <Tabs defaultValue="store" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="store" className="flex items-center gap-2">
            <Store className="h-4 w-4" />
            Store
          </TabsTrigger>
          <TabsTrigger value="printer" className="flex items-center gap-2">
            <Printer className="h-4 w-4" />
            Printer
          </TabsTrigger>
          <TabsTrigger value="barcode" className="flex items-center gap-2">
            <Barcode className="h-4 w-4" />
            Barcode
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <SettingsIcon className="h-4 w-4" />
            System
          </TabsTrigger>
        </TabsList>

        {/* Store Settings */}
        <TabsContent value="store">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Store className="h-5 w-5" />
                Store Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="storeName">Store Name *</Label>
                  <Input
                    id="storeName"
                    value={storeSettings.storeName}
                    onChange={(e) => setStoreSettings(prev => ({ ...prev, storeName: e.target.value }))}
                    placeholder="Enter store name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gstNumber">GST Number</Label>
                  <Input
                    id="gstNumber"
                    value={storeSettings.gstNumber}
                    onChange={(e) => setStoreSettings(prev => ({ ...prev, gstNumber: e.target.value }))}
                    placeholder="Enter GST number"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Textarea
                  id="address"
                  value={storeSettings.address}
                  onChange={(e) => setStoreSettings(prev => ({ ...prev, address: e.target.value }))}
                  placeholder="Enter store address"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    value={storeSettings.phone}
                    onChange={(e) => setStoreSettings(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="Enter phone number"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={storeSettings.email}
                    onChange={(e) => setStoreSettings(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="Enter email address"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Select 
                    value={storeSettings.currency} 
                    onValueChange={(value) => setStoreSettings(prev => ({ ...prev, currency: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="INR">Indian Rupee (₹)</SelectItem>
                      <SelectItem value="USD">US Dollar ($)</SelectItem>
                      <SelectItem value="EUR">Euro (€)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="taxRate">Default Tax Rate (%)</Label>
                  <Input
                    id="taxRate"
                    type="number"
                    value={storeSettings.taxRate}
                    onChange={(e) => setStoreSettings(prev => ({ ...prev, taxRate: parseFloat(e.target.value) || 0 }))}
                    placeholder="18"
                  />
                </div>
              </div>

              <Button onClick={() => handleSaveSettings('Store')} className="w-full">
                <Save className="h-4 w-4 mr-2" />
                Save Store Settings
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Printer Settings */}
        <TabsContent value="printer">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Printer className="h-5 w-5" />
                Receipt Printer Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="printerName">Printer Name</Label>
                  <Input
                    id="printerName"
                    value={printerSettings.printerName}
                    onChange={(e) => setPrinterSettings(prev => ({ ...prev, printerName: e.target.value }))}
                    placeholder="Enter printer name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="paperSize">Paper Size</Label>
                  <Select 
                    value={printerSettings.paperSize} 
                    onValueChange={(value) => setPrinterSettings(prev => ({ ...prev, paperSize: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="58mm">58mm</SelectItem>
                      <SelectItem value="80mm">80mm</SelectItem>
                      <SelectItem value="A4">A4</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Print Options</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="printLogo">Print Logo</Label>
                    <Switch
                      id="printLogo"
                      checked={printerSettings.printLogo}
                      onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, printLogo: checked }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="printHeader">Print Header</Label>
                    <Switch
                      id="printHeader"
                      checked={printerSettings.printHeader}
                      onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, printHeader: checked }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="printFooter">Print Footer</Label>
                    <Switch
                      id="printFooter"
                      checked={printerSettings.printFooter}
                      onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, printFooter: checked }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="autocut">Auto Cut Paper</Label>
                    <Switch
                      id="autocut"
                      checked={printerSettings.autocut}
                      onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, autocut: checked }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="cashDrawer">Open Cash Drawer</Label>
                    <Switch
                      id="cashDrawer"
                      checked={printerSettings.cashDrawer}
                      onCheckedChange={(checked) => setPrinterSettings(prev => ({ ...prev, cashDrawer: checked }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="copies">Number of Copies</Label>
                    <Input
                      id="copies"
                      type="number"
                      min="1"
                      max="5"
                      value={printerSettings.copies}
                      onChange={(e) => setPrinterSettings(prev => ({ ...prev, copies: parseInt(e.target.value) || 1 }))}
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button onClick={() => handleSaveSettings('Printer')} className="flex-1">
                  <Save className="h-4 w-4 mr-2" />
                  Save Printer Settings
                </Button>
                <Button variant="outline" onClick={testPrint}>
                  <TestTube className="h-4 w-4 mr-2" />
                  Test Print
                </Button>
              </div>

              {/* Receipt Preview */}
              <Card className="bg-muted/50">
                <CardHeader>
                  <CardTitle className="text-sm">Receipt Preview</CardTitle>
                </CardHeader>
                <CardContent className="font-mono text-xs space-y-1">
                  {printerSettings.printHeader && (
                    <div className="text-center border-b pb-2 mb-2">
                      <div className="font-bold">{storeSettings.storeName}</div>
                      <div>{storeSettings.address}</div>
                      <div>Phone: {storeSettings.phone}</div>
                      <div>GST: {storeSettings.gstNumber}</div>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Invoice: INV-2024-001</span>
                    <span>Date: {new Date().toLocaleDateString()}</span>
                  </div>
                  <div>Customer: John Doe</div>
                  <hr className="my-2" />
                  <div className="flex justify-between">
                    <span>Rice Basmati 1kg x2</span>
                    <span>₹330.00</span>
                  </div>
                  <hr className="my-2" />
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>₹330.00</span>
                  </div>
                  <div className="flex justify-between">
                    <span>GST (5%):</span>
                    <span>₹15.71</span>
                  </div>
                  <div className="flex justify-between font-bold">
                    <span>Total:</span>
                    <span>₹330.00</span>
                  </div>
                  {printerSettings.printFooter && (
                    <div className="text-center border-t pt-2 mt-2">
                      <div>Thank you for shopping!</div>
                      <div>Visit again</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Barcode Settings */}
        <TabsContent value="barcode">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Barcode className="h-5 w-5" />
                Barcode Generator Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="barcodeFormat">Barcode Format</Label>
                  <Select 
                    value={barcodeSettings.format} 
                    onValueChange={(value) => setBarcodeSettings(prev => ({ ...prev, format: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CODE128">CODE128</SelectItem>
                      <SelectItem value="EAN13">EAN13</SelectItem>
                      <SelectItem value="UPC">UPC</SelectItem>
                      <SelectItem value="CODE39">CODE39</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fontSize">Font Size</Label>
                  <Input
                    id="fontSize"
                    type="number"
                    min="8"
                    max="20"
                    value={barcodeSettings.fontSize}
                    onChange={(e) => setBarcodeSettings(prev => ({ ...prev, fontSize: parseInt(e.target.value) || 12 }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="barcodeWidth">Width</Label>
                  <Input
                    id="barcodeWidth"
                    type="number"
                    min="1"
                    max="5"
                    value={barcodeSettings.width}
                    onChange={(e) => setBarcodeSettings(prev => ({ ...prev, width: parseInt(e.target.value) || 2 }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="barcodeHeight">Height</Label>
                  <Input
                    id="barcodeHeight"
                    type="number"
                    min="50"
                    max="200"
                    value={barcodeSettings.height}
                    onChange={(e) => setBarcodeSettings(prev => ({ ...prev, height: parseInt(e.target.value) || 100 }))}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="displayValue">Display Value Below Barcode</Label>
                <Switch
                  id="displayValue"
                  checked={barcodeSettings.displayValue}
                  onCheckedChange={(checked) => setBarcodeSettings(prev => ({ ...prev, displayValue: checked }))}
                />
              </div>

              <div className="flex gap-4">
                <Button onClick={() => handleSaveSettings('Barcode')} className="flex-1">
                  <Save className="h-4 w-4 mr-2" />
                  Save Barcode Settings
                </Button>
                <Button variant="outline" onClick={generateSampleBarcode}>
                  <Barcode className="h-4 w-4 mr-2" />
                  Generate Sample
                </Button>
              </div>

              {/* Barcode Preview */}
              <Card className="bg-muted/50">
                <CardHeader>
                  <CardTitle className="text-sm">Barcode Preview</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center space-y-2">
                  <div 
                    className="bg-white p-4 border-2 border-dashed border-gray-300 rounded"
                    style={{ 
                      width: `${barcodeSettings.width * 60}px`,
                      height: `${barcodeSettings.height + 40}px`
                    }}
                  >
                    <div className="w-full h-full bg-gradient-to-r from-black via-transparent to-black bg-repeat-x opacity-80"></div>
                    {barcodeSettings.displayValue && (
                      <div 
                        className="text-center mt-2 font-mono"
                        style={{ fontSize: `${barcodeSettings.fontSize}px` }}
                      >
                        8901030801234
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">Format: {barcodeSettings.format}</p>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Settings */}
        <TabsContent value="system">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wifi className="h-5 w-5" />
                  Network Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="networkMode">Network Mode</Label>
                  <Select defaultValue="auto">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Automatic</SelectItem>
                      <SelectItem value="manual">Manual</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="syncInterval">Data Sync (minutes)</Label>
                  <Input
                    id="syncInterval"
                    type="number"
                    defaultValue="15"
                    min="5"
                    max="60"
                  />
                </div>
                <Button className="w-full">
                  <Save className="h-4 w-4 mr-2" />
                  Save Network Settings
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Receipt className="h-5 w-5" />
                  Data Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button variant="outline" className="w-full">
                  Export All Data
                </Button>
                <Button variant="outline" className="w-full">
                  Import Data
                </Button>
                <Button variant="outline" className="w-full">
                  Backup Database
                </Button>
                <Button variant="destructive" className="w-full">
                  Reset All Data
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}