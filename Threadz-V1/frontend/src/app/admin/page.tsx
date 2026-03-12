'use client';

import { useState, useEffect } from 'react';
import { Users, ShoppingCart, Settings, BarChart3, Package, TrendingUp, DollarSign, Eye, Edit, Trash2, Download, Upload, Search, Filter, ChevronDown, X, Check, AlertCircle } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';

interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
  last_login: string;
  status: 'active' | 'inactive' | 'suspended';
}

interface Order {
  order_id: string;
  user_id: string;
  user_name: string;
  total_amount: number;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  created_at: string;
  items_count: number;
}

interface Design {
  design_id: string;
  design_name: string;
  designer_name: string;
  status: 'public' | 'private' | 'pending' | 'flagged';
  downloads: number;
  likes: number;
  created_at: string;
}

const mockUsers: User[] = [
  {
    user_id: 'user-001',
    email: 'john@example.com',
    full_name: 'John Doe',
    role: 'user',
    created_at: '2024-01-15',
    last_login: '2024-03-12',
    status: 'active'
  },
  {
    user_id: 'user-002',
    email: 'jane@example.com',
    full_name: 'Jane Smith',
    role: 'user',
    created_at: '2024-02-20',
    last_login: '2024-03-11',
    status: 'active'
  },
  {
    user_id: 'admin-001',
    email: 'Threadz2026@gmail.com',
    full_name: 'Threadz Admin',
    role: 'admin',
    created_at: '2024-01-01',
    last_login: '2024-03-12',
    status: 'active'
  }
];

const mockOrders: Order[] = [
  {
    order_id: 'order-001',
    user_id: 'user-001',
    user_name: 'John Doe',
    total_amount: 59.99,
    status: 'processing',
    created_at: '2024-03-10',
    items_count: 2
  },
  {
    order_id: 'order-002',
    user_id: 'user-002',
    user_name: 'Jane Smith',
    total_amount: 89.99,
    status: 'shipped',
    created_at: '2024-03-09',
    items_count: 3
  },
  {
    order_id: 'order-003',
    user_id: 'user-001',
    user_name: 'John Doe',
    total_amount: 29.99,
    status: 'delivered',
    created_at: '2024-03-08',
    items_count: 1
  }
];

