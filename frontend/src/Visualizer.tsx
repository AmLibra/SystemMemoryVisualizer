import { useMeasure } from "@uidotdev/usehooks";
import * as d3 from "d3";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  MemoryUsageLineChart,
  physicalMemoryAcessor,
  virtualMemoryAcessor,
} from "./MemoryUsageLineChart";

export type ByteAddressUnit = number;
export type Time = number;

/**
 * 48 bits here comes from the fact that current AMD64 CPUs support
 * 48-bit virtual addresses (not 64-bit).
 */
export const ADDRESS_MAX: ByteAddressUnit = 2 ** 48 - 1;

export type Allocation = {
  startAddress: ByteAddressUnit;
  size: ByteAddressUnit;

  allocatedAt: Time;
  freedAt: Time | null;

  fill: string;
};

export type MemoryUsageDataPoint = {
  time: Time;
  virtualMemoryUsage: ByteAddressUnit;
  physicalMemoryUsage: ByteAddressUnit;
};

function formatAddress(pageNumber: ByteAddressUnit) {
  const UINT48_DIGITS = 12;
  return pageNumber.toString(16).toUpperCase().padStart(UINT48_DIGITS, "0");
}

export default function Visualizer(props: {
  allocations: Allocation[];
  maxTime: Time;
  usage: MemoryUsageDataPoint[];
  availablePhysicalMemory: ByteAddressUnit;
}) {
  const [ref, { width, height }] = useMeasure();

  return (
    <div className="chart-wrapper" ref={ref}>
      {width !== null && height !== null && (
        <VisualizerContents {...props} width={width} height={height} />
      )}
    </div>
  );
}

const USAGE_CHART_PADDING = 15;
const USAGE_CHART_HEIGHT = 120;

const USAGE_CHART_FULL_HEIGHT = USAGE_CHART_HEIGHT + USAGE_CHART_PADDING * 2;

const margin = {
  top: 75,
  right: 5,
  bottom: 20 + USAGE_CHART_FULL_HEIGHT,
  left: 135,
} as const;

