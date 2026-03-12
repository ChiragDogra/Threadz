'use client';

import { useState } from 'react';
import { Package, CreditCard, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function UserDashboard() {
  const [activeTab, setActiveTab] = useState('orders');
  const { user } = useAuthStore();

  const mockOrders = [
    {
      id: 'ORD-001',
      date: '2026-03-10',
      status: 'delivered',
      total: 129.97,
      items: 3
    }
  ];

  const tabs = [
    { id: 'orders', label: '📊 Orders', icon: Package },
    { id: 'profile', label: '👤 Profile', icon: Settings },
    { id: 'billing', label: '💳 Billing', icon: CreditCard }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-cream-100 mb-6">
            Welcome back, {user?.name}!
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
          
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button 
              onClick={() => {
                const { logout } = useAuthStore.getState();
                logout();
              }}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900 rounded-lg transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:col-span-3">
        {activeTab === 'orders' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-xl font-semibold text-slate-900 dark:text-cream-100 mb-6">Your Orders</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Order ID</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Total</th>
                    <th className="text-left py-3 px-4 font-medium text-slate-700 dark:text-cream-200">Items</th>
                  </tr>
                </thead>
                <tbody>
                  {mockOrders.map((order, index) => (
                    <tr key={order.id} className={`border-b border-gray-200 dark:border-gray-700 ${
                      index % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900' : ''
                    }`}>
                      <td className="py-3 px-4 text-slate-900 dark:text-cream-100">{order.id}</td>
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
