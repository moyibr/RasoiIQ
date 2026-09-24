'use client';

import { ForecastPoint } from '@/lib/api';
import { ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

interface ForecastChartProps {
  data: ForecastPoint[];
  category: string;
}

export default function ForecastChart({ data, category }: ForecastChartProps) {
  const formattedData = data.map((d) => {
    const date = new Date(d.date);
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return {
      ...d,
      displayDate: `${monthNames[date.getMonth()]} ${String(date.getDate()).padStart(2, '0')}`
    };
  });

  if (!data || data.length === 0) {
    return <div className="p-4 bg-red-50 text-red-600 rounded">No forecast data available from API.</div>;
  }

  return (
    <div className="w-full h-full flex flex-col">
      
      <div style={{ height: 350, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#232B38" />
            <XAxis dataKey="displayDate" stroke="#9AA3B2" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#9AA3B2" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val} kg`} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#232B38', border: '1px solid #1B212B', borderRadius: '4px', color: '#F2F0EA' }}
              itemStyle={{ color: '#F2F0EA' }}
              formatter={(value: number, name: string) => [`${value.toFixed(1)} kg`, name]}
            />
            <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ color: '#9AA3B2', fontSize: '12px' }} />
            
            <Line 
              type="monotone" 
              dataKey="confidence_upper" 
              stroke="#4FB5C7" 
              strokeOpacity={0.3}
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false} 
              name="Upper Bound" 
            />
            
            <Line 
              type="monotone" 
              dataKey="confidence_lower" 
              stroke="#4FB5C7" 
              strokeOpacity={0.3}
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false} 
              name="Lower Bound" 
            />
            
            <Line 
              type="monotone" 
              dataKey="predicted_kg" 
              stroke="#4FB5C7" 
              strokeWidth={2} 
              dot={false} 
              name="Predicted Demand" 
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