const mockDesigns: Design[] = [
  {
    design_id: 'design-001',
    design_name: 'Cool Tiger',
    designer_name: 'John Doe',
    status: 'public',
    downloads: 145,
    likes: 89,
    created_at: '2024-03-05'
  },
  {
    design_id: 'design-002',
    design_name: 'Abstract Waves',
    designer_name: 'Jane Smith',
    status: 'public',
    downloads: 92,
    likes: 67,
    created_at: '2024-03-07'
  },
  {
    design_id: 'design-003',
    design_name: 'Minimal Logo',
    designer_name: 'Threadz Admin',
    status: 'pending',
    downloads: 0,
    likes: 0,
    created_at: '2024-03-12'
  }
];

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showOrderDropdown, setShowOrderDropdown] = useState(false);
  const [showDesignDropdown, setShowDesignDropdown] = useState(false);

  // Redirect if not admin
  useEffect(() => {
    if (user && user.role !== 'admin') {
      window.location.href = '/account';
    }
  }, [user]);

  const stats = {
    totalUsers: mockUsers.length,
    activeUsers: mockUsers.filter(u => u.status === 'active').length,
    totalOrders: mockOrders.length,
    revenue: mockOrders.reduce((sum, order) => sum + order.total_amount, 0),
    totalDesigns: mockDesigns.length,
    pendingDesigns: mockDesigns.filter(d => d.status === 'pending').length,
    totalDownloads: mockDesigns.reduce((sum, design) => sum + design.downloads, 0),
    totalLikes: mockDesigns.reduce((sum, design) => sum + design.likes, 0)
  };

  const filteredUsers = mockUsers.filter(user =>
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredOrders = mockOrders.filter(order =>
    order.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.order_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredDesigns = mockDesigns.filter(design =>
    design.design_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    design.designer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h1>
          <p className="text-red-500 mb-4">You don't have permission to access the admin dashboard.</p>
          <Link href="/" className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-slate-900 dark:via-teal-800 dark:to-purple-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-purple-900 dark:text-cream-100">Admin Dashboard</h1>
            <p className="text-purple-700 dark:text-cream-200">Manage your Threadz platform</p>
          </div>
          <div className="flex gap-4">
            <Link href="/" className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
              View Site
            </Link>
            <button className="px-4 py-2 bg-purple-100 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-700 transition-colors">
              <Settings className="w-5 h-5 inline mr-2" />
              Settings
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-white dark:bg-gray-800 p-1 rounded-xl shadow-lg">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'users', label: 'Users', icon: Users },
            { id: 'orders', label: 'Orders', icon: ShoppingCart },
            { id: 'designs', label: 'Designs', icon: Package }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                activeTab === id
                  ? 'bg-purple-600 text-white'
                  : 'text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-700'
              }`}
            >
              <Icon className="w-5 h-5 mr-2" />
              {label}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-purple-400 dark:text-purple-300 w-5 h-5" />
            <input
              type="text"
              placeholder={`Search ${activeTab}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg bg-white dark:bg-gray-800 text-purple-900 dark:text-cream-100 placeholder-purple-500 dark:placeholder-purple-400"
            />
          </div>
        </div>

        {/* Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <Users className="w-8 h-8 text-purple-600" />
                <span className="text-sm text-green-600 font-semibold">+12%</span>
              </div>
              <h3 className="text-2xl font-bold text-purple-900 dark:text-cream-100">{stats.totalUsers}</h3>
              <p className="text-purple-700 dark:text-cream-200">Total Users</p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <ShoppingCart className="w-8 h-8 text-purple-600" />
                <span className="text-sm text-green-600 font-semibold">+8%</span>
              </div>
              <h3 className="text-2xl font-bold text-purple-900 dark:text-cream-100">{stats.totalOrders}</h3>
              <p className="text-purple-700 dark:text-cream-200">Total Orders</p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <DollarSign className="w-8 h-8 text-purple-600" />
                <span className="text-sm text-green-600 font-semibold">+15%</span>
              </div>
              <h3 className="text-2xl font-bold text-purple-900 dark:text-cream-100">${stats.revenue.toFixed(2)}</h3>
              <p className="text-purple-700 dark:text-cream-200">Total Revenue</p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <Package className="w-8 h-8 text-purple-600" />
                <span className="text-sm text-green-600 font-semibold">+20%</span>
              </div>
              <h3 className="text-2xl font-bold text-purple-900 dark:text-cream-100">{stats.totalDesigns}</h3>
              <p className="text-purple-700 dark:text-cream-200">Total Designs</p>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <div className="p-6 border-b border-purple-200 dark:border-purple-700">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100">User Management</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-purple-50 dark:bg-purple-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Joined</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Last Login</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-200 dark:divide-purple-700">
                  {filteredUsers.map((user) => (
                    <tr key={user.user_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-purple-900 dark:text-cream-100">{user.full_name}</div>
                          <div className="text-sm text-purple-500 dark:text-purple-400">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                        }`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          user.status === 'active' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
                            : user.status === 'inactive'
                            ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
                        }`}>
                          {user.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{user.created_at}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{user.last_login}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300 mr-2">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <div className="p-6 border-b border-purple-200 dark:border-purple-700">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100">Order Management</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-purple-50 dark:bg-purple-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Order ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Items</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Total</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-200 dark:divide-purple-700">
                  {filteredOrders.map((order) => (
                    <tr key={order.order_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-900 dark:text-cream-100">{order.order_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{order.user_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{order.items_count}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">${order.total_amount.toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          order.status === 'delivered' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
                            : order.status === 'shipped'
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200'
                            : order.status === 'processing'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200'
                            : order.status === 'pending'
                            ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{order.created_at}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300 mr-2">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300">
                          <Edit className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'designs' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <div className="p-6 border-b border-purple-200 dark:border-purple-700">
              <h2 className="text-xl font-semibold text-purple-900 dark:text-cream-100">Design Management</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-purple-50 dark:bg-purple-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Design</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Designer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Downloads</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Likes</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-purple-700 dark:text-purple-300 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-200 dark:divide-purple-700">
                  {filteredDesigns.map((design) => (
                    <tr key={design.design_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-purple-900 dark:text-cream-100">{design.design_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{design.designer_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          design.status === 'public' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
                            : design.status === 'private'
                            ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                            : design.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
                        }`}>
                          {design.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{design.downloads}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{design.likes}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 dark:text-purple-300">{design.created_at}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300 mr-2">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300 mr-2">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
