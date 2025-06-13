import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  } from "@/src/components/ui/table"
  import { Card, CardHeader, CardTitle, CardContent } from "@/src/components/ui/card";
  
  // Assuming your transaction data has this shape
  interface Transaction {
    id: string;
    amount: number;
    status: 'completed' | 'pending' | 'failed';
    type: 'deposit' | 'withdrawal' | 'trade';
    timestamp: string;
  }
  
  interface DataTableProps {
    data: Transaction[];
  }
  
  export function DataTable({ data }: DataTableProps) {
    const formatCurrency = (amount: number) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(amount);
    };
  
    return (
      <Card>
         <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transaction ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell className="font-medium">{transaction.id}</TableCell>
                  <TableCell className="capitalize">{transaction.type}</TableCell>
                  <TableCell className="capitalize">{transaction.status}</TableCell>
                  <TableCell className="text-right">{formatCurrency(transaction.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  }