'use client';

import { useState, useEffect } from 'react';
import { DollarSign, Activity, CreditCard, Users } from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

import { DataCard } from '@/components/DataCard';
import { DataTable } from '@/components/DataTable';
import { Filters } from '@/components/Filters';
import { Overview } from '@/components/overview';
import { MainNav } from '@/components/main-nav';
import { Search } from '@/components/search';
import { UserNav } from '@/components/user-nav';

// --- MOCK API CALLS ---
const mockTransactions = [
  { id: 'TXN12345', amount: 250.75, status: 'completed', type: 'trade', timestamp: '2023-10-26T10:00:00Z' },
  { id: 'TXN12346', amount: 1500.00, status: 'completed', type: 'deposit', timestamp: '2023-10-26T11:30:00Z' },
  { id: 'TXN12347', amount: 89.99, status: 'pending', type: 'withdrawal', timestamp: '2023-10-26T12:05:00Z' },
  { id: 'TXN12348', amount: 50.00, status: 'failed', type: 'trade', timestamp: '2023-10-26T14:00:00Z' },
  { id: 'TXN12349', amount: 12000.00, status: 'completed', type: 'deposit', timestamp: '2023-10-25T09:00:00Z' },
  { id: 'TXN12350', amount: 345.50, status: 'completed', type: 'trade', timestamp: '2023-10-25T15:20:00Z' },
];

const mockMetrics = {
  totalVolume: 14190.24,
  totalTransactions: 6,
  pendingCount: 1,
  failedCount: 1,
};

const mockGraphData = [
  { name: 'Jan', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Feb', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Mar', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Apr', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'May', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Jun', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Jul', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Aug', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Sep', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Oct', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Nov', total: Math.floor(Math.random() * 5000) + 1000 },
  { name: 'Dec', total: Math.floor(Math.random() * 5000) + 1000 },
];

const getTransactions = async (filters: { status?: string; type?: string }) => {
  return new Promise(resolve => setTimeout(() => {
    let data = mockTransactions;
    if (filters.status) {
      data = data.filter(t => t.status === filters.status);
    }
    if (filters.type) {
      data = data.filter(t => t.type === filters.type);
    }
    resolve(data);
  }, 500));
};

const getMetrics = async () => {
  return new Promise(resolve => setTimeout(() => resolve(mockMetrics), 300));
};
// --- END MOCK API CALLS ---

export default function IncidentsPage() {
  const [transactions, setTransactions] = useState([]);
  const [metrics, setMetrics] = useState({ totalVolume: 0, totalTransactions: 0, pendingCount: 0, failedCount: 0 });
  const [filters, setFilters] = useState({});

  useEffect(() => {
    getMetrics().then(data => setMetrics(data as any));
  }, []);

  useEffect(() => {
    getTransactions(filters).then(data => setTransactions(data as any));
  }, [filters]);

  const handleFilterChange = (newFilters: { status?: string; type?: string }) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const resetFilters = () => {
    setFilters({});
  };

  return (
    <div className="bg-red-500 text-white p-4">
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex h-16 items-center px-4">
          <MainNav className="mx-6" />
          <div className="ml-auto flex items-center space-x-4">
            <Search />
            <UserNav />
          </div>
        </div>
      </div>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <div className="flex items-center space-x-2">
            <Filters onFilterChange={handleFilterChange} onReset={resetFilters} />
          </div>
        </div>
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analytics" disabled>Analytics</TabsTrigger>
            <TabsTrigger value="reports" disabled>Reports</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <DataCard
                title="Total Volume"
                value={`$${metrics.totalVolume.toLocaleString()}`}
                description="Total value of all transactions"
                icon={<DollarSign />}
              />
              <DataCard
                title="Total Transactions"
                value={`+${metrics.totalTransactions}`}
                description="Count of all transactions"
                icon={<Users />}
              />
              <DataCard
                title="Pending"
                value={`+${metrics.pendingCount}`}
                description="Transactions awaiting processing"
                icon={<CreditCard />}
              />
              <DataCard
                title="Failed"
                value={`+${metrics.failedCount}`}
                description="Transactions that did not complete"
                icon={<Activity />}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
              <Card className="col-span-4">
                <CardHeader>
                  <CardTitle>Overview</CardTitle>
                </CardHeader>
                <CardContent className="pl-2">
                  <Overview data={mockGraphData} />
                </CardContent>
              </Card>
              <div className="col-span-3">
                <DataTable data={transactions} />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}