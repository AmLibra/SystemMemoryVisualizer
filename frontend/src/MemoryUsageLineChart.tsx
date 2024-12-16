import { useId, useMemo, useState } from "react";
import { MemoryUsageDataPoint } from "./Visualizer";
import * as d3 from "d3";

export function MemoryUsageLineChart({
  color,
  xScale,
  yScaleUsage,
  transform,
  maxTime,
  usage,
  accessor,
}: {
  color: string;
  xScale: d3.ScaleLinear<number, number>;
  yScaleUsage: d3.ScaleLinear<number, number>;
  transform: d3.ZoomTransform;
  maxTime: number;
  usage: MemoryUsageDataPoint[];
  accessor: (d: MemoryUsageDataPoint) => number;
}) {
  const gradientId = useId();

  const path = useMemo(
    () =>
      d3
        .line<MemoryUsageDataPoint>()
        .x(
          (d: MemoryUsageDataPoint) =>
            xScale(d.time) * transform.k + transform.x
        )
        .y((d: MemoryUsageDataPoint) => yScaleUsage(accessor(d)))
        .curve(d3.curveStepAfter)(usage) ?? "",
    [xScale, transform, yScaleUsage, accessor, usage]
  );

  if (usage.length === 0) return null;

  return (
    <>
      {/* Gradient definition */}
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={`${color}44`} />
          <stop offset="50%" stopColor={`${color}33`} />
          <stop offset="100%" stopColor={`${color}00`} />
        </linearGradient>
      </defs>

      {/* Line */}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
      />

      {/* Gradient background */}
      <path
        d={
          path +
          "L" +
          [
            xScale(maxTime) * transform.k + transform.x,
            yScaleUsage(0),
            xScale(usage[0].time) * transform.k + transform.x,
            yScaleUsage(0),
          ].join(",")
        }
        fill={`url(#${gradientId})`}
      />

      {/* Hover overlay */}
      <rect width="100%" height="100%" fill="none" pointerEvents="all" />
    </>
  );
}

export function virtualMemoryAccessor(d: MemoryUsageDataPoint) {
  return d.virtualMemoryUsage;
}

export function physicalMemoryAccessor(d: MemoryUsageDataPoint) {
  return d.physicalMemoryUsage;
}
