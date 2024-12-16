import { useMeasure } from "@uidotdev/usehooks";
import * as d3 from "d3";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  MemoryUsageLineChart,
  physicalMemoryAccessor,
  virtualMemoryAccessor,
} from "./MemoryUsageLineChart";
import { createPortal } from "react-dom";

export type ByteAddressUnit = number;
export type Time = number;

/**
 * 48 bits here comes from the fact that current AMD64 CPUs support
 * 48-bit virtual addresses (not 64-bit).
 */
const ADDRESS_MAX: ByteAddressUnit = 2 ** 48 - 1;

export type Allocation = {
  startAddress: ByteAddressUnit;
  size: ByteAddressUnit;

  allocatedAt: Time;
  freedAt: Time | null;

  fill: string;
  command: string;
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
  minAddress: ByteAddressUnit | null;
  maxAddress: ByteAddressUnit | null;
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
  minAddress,
  maxAddress,
  maxTime,
  width,
  height,
  usage,
  availablePhysicalMemory,
}: {
  allocations: Allocation[];
  minAddress: ByteAddressUnit | null;
  maxAddress: ByteAddressUnit | null;
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
  const yScale = useMemo(
    () =>
      d3
        .scaleLinear()
        .domain([
          minAddress === null ? 0 : minAddress,
          maxAddress === null ? ADDRESS_MAX : maxAddress,
        ])
        .range([0, height - margin.top - margin.bottom]),
    [minAddress, maxAddress]
  );

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

  const ticks = useAddressTicks(height, transform, yScale, minAddress, maxAddress);

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
              <AllocationRect
                key={index}
                allocation={allocation}
                transform={transform}
                xScale={xScale}
                yScale={yScale}
                maxTime={maxTime}
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
              <MemoryUsageLines
                usage={usage}
                availablePhysicalMemory={availablePhysicalMemory}
                transform={transform}
                maxTime={maxTime}
                xScale={xScale}
              />
            </g>
          </g>
        </g>
      </svg>
    </>
  );
}

function MemoryUsageLines({
  usage,
  availablePhysicalMemory,
  transform,
  maxTime,
  xScale,
}: {
  usage: MemoryUsageDataPoint[];
  availablePhysicalMemory: ByteAddressUnit;
  transform: d3.ZoomTransform;
  maxTime: Time;
  xScale: d3.ScaleLinear<number, number>;
}) {
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

  const [hoverValue, setHoverValue] = useState<{
    x: number;
    yVirtual: number;
    yPhysical: number;
  } | null>(null);

  return (
    <g
      onMouseMove={(event) => {
        const [mouseX] = d3.pointer(event);
        const scaledX = (mouseX - transform.x) / transform.k; // Adjust for zoom and pan

        // Find the closest data point using bisector
        const bisect = d3.bisector((d: MemoryUsageDataPoint) => d.time).right;
        const index = bisect(usage, xScale.invert(scaledX));
        const closestPoint = usage[index] ?? null; // Safe fallback if out of bounds

        if (closestPoint) {
          setHoverValue({
            x: xScale(closestPoint.time) * transform.k + transform.x,
            yVirtual: closestPoint.virtualMemoryUsage,
            yPhysical: closestPoint.physicalMemoryUsage,
          });
        } else {
          setHoverValue(null);
        }
      }}
      onMouseLeave={() => setHoverValue(null)}
    >
      <MemoryUsageLineChart
        xScale={xScale}
        yScaleUsage={yScaleUsage}
        transform={transform}
        maxTime={maxTime}
        usage={usage}
        color="#5e5ce6"
        accessor={virtualMemoryAccessor}
      />
      <MemoryUsageLineChart
        xScale={xScale}
        yScaleUsage={yScaleUsage}
        transform={transform}
        maxTime={maxTime}
        usage={usage}
        color="#ffd50b"
        accessor={physicalMemoryAccessor}
      />

      {/* Hover marker (vertical line) */}
      {hoverValue !== null && (
        <>
          {/* Vertical Line at hoverX */}
          <line
            x1={hoverValue.x}
            x2={hoverValue.x}
            y1={-10}
            y2={USAGE_CHART_HEIGHT}
            stroke="#cccccc"
            strokeWidth={2}
            strokeDasharray="5,5"
            style={{ pointerEvents: "none" }}
          />

          <text
            x={hoverValue.x + 10}
            y={4}
            textAnchor="left"
            fontSize={14}
            fill="#5e5ce6"
            style={{ pointerEvents: "none" }}
          >
            {hoverValue.yVirtual.toLocaleString()} virtual pages
          </text>
          <text
            x={hoverValue.x + 10}
            y={22}
            textAnchor="left"
            fontSize={14}
            fill="#ffd50b"
            style={{ pointerEvents: "none" }}
          >
            {hoverValue.yPhysical.toLocaleString()} physical pages
          </text>
        </>
      )}
    </g>
  );
}

