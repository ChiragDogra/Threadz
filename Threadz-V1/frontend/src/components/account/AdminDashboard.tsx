'use client';

import { useState } from 'react';
import { Package, CreditCard, Settings, Users, TrendingUp } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('orders');
  const { user } = useAuthStore();

  const mockOrders = [
    {
      id: 'ORD-001',
      user: { name: 'John Doe', email: 'john@example.com' },
      items: 3,
      total: 129.97,
      status: 'delivered' as 'pending' | 'processing' | 'shipped' | 'delivered',
      date: '2026-03-10'
    },
    {
      id: 'ORD-002',
      user: { name: 'Jane Smith', email: 'jane@example.com' },
      items: 2,
      total: 89.99,
      status: 'shipped',
      date: '2026-03-08'
    },
    {
      id: 'ORD-003',
      user: { name: 'Bob Johnson', email: 'bob@example.com' },
      items: 5,
      total: 199.99,
      status: 'processing',
      date: '2026-03-05'
    }
  ];

  const mockProducts = [
    {
      id: 'PROD-001',
      name: 'Custom Tee',
      price: 29.99,
      stock: 50,
      category: 't-shirt'
    },
    {
      id: 'PROD-002',
      name: 'Premium Hoodie',
      price: 59.99,
      stock: 25,
      category: 'hoodie'
    }
  ];

  const mockUsers = [
    {
      id: 'USR-001',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'user',
      lastActive: '2026-03-10'
    },
    {
      id: 'USR-002',
      name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'user',
      lastActive: '2026-03-09'
    }
  ];

  const tabs = [
    { id: 'orders', label: '📦 Orders', icon: Package },
    { id: 'products', label: '📱 Products', icon: Settings },
    { id: 'users', label: '👥 Users', icon: Users },
    { id: 'analytics', label: '📊 Analytics', icon: TrendingUp }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      {/* Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-cream-100 mb-6">
            Admin Dashboard
          </h2>
          
          <nav className="space-y-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  activeTab === tab.id
                    ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-200'
                    : 'text-slate-600 dark:text-cream-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <tab.icon className="h-5 w-5" />
                <span className="text-sm font-medium">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:col-span-4">
        {activeTab === 'orders' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-slate-900 dark:text-cream-100">Orders Management</h3>
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors">
                  Export CSV
                </button>
                <button className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-slate-700 dark:text-cream-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors">
                  Filter Orders
                </button>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Order ID</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Customer</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Total</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Items</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mockOrders.map((order) => (
                    <tr key={order.id} className={`border-b border-gray-200 dark:border-gray-700 ${
                      order.status === 'delivered' ? 'bg-green-50 dark:bg-green-900' : ''
                    }`}>
                      <td className="py-3 px-4 text-slate-900 dark:text-cream-100">{order.id}</td>
                      <td className="py-3 px-4 text-slate-600 dark:text-cream-200">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center text-purple-700 dark:text-purple-200 text-xs font-bold">
                            {order.user.name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-medium text-slate-900 dark:text-cream-100">{order.user.name}</p>
                            <p className="text-sm text-slate-600 dark:text-cream-200">{order.user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-cream-200">{order.date}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                          order.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-900 dark:text-cream-100">${order.total}</td>
                      <td className="py-3 px-4 text-slate-600 dark:text-cream-200">{order.items}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <button className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-medium transition-colors">
                            View Details
                          </button>
                          <button className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white rounded text-xs font-medium transition-colors">
                            Track Order
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'products' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-slate-900 dark:text-cream-100">Products Management</h3>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors">
                Add Product
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mockProducts.map((product) => (
                <div key={product.id} className="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="text-lg font-semibold text-slate-900 dark:text-cream-100">{product.name}</h4>
                      <p className="text-sm text-slate-600 dark:text-cream-200">{product.category}</p>
                      <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">${product.price}</p>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        product.stock > 20 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {product.stock} in stock
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button className="flex-1 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors">
                      Edit
                    </button>
                    <button className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-slate-900 dark:text-cream-100">Users Management</h3>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors">
                Add User
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">User</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Email</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Role</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Last Active</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mockUsers.map((user) => (
                    <tr key={user.id} className="border-b border-gray-200 dark:border-gray-700">
                      <td className="py-3 px-4 text-slate-900 dark:text-cream-100">{user.name}</td>
                      <td className="py-3 px-4 text-slate-600 dark:text-cream-200">{user.email}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-cream-200">{user.lastActive}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <button className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-medium transition-colors">
                            Edit
                          </button>
                          <button className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-medium transition-colors">
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-xl font-semibold text-slate-900 dark:text-cream-100 mb-6">Analytics Overview</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 p-6 rounded-lg border border-purple-200 dark:border-purple-700">
                <div className="text-center">
                  <Package className="h-12 w-12 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
                  <h4 className="text-2xl font-bold text-slate-900 dark:text-cream-100">1,234</h4>
                  <p className="text-slate-600 dark:text-cream-200">Total Orders</p>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-orange-100 to-yellow-100 dark:from-orange-900 dark:to-yellow-900 p-6 rounded-lg border border-orange-200 dark:border-orange-700">
                <div className="text-center">
                  <CreditCard className="h-12 w-12 text-orange-600 dark:text-orange-400 mx-auto mb-4" />
                  <h4 className="text-2xl font-bold text-slate-900 dark:text-cream-100">$45,678</h4>
                  <p className="text-slate-600 dark:text-cream-200">Total Revenue</p>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-green-100 to-blue-100 dark:from-green-900 dark:to-blue-900 p-6 rounded-lg border border-green-200 dark:border-green-700">
                <div className="text-center">
                  <Users className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
                  <h4 className="text-2xl font-bold text-slate-900 dark:text-cream-100">567</h4>
                  <p className="text-slate-600 dark:text-cream-200">Active Users</p>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-yellow-100 to-orange-100 dark:from-yellow-900 dark:to-orange-900 p-6 rounded-lg border border-yellow-200 dark:border-yellow-700">
                <div className="text-center">
                  <TrendingUp className="h-12 w-12 text-yellow-600 dark:text-yellow-400 mx-auto mb-4" />
                  <h4 className="text-2xl font-bold text-slate-900 dark:text-cream-100">23</h4>
                  <p className="text-slate-600 dark:text-cream-200">Products Sold</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