function VisualizerContents({
  allocations,
  maxTime,
  width,
  height,
  usage,
  availablePhysicalMemory,
}: {
  allocations: Allocation[];
  maxTime: Time;
  width: number;
  height: number;
  usage: MemoryUsageDataPoint[];
  availablePhysicalMemory: ByteAddressUnit;
}) {
  const xScale = d3
    .scaleLinear()
    .domain([0, maxTime])
    .range([0, width - margin.left - margin.right]);
  const yScale = d3
    .scaleLinear()
    .domain([0, ADDRESS_MAX])
    .range([0, height - margin.top - margin.bottom]);

  const yScaleUsage = d3
    .scaleLinear()
    .domain([
      0,
      Math.max(
        ...usage.map((u) => u.physicalMemoryUsage),
        ...usage.map((u) => u.virtualMemoryUsage),
        availablePhysicalMemory
      ),
    ])
    .range([USAGE_CHART_HEIGHT, 0]);

  const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);

  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 400_000_000_000])
      .translateExtent([
        [0, 0],
        [width, height],
      ])
      .on("zoom", (event: d3.D3ZoomEvent<SVGGElement, any>) => {
        setTransform(event.transform.translate(0, 0));
      });

    svg.call(zoom);
  }, [width, height]);

  const ticks = useAddressTicks(height, transform);

  return (
    <>
      <svg className="y-axis-ticks">
        {/* Y axis ticks */}
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          {ticks.map(({ value, type }) => (
            <text
              key={value}
              x={-22}
              y={transform.applyY(yScale(value))}
              dominantBaseline="middle"
              textAnchor="end"
              fill={type === "major" ? "#999" : "#666"}
              fontSize={12}
              letterSpacing={0.5}
            >
              {formatAddress(value)}
            </text>
          ))}
        </g>
      </svg>

      <svg className="chart" ref={svgRef}>
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          <g>
            {/* Grid lines */}
            {ticks
              .filter(({ type }) => type !== "default")
              .map(({ value, type }) => {
                const height = yScale(value);
                return (
                  <line
                    key={value}
                    x1={transform.applyX(-margin.left)}
                    x2={transform.applyX(width - margin.right)}
                    y1={transform.applyY(height)}
                    y2={transform.applyY(height)}
                    stroke={type === "major" ? "#2a2a2a" : "#222"}
                    strokeWidth={2}
                    strokeDasharray={type === "minor" ? "4 4" : undefined}
                  />
                );
              })}
          </g>

          <g>
            {/* Allocations */}
            {allocations.map((allocation, index) => (
              <rect
                key={index}
                x={transform.applyX(xScale(allocation.allocatedAt))}
                width={
                  transform.k *
                  Math.max(
                    0,
                    xScale(allocation.freedAt ?? maxTime) -
                      xScale(allocation.allocatedAt)
                  )
                }
                y={transform.applyY(yScale(allocation.startAddress))}
                height={Math.max(
                  1,
                  transform.k * yScale(allocation.size)
                )}
                fill={allocation.fill}
              />
            ))}
          </g>

          <g>
            <rect
              x={0 - margin.left}
              y={height - margin.top - USAGE_CHART_FULL_HEIGHT}
              width={width}
              height={USAGE_CHART_FULL_HEIGHT}
              fill="#191919"
            />

            <line
              x1={0 - margin.left}
              x2={width}
              y1={height - margin.top - USAGE_CHART_FULL_HEIGHT + 0.5}
              y2={height - margin.top - USAGE_CHART_FULL_HEIGHT + 0.5}
              stroke="rgba(255, 255, 255, .1)"
              strokeWidth={1}
            />

            <g
              transform={`translate(0, ${
                height - margin.top - USAGE_CHART_HEIGHT - USAGE_CHART_PADDING
              })`}
            >
              <MemoryUsageLineChart
                xScale={xScale}
                yScaleUsage={yScaleUsage}
                transform={transform}
                maxTime={maxTime}
                usage={usage}
                color="#5e5ce6"
                accessor={virtualMemoryAcessor}
              />
              <MemoryUsageLineChart
                xScale={xScale}
                yScaleUsage={yScaleUsage}
                transform={transform}
                maxTime={maxTime}
                usage={usage}
                color="#ffd50b"
                accessor={physicalMemoryAcessor}
              />
            </g>
          </g>
        </g>
      </svg>
    </>
  );
}

function useAddressTicks(
  height: number,
  transform: d3.ZoomTransform
): { value: number; type: "default" | "minor" | "major" }[] {
  return useMemo(() => {
    const yScale = d3
      .scaleLinear()
      .domain([0, ADDRESS_MAX])
      .range([0, height - margin.top - margin.bottom]);
    const minVisibleAddress: ByteAddressUnit = clamp(
      0,
      Math.floor(yScale.invert(transform.invertY(0))),
      ADDRESS_MAX
    );
    const maxVisibleAddress: ByteAddressUnit = clamp(
      0,
      Math.floor(
        yScale.invert(transform.invertY(height - margin.top - margin.bottom))
      ),
      ADDRESS_MAX
    );

    const zoomedHeight = (height - margin.top - margin.bottom) * transform.k;

    const VALUES_PER_PIXEL = 1 / 50;

    const increment =
      2 ** Math.floor(Math.log2(ADDRESS_MAX / zoomedHeight / VALUES_PER_PIXEL));

    const result: { value: number; type: "default" | "minor" | "major" }[] = [];
    for (
      let value = largestMultipleUnder(increment, minVisibleAddress);
      value < maxVisibleAddress;
      value += increment
    ) {
      const modulo = value % (increment * 0x4);

      result.push({
        value,
        type:
          modulo === 0
            ? "major"
            : modulo === increment * 0x2
            ? "minor"
            : "default",
      });
    }

    return result;
  }, [height, transform]);
}

function largestMultipleUnder(multiplier: number, x: number) {
  return Math.floor((x - 1) / multiplier) * multiplier;
}

function clamp(min: number, value: number, max: number): number {
  return Math.min(Math.max(min, value), max);
}
