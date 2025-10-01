import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Plus, Pencil, Trash2, Search, User, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  gstNumber: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  opening_balance: number;
  outstandingBalance?: number; // Optional as it might not be in the form
  createdDate?: string; // Optional as it might not be in the form
  total_spent: number;
  total_orders: number;
  last_purchase: string | null;
}

// API fetching functions
const fetchCustomers = async (): Promise<Customer[]> => {
  const response = await fetch('/api/customers');
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const jsonResponse = await response.json();
  return jsonResponse.data; // Extract the array from the 'data' key
};

const addCustomer = async (customer: Partial<Customer>): Promise<Customer> => {
  const response = await fetch('/api/customers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(customer),
  });
  if (!response.ok) throw new Error('Failed to add customer');
  return response.json();
};

const updateCustomer = async (customer: Partial<Customer> & { id: string }): Promise<Customer> => {
  const response = await fetch(`/api/customers/${customer.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(customer),
  });
  if (!response.ok) throw new Error('Failed to update customer');
  return response.json();
};

const deleteCustomer = async (id: string): Promise<void> => {
  const response = await fetch(`/api/customers/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete customer');
};

const Customers = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [openingBalanceType, setOpeningBalanceType] = useState<'collect' | 'pay'>('collect');

  const [formData, setFormData] = useState<Partial<Customer>>({
    name: "",
    email: "",
    phone: "",
    gstNumber: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
    opening_balance: 0,
    outstandingBalance: 0,
  });

  const queryClient = useQueryClient();

  const { data: customers = [], isLoading, isError } = useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: fetchCustomers,
  });

  const mutationOptions = {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  };

  const filteredCustomers = customers?.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.phone.includes(searchTerm) ||
      (customer.email && customer.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
      customer.gstNumber.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const addMutation = useMutation({
    ...mutationOptions,
    mutationFn: addCustomer,
    onSuccess: (data) => {
      toast.success(`${data.name} has been added successfully.`);
      mutationOptions.onSuccess();
    },
    onError: () => toast.error("Failed to add customer."),
  });

  const updateMutation = useMutation({
    ...mutationOptions,
    mutationFn: updateCustomer,
    onSuccess: (data) => {
      toast.success(`${data.name} has been updated successfully.`);
      mutationOptions.onSuccess();
    },
    onError: () => toast.error("Failed to update customer."),
  });

  const deleteMutation = useMutation({ ...mutationOptions, mutationFn: deleteCustomer });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      let newFormData = { ...prev };
      if (name === "opening_balance") {
        const rawValue = parseFloat(value) || 0;
        newFormData.opening_balance = openingBalanceType === 'collect' ? -Math.abs(rawValue) : Math.abs(rawValue);
      } else if (name === "outstandingBalance") {
        newFormData.outstandingBalance = parseFloat(value) || 0;
      } else {
        newFormData[name as keyof typeof newFormData] = value;
      }
      return newFormData;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (editingCustomer) {
      updateMutation.mutate({ ...formData, id: editingCustomer.id });
    } else {
      addMutation.mutate(formData);
    }

    resetForm();
  };

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer); // Keep this to manage dialog title
    setFormData(customer); // Pre-fill form
    if (customer.opening_balance < 0) {
      setOpeningBalanceType('collect');
    } else {
      setOpeningBalanceType('pay');
    }
    setIsDialogOpen(true); // Open dialog
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => toast.success("Customer has been removed successfully."),
      onError: () => toast.error("Failed to remove customer."),
    });
  };

  const resetForm = () => {
    setFormData({
      name: "",
      email: "",
      phone: "",
      gstNumber: "",
      address: "",
      city: "",
      state: "",
      pincode: "",
      opening_balance: 0,
      outstandingBalance: 0,
    });
    setOpeningBalanceType('collect');
    setEditingCustomer(null);
    setIsDialogOpen(false);
  };

  // Reset form when dialog closes
  useEffect(() => {
    if (!isDialogOpen) {
      resetForm();
    }
  }, [isDialogOpen]);

  const totalCustomers = customers?.length || 0;
  const totalOutstanding = customers?.reduce(
    (sum, customer) => sum + (customer.outstandingBalance || 0),
    0
  ) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customers</h1>
          <p className="text-muted-foreground">
            Manage your customer database
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild disabled={isLoading}>
            <Button onClick={() => resetForm()}>
              <Plus className="mr-2 h-4 w-4" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingCustomer ? "Edit Customer" : "Add New Customer"}
              </DialogTitle>
              <DialogDescription>
                {editingCustomer
                  ? "Update customer information"
                  : "Enter customer details to add a new customer"}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Customer Name *</Label>
                    <Input
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number *</Label>
                    <Input
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gstNumber">GST Number</Label>
                    <Input
                      id="gstNumber"
                      name="gstNumber"
                      value={formData.gstNumber}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    name="address"
                    value={formData.address}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      name="city"
                      value={formData.city}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      name="state"
                      value={formData.state}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pincode">Pincode</Label>
                    <Input
                      id="pincode"
                      name="pincode"
                      value={formData.pincode}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Opening Balance (₹)</Label>
                    <div className="flex h-10 w-full items-center rounded-md border border-input bg-background text-sm ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                      <Input
                        id="opening_balance"
                        name="opening_balance"
                        type="number"
                        value={Math.abs(formData.opening_balance || 0)}
                        onChange={handleInputChange}
                        className="h-full w-full border-0 bg-transparent px-3 py-2 [appearance:textfield] focus-visible:ring-0 focus-visible:ring-offset-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                      />
                      <Select value={openingBalanceType} onValueChange={(value: 'collect' | 'pay') => {
                        setOpeningBalanceType(value);
                        setFormData(prev => ({...prev, opening_balance: -prev.opening_balance }));
                      }}>
                        <SelectTrigger className="h-full w-[60%] rounded-l-none border-0 border-l bg-blue-100 focus:ring-0 focus:ring-offset-0">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="collect">To Collect</SelectItem>
                          <SelectItem value="pay">To Pay</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="outstandingBalance">
                      Outstanding Balance (₹)
                    </Label>
                    <Input
                      id="outstandingBalance"
                      name="outstandingBalance"
                      type="number"
                      value={formData.outstandingBalance}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit">
                  {(addMutation.isPending || updateMutation.isPending) && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  {editingCustomer ? "Update" : "Add"}{" "}
                  Customer
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Customers
            </CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCustomers}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Outstanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{totalOutstanding.toLocaleString("en-IN")}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCustomers}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Customer List</CardTitle>
          <CardDescription>
            View and manage all customers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, phone, email, or GST..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>GST Number</TableHead>
                  <TableHead>Total Spent</TableHead>
                  <TableHead className="text-right">Outstanding</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center h-24">
                      <Loader2 className="mx-auto h-6 w-6 animate-spin text-muted-foreground" />
                    </TableCell>
                  </TableRow>
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-destructive">
                      Failed to load customers. Please try again.
                    </TableCell>
                  </TableRow>
                ) : filteredCustomers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center">
                      No customers found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCustomers?.map((customer) => (
                    <TableRow key={customer.id}>
                      <TableCell className="font-medium">
                        {customer.id}
                      </TableCell>
                      <TableCell>{customer.name}</TableCell>
                      <TableCell>{customer.phone}</TableCell>
                      <TableCell>{customer.email}</TableCell>
                      <TableCell>{customer.gstNumber || 'N/A'}</TableCell>
                      <TableCell>₹{customer.total_spent.toLocaleString("en-IN")}</TableCell>
                      <TableCell className="text-right">
                        ₹{(customer.outstandingBalance || 0).toLocaleString("en-IN")}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(customer)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(customer.id)}
                            disabled={deleteMutation.isPending && deleteMutation.variables === customer.id}
                          >
                            {deleteMutation.isPending && deleteMutation.variables === customer.id 
                              ? <Loader2 className="h-4 w-4 animate-spin" /> 
                              : <Trash2 className="h-4 w-4" />}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Customers;