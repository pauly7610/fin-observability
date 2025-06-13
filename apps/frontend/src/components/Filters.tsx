'use client'; // Keep this as it uses client-side hooks

import { Button } from "@/src/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/src/components/ui/select";

interface FiltersProps {
  onFilterChange: (filters: { status?: string; type?: string }) => void;
  onReset: () => void;
}

export function Filters({ onFilterChange, onReset }: FiltersProps) {
  // We can manage the state internally to call the parent prop
  const handleStatusChange = (value: string) => {
    onFilterChange({ status: value === 'all' ? undefined : value });
  };

  const handleTypeChange = (value: string) => {
    onFilterChange({ type: value === 'all' ? undefined : value });
  };

  return (
    <div className="flex items-center space-x-4">
      <div className="flex items-center space-x-2">
        <label htmlFor="status-select" className="text-sm font-medium">Status</label>
        <Select onValueChange={handleStatusChange} defaultValue="all">
          <SelectTrigger className="w-[180px]" id="status-select">
            <SelectValue placeholder="Filter by status..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center space-x-2">
         <label htmlFor="type-select" className="text-sm font-medium">Type</label>
        <Select onValueChange={handleTypeChange} defaultValue="all">
          <SelectTrigger className="w-[180px]" id="type-select">
            <SelectValue placeholder="Filter by type..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="deposit">Deposit</SelectItem>
            <SelectItem value="withdrawal">Withdrawal</SelectItem>
            <SelectItem value="trade">Trade</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button onClick={onReset} variant="outline">Reset</Button>
    </div>
  );
}