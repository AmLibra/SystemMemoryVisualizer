import { useEffect, useRef, useState } from "react";
import Visualizer, {Allocation, ADDRESS_MAX, MemoryUsageDataPoint} from "./Visualizer";
import { COLORS } from "./util/colors";

type AllocationId = number;
type Time = number;

type IncomingMessage =
  | {
      type: "add";
      time: Time;
      allocation: {
        id: AllocationId;
        pid: number;
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
      pid: number;
    }
  | {
      type: "usage";
      time: Time;
      pid: number;
      rss: number;
      vm: number;
    }
  | { type: "time"; time: Time }
  | { type: "catchup"; messages: IncomingMessage[] };

export default function App() {
  const [allocations, setAllocations] = useState<
    Record<AllocationId, Allocation>
  >({});
  const [maxTime, setMaxTime] = useState<Time>(1);
  const [usages, addUsage] = useState<MemoryUsageDataPoint[]>([]);

  const initialized = useRef(false);
  useEffect(() => {
    if (initialized.current) {
      return;
    }
    initialized.current = true;

    const socket = new WebSocket("ws://localhost:8000");

    function handleMessage(message: IncomingMessage) {
      const { type } = message;

      if (type !== "catchup") {
        setMaxTime((t) => Math.max(t, message.time));
      }

      switch (type) {
        case "add":
          setAllocations((allocations) => {
            const { id } = message.allocation;
            return {
              ...allocations,
              [id]: {
                startAddress: message.allocation.startAddr,
                size: message.allocation.endAddr - message.allocation.startAddr,
                allocatedAt: message.time,
                freedAt: null,
                fill: COLORS[Math.floor(Math.random() * COLORS.length)]
              },
            };
          });
          break;
        case "remove":
          setAllocations((allocations) => {
            const { id } = message;
            return {
              ...allocations,
              [id]: {
                ...allocations[id],
                freedAt: message.time,
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
              physicalMemoryUsage: message.rss
            }
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
      </nav>

      <Visualizer
        allocations={Object.values(allocations)}
        maxTime={maxTime}
        usage={usages}
        availablePhysicalMemory={ADDRESS_MAX / 4}
      />
    </div>
  );
}
