import { useEffect, useRef, useState } from "react";
import Visualizer, {
  Allocation,
  MemoryUsageDataPoint,
  ByteAddressUnit,
} from "./Visualizer";
import { COLORS } from "./util/colors";

export type AllocationId = number;
type Time = number;
type ProcessId = number;

function getQueryParam(key: string): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

type IncomingMessage =
  | {
      type: "add";
      time: Time;
      allocation: {
        id: AllocationId;
        pid: ProcessId;
        startAddr: number;
        endAddr: number;
        size: number;
        pages: number;
        comm: string;
      };
    }
  | {
      type: "remove";
      time: Time;
      id: AllocationId;
      pid: ProcessId;
    }
  | {
      type: "usage";
      time: Time;
      rss: number;
      vm: number;
    }
  | { type: "time"; time: Time }
  | { type: "catchup"; messages: IncomingMessage[] };

export default function App() {
  const [allocations, setAllocations] = useState<
    Record<ProcessId, Record<AllocationId, Allocation>>
  >({});

  const [minAddress, setMinAddress] = useState<ByteAddressUnit | null>(null);
  const [maxAddress, setMaxAddress] = useState<ByteAddressUnit | null>(null);

  const [processNames, setProcessNames] = useState<{
    [processId: ProcessId]: Set<string>;
  }>({});
  const [selectedProcess, setSelectedProcess] = useState<ProcessId | "all">(
    "all"
  );

  const [maxTime, setMaxTime] = useState<Time>(1);
  const [usages, addUsage] = useState<MemoryUsageDataPoint[]>([]);

  const initialized = useRef(false);
  useEffect(() => {
    if (initialized.current) {
      return;
    }
    initialized.current = true;

    const port =
      getQueryParam("port") || import.meta.env.REACT_APP_PORT || "8080";
    const socket = new WebSocket(`ws://localhost:${port}`);
    console.log(`Connecting to WebSocket server at ws://localhost:${port}`);

    function handleMessage(message: IncomingMessage) {
      const { type } = message;

      if (type !== "catchup") {
        setMaxTime((t) => Math.max(t, message.time));
      }

      switch (type) {
        case "add":
          setMinAddress((min) =>
            min === null
              ? message.allocation.startAddr
              : Math.min(min, message.allocation.startAddr)
          );
          setMaxAddress((max) =>
            max === null
              ? message.allocation.endAddr
              : Math.max(max, message.allocation.endAddr)
          );

          setProcessNames((previousNames) => ({
            ...previousNames,
            [message.allocation.pid]: new Set([
              ...(previousNames[message.allocation.pid] ?? []),
              message.allocation.comm,
            ]),
          }));

          setAllocations((previousAllocations) => {
            const { id, pid } = message.allocation;

            return {
              ...previousAllocations,
              [pid]: {
                ...(previousAllocations[pid] ?? {}),
                [id]: {
                  startAddress: message.allocation.startAddr,
                  size:
                    message.allocation.endAddr - message.allocation.startAddr,
                  allocatedAt: message.time,
                  freedAt: null,
                  fill: COLORS[Math.floor(Math.random() * COLORS.length)],
                  command: message.allocation.comm,
                },
              },
            };
          });
          break;
        case "remove":
          setAllocations((previousAllocations) => {
            const { id, pid } = message;
            return {
              ...previousAllocations,
              [pid]: {
                ...previousAllocations[pid],
                [id]: {
                  ...previousAllocations[pid][id],
                  freedAt: message.time,
                },
              },
            };
          });
          break;
        case "usage":
          addUsage((usages) => [
            ...usages,
            {
              time: message.time,
              virtualMemoryUsage: message.vm,
              physicalMemoryUsage: message.rss,
            },
          ]);
          break;
        case "time":
          setMaxTime((t) => Math.max(t, message.time));
          break;
        case "catchup":
          message.messages.forEach(handleMessage);
          break;
        default:
          const impossibleType: never = type;
          throw new Error("Invalid message type: " + impossibleType);
      }
    }

    socket.onmessage = (event) => {
      handleMessage(JSON.parse(event.data));
    };
  }, []);
  return (
    <div className="app">
      <nav className="nav">
        <h1>Memory Allocation Visualizer</h1>

        <label className="process-selector">
          <span className="sr-only">Process</span>
          <select
            onChange={(e) => {
              setSelectedProcess(
                e.target.value === "all" ? "all" : parseInt(e.target.value)
              );
            }}
          >
            <option disabled>Processes</option>
            <option value="all">All processes</option>
            {Object.entries(processNames).map(([pid, names]) => (
              <option key={pid} value={pid}>
                {pid} ({Array.from(names).join(", ")})
              </option>
            ))}
          </select>
        </label>
      </nav>

      <Visualizer
        allocations={
          selectedProcess === "all"
            ? Object.fromEntries(
                Object.values(allocations).flatMap((allocationsById) =>
                  Object.entries(allocationsById)
                )
              )
            : allocations[selectedProcess] ?? {}
        }
        minAddress={minAddress}
        maxAddress={maxAddress}
        maxTime={maxTime}
        usage={usages}
      />
    </div>
  );
}
