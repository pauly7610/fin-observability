"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from "recharts"

interface OverviewProps {
  data: any[]
}

export function Overview({ data }: OverviewProps) {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="name"
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#888888"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `$${value}`}
        />
        <Tooltip />
        <Legend />
        <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}