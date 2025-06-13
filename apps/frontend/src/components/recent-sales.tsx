// Make sure to run: npx shadcn-ui@latest add avatar
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
  } from "@/src/components/ui/avatar"
  import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/src/components/ui/card";
  
  // Using your transaction data shape for a more relevant example
  interface Transaction {
    id: string;
    amount: number;
    // Let's add a user/customer name to make this component work
    customerName: string; 
    customerEmail: string;
  }
  
  // Mock data to demonstrate
  const recentTransactions: Transaction[] = [
      { id: 'TXN12345', amount: 250.75, customerName: "Olivia Martin", customerEmail: "olivia.martin@email.com" },
      { id: 'TXN12346', amount: 1500.00, customerName: "Jackson Lee", customerEmail: "jackson.lee@email.com" },
      { id: 'TXN12347', amount: 89.99, customerName: "Isabella Nguyen", customerEmail: "isabella.nguyen@email.com"},
      { id: 'TXN12348', amount: 50.00, customerName: "William Kim", customerEmail: "will@email.com" },
      { id: 'TXN12349', amount: 12000.00, customerName: "Sofia Davis", customerEmail: "sofia.davis@email.com" },
  ]
  
  
  export function RecentSales() {
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
          <CardDescription>
              A summary of the most recent transactions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-8">
              {recentTransactions.map(transaction => (
                   <div key={transaction.id} className="flex items-center">
                      <Avatar className="h-9 w-9">
                          <AvatarImage src={`/avatars/${Math.ceil(Math.random() * 5)}.png`} alt="Avatar" />
                          <AvatarFallback>{transaction.customerName.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <div className="ml-4 space-y-1">
                          <p className="text-sm font-medium leading-none">{transaction.customerName}</p>
                          <p className="text-sm text-muted-foreground">{transaction.customerEmail}</p>
                      </div>
                      <div className="ml-auto font-medium">{formatCurrency(transaction.amount)}</div>
                  </div>
              ))}
          </div>
        </CardContent>
      </Card>
    )
  }