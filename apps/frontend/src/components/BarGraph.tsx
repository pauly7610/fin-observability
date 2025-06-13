'use client';

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';

interface BarGraphProps {
    data: any[]; // Expects data in the format [{ name: 'Jan', total: 1200 }, ...]
    title: string;
}

export function BarGraph({ data, title }: BarGraphProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={data}>
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
            </CardContent>
        </Card>
    );
}