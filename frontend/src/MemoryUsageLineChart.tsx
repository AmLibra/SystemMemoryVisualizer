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
  const [hoverValue, setHoverValue] = useState<number | null>(null);
  const [hoverX, setHoverX] = useState<number | null>(null);

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

  // Handle mouse move to calculate hover value
  const handleMouseMove = (event: React.MouseEvent<SVGRectElement, MouseEvent>) => {
    const [mouseX] = d3.pointer(event);
    const scaledX = (mouseX - transform.x) / transform.k; // Adjust for zoom and pan

    // Find the closest data point using bisector
    const bisect = d3.bisector((d: MemoryUsageDataPoint) => d.time).right;
    const index = bisect(usage, xScale.invert(scaledX));
    const closestPoint = usage[index] || null; // Safe fallback if out of bounds

    if (closestPoint) {
      setHoverValue(accessor(closestPoint));
      setHoverX(xScale(closestPoint.time) * transform.k + transform.x);
    } else {
      setHoverValue(null);
      setHoverX(null);
    }
  };

  const handleMouseLeave = () => {
    setHoverValue(null);
    setHoverX(null);
  };

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
            xScale(0) * transform.k + transform.x,
            yScaleUsage(0),
          ].join(",")
        }
        fill={`url(#${gradientId})`}
      />

      {/* Hover overlay */}
      <rect
        width="100%"
        height="100%"
        fill="none"
        pointerEvents="all"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />

      {/* Hover marker and text */}
      {hoverX !== null && hoverValue !== null && (
        <>
          <circle
            cx={hoverX}
            cy={yScaleUsage(hoverValue)}
            r={5}
            fill={color}
          />
          <text
            x={hoverX}
            y={yScaleUsage(hoverValue) - 10}
            fill={color}
            textAnchor="middle"
            fontSize={12}
          >
            {formatValue(hoverValue)}
          </text>
        </>
      )}
    </>
  );
}


export function virtualMemoryAcessor(d: MemoryUsageDataPoint) {
  return d.virtualMemoryUsage;
}

export function physicalMemoryAcessor(d: MemoryUsageDataPoint) {
    return d.physicalMemoryUsage;
}

  // Helper function to format values
const formatValue = (value: number): string => {
  // Group digits in sets of 3, and add "B" at the end
  return value.toLocaleString() + " pages";
};
