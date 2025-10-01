import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  FileText,
  TrendingUp,
  Settings,
  ArrowLeftRight,
  CreditCard,
  BarChart3,
  Users,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/" },
  { icon: Package, label: "Products", path: "/products" },
  { icon: ShoppingCart, label: "Sales", path: "/sales" },
  { icon: FileText, label: "Purchase", path: "/purchase" },
  { icon: ArrowLeftRight, label: "Returns", path: "/returns" },
  { icon: CreditCard, label: "Credit Notes", path: "/credit-notes" },
  { icon: TrendingUp, label: "Inventory", path: "/inventory" },
  { icon: BarChart3, label: "Reports", path: "/reports" },
  { icon: Users, label: "Customers", path: "/customers" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div className={cn(
      "bg-pos-sidebar text-pos-sidebarForeground h-screen transition-all duration-300 ease-in-out flex flex-col",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-pos-sidebarForeground/10">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <h1 className="text-xl font-bold text-pos-sidebarActive">
              RetailPOS
            </h1>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-pos-sidebarForeground/10 transition-colors"
          >
            {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                "hover:bg-pos-sidebarForeground/10",
                isActive 
                  ? "bg-pos-sidebarActive text-white shadow-lg" 
                  : "text-pos-sidebarForeground/80 hover:text-pos-sidebarForeground"
              )}
            >
              <Icon size={20} className="flex-shrink-0" />
              {!collapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-pos-sidebarForeground/10">
        {!collapsed && (
          <div className="text-xs text-pos-sidebarForeground/60 text-center">
            POS System v1.0
          </div>
        )}
      </div>
    </div>
  );
}