# `components/Charts.tsx` — ECharts 4종 그대로 복사

```tsx
"use client";
import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const ink = "#1a1a1a";
const inkMuted = "#6a6a6a";
const paper = "#F7F2E6";
const rust = "#A0522D";
const slate = "#435B6C";
const border = "rgba(26,26,26,0.12)";

const baseGrid = {
  left: 56,
  right: 24,
  top: 24,
  bottom: 36,
  containLabel: true,
};
const baseAxis = {
  axisLine: { lineStyle: { color: border } },
  axisTick: { show: false },
  axisLabel: {
    color: inkMuted,
    fontFamily: "Pretendard Variable, sans-serif",
    fontSize: 11,
  },
  splitLine: { lineStyle: { color: border, type: "dashed" } },
};

export function SerpChart({
  data,
}: {
  data: { month: string; value: number }[];
}) {
  return (
    <ReactECharts
      style={{ height: 280 }}
      opts={{ renderer: "svg" }}
      option={{
        backgroundColor: paper,
        grid: baseGrid,
        tooltip: { trigger: "axis" },
        xAxis: {
          type: "category",
          data: data.map((d) => d.month),
          ...baseAxis,
        },
        yAxis: { type: "value", ...baseAxis },
        series: [
          {
            type: "line",
            data: data.map((d) => d.value),
            smooth: true,
            symbol: "circle",
            symbolSize: 6,
            lineStyle: { color: rust, width: 2 },
            itemStyle: { color: rust },
            areaStyle: { color: "rgba(160,82,45,0.10)" },
          },
        ],
      }}
    />
  );
}

export function PriceDistChart({
  data,
}: {
  data: { bucket: string; count: number }[];
}) {
  return (
    <ReactECharts
      style={{ height: 280 }}
      opts={{ renderer: "svg" }}
      option={{
        backgroundColor: paper,
        grid: baseGrid,
        tooltip: { trigger: "axis" },
        xAxis: {
          type: "category",
          data: data.map((d) => d.bucket),
          ...baseAxis,
        },
        yAxis: { type: "value", ...baseAxis },
        series: [
          {
            type: "bar",
            data: data.map((d) => d.count),
            itemStyle: { color: slate },
            barWidth: 28,
          },
        ],
      }}
    />
  );
}

export function RevenueChart({
  data,
}: {
  data: { year: string; value: number }[];
}) {
  return (
    <ReactECharts
      style={{ height: 280 }}
      opts={{ renderer: "svg" }}
      option={{
        backgroundColor: paper,
        grid: baseGrid,
        tooltip: {
          trigger: "axis",
          valueFormatter: (v: number) => v.toLocaleString() + " 억",
        },
        xAxis: { type: "category", data: data.map((d) => d.year), ...baseAxis },
        yAxis: {
          type: "value",
          ...baseAxis,
          axisLabel: {
            ...baseAxis.axisLabel,
            formatter: (v: number) => v.toLocaleString(),
          },
        },
        series: [
          {
            type: "bar",
            data: data.map((d, i) => ({
              value: d.value,
              itemStyle: { color: i === data.length - 1 ? rust : slate },
            })),
            barWidth: 32,
          },
        ],
      }}
    />
  );
}

export function SocialChart({
  data,
}: {
  data: { platform: string; followers: number; growth: number }[];
}) {
  return (
    <ReactECharts
      style={{ height: 280 }}
      opts={{ renderer: "svg" }}
      option={{
        backgroundColor: paper,
        grid: { ...baseGrid, right: 64 },
        tooltip: { trigger: "axis" },
        legend: {
          top: 0,
          right: 0,
          textStyle: {
            color: ink,
            fontFamily: "Pretendard Variable",
            fontSize: 11,
          },
        },
        xAxis: {
          type: "category",
          data: data.map((d) => d.platform),
          ...baseAxis,
        },
        yAxis: [
          {
            type: "value",
            name: "팔로워",
            ...baseAxis,
            axisLabel: {
              ...baseAxis.axisLabel,
              formatter: (v: number) => (v / 1000).toFixed(0) + "K",
            },
          },
          {
            type: "value",
            name: "성장률 %",
            ...baseAxis,
            splitLine: { show: false },
          },
        ],
        series: [
          {
            type: "bar",
            name: "팔로워",
            data: data.map((d) => d.followers),
            itemStyle: { color: slate },
            barWidth: 24,
            yAxisIndex: 0,
          },
          {
            type: "line",
            name: "월간 성장 %",
            data: data.map((d) => d.growth),
            itemStyle: { color: rust },
            lineStyle: { width: 2 },
            symbol: "circle",
            symbolSize: 7,
            yAxisIndex: 1,
          },
        ],
      }}
    />
  );
}
```
