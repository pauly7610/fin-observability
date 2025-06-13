import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "@/src/components/ui/card"
  
  interface DataCardProps {
    title: string;
    value: string | number;
    description: string;
    icon: React.ReactNode; // Accept an icon component
  }
  
  export function DataCard({ title, value, description, icon }: DataCardProps) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {title}
          </CardTitle>
          {/* We render the icon passed as a prop */}
          <div className="h-4 w-4 text-muted-foreground">
            {icon}
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        </CardContent>
      </Card>
    )
  }