function AllocationRect({
  allocation,
  transform,
  xScale,
  yScale,
  maxTime,
}: {
  allocation: Allocation;
  transform: d3.ZoomTransform;
  xScale: d3.ScaleLinear<number, number>;
  yScale: d3.ScaleLinear<number, number>;
  maxTime: Time;
}) {
  const allocRef = useRef<SVGRectElement>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  useEffect(() => {
    if (tooltipPosition === null || !allocRef.current) return;
    setTooltipPosition(allocRef.current.getBoundingClientRect());
  }, [xScale, yScale, transform]);

  return (
    <>
      <rect
        ref={allocRef}
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
        height={Math.max(1, transform.k * (yScale(allocation.startAddress + allocation.size) - yScale(allocation.startAddress)))}
        fill={allocation.fill}
        onMouseOver={() => {
          setTooltipPosition(allocRef.current?.getBoundingClientRect() ?? null);
        }}
        onMouseOut={() => setTooltipPosition(null)}
        onMouseLeave={() => setTooltipPosition(null)}
      />

      {tooltipPosition !== null &&
        createPortal(
          <div
            className="tooltip"
            style={{
              left: `${Math.max(tooltipPosition.x, 130)}px`,
              top: `${Math.max(tooltipPosition.y + 10, 70)}px`,
              borderColor: allocation.fill,
            }}
          >
            <h3 className="tooltip-address">
              0x
              {allocation.startAddress
                .toString(16)
                .toUpperCase()
                .padStart(12, "0")}{" "}
              – 0x
              {(allocation.startAddress + allocation.size)
                .toString(16)
                .toUpperCase()
                .padStart(12, "0")}
            </h3>

            <div className="tooltip-stats">
              <div>
                <h4>Size</h4>
                <p>{humanFileSize(allocation.size)}</p>
              </div>
              <div>
                <h4>Command</h4>
                <p>{allocation.command}</p>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}

function useAddressTicks(
  height: number,
  transform: d3.ZoomTransform,
  yScale: d3.ScaleLinear<number, number>,
  minAddress: ByteAddressUnit | null,
  maxAddress: ByteAddressUnit | null
): { value: number; type: "default" | "minor" | "major" }[] {
  return useMemo(() => {
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
      2 ** Math.floor(Math.log2((((maxAddress ?? ADDRESS_MAX) - (minAddress ?? 0)) / zoomedHeight / VALUES_PER_PIXEL)));

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
  }, [height, transform, yScale]);
}

function largestMultipleUnder(multiplier: number, x: number) {
  return Math.floor((x - 1) / multiplier) * multiplier;
}

function clamp(min: number, value: number, max: number): number {
  return Math.min(Math.max(min, value), max);
}

/**
 * Format bytes as human-readable text.
 *
 * Source: https://stackoverflow.com/a/14919494/4652564
 *         (by Mark Penner, CC BY-SA 4.0)
 *
 * @param bytes Number of bytes.
 * @param si True to use metric (SI) units, aka powers of 1000. False to use
 *           binary (IEC), aka powers of 1024.
 * @param dp Number of decimal places to display.
 *
 * @return Formatted string.
 */
function humanFileSize(bytes: number, si = false, dp = 1) {
  const thresh = si ? 1000 : 1024;

  if (Math.abs(bytes) < thresh) {
    return bytes + " B";
  }

  const units = si
    ? ["kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    : ["KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"];
  let u = -1;
  const r = 10 ** dp;

  do {
    bytes /= thresh;
    ++u;
  } while (
    Math.round(Math.abs(bytes) * r) / r >= thresh &&
    u < units.length - 1
  );

  return bytes.toFixed(dp) + " " + units[u];
}
