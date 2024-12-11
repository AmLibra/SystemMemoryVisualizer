import { useEffect } from "react";
import Visualizer, { PAGE_NUMBER_MAX } from "./Visualizer";

export default function App() {

  useEffect(() => {
    const socket = new WebSocket("ws://172.16.106.136:8000");

    socket.onmessage = (event) => {
      alert(event.data);
    };

    return () => {
      socket.close();
    };
  }, []);
  return (
    <div className="app">
      <nav className="nav">
        <h1>Memory Allocation Visualizer</h1>
      </nav>

      <Visualizer
        allocations={[
          {
            startAddress: 0,
            size: 1,
            allocatedAt: 0,
            freedAt: null,
          },
          {
            startAddress: PAGE_NUMBER_MAX / 10,
            size: (PAGE_NUMBER_MAX * 0.5) / 10,
            allocatedAt: 0,
            freedAt: 25,
          },
          {
            startAddress: PAGE_NUMBER_MAX / 10,
            size: PAGE_NUMBER_MAX / 10,
            allocatedAt: 25,
            freedAt: null,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 5,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 0,
            freedAt: 10,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 6,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 0,
            freedAt: 20,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 7,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 0,
            freedAt: 30,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 8,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 8,
            freedAt: 40,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 9,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 10,
            freedAt: 45,
          },
          {
            startAddress: (PAGE_NUMBER_MAX / 10) * 9 + PAGE_NUMBER_MAX / 100,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 13,
            freedAt: 48,
          },
          {
            startAddress:
              (PAGE_NUMBER_MAX / 10) * 9 + (PAGE_NUMBER_MAX / 100) * 2,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 27,
            freedAt: 49,
          },
          {
            startAddress:
              (PAGE_NUMBER_MAX / 10) * 9 + (PAGE_NUMBER_MAX / 100) * 3,
            size: PAGE_NUMBER_MAX / 100,
            allocatedAt: 29,
            freedAt: 49.5,
          },
        ]}
        maxTime={50}
        usage={[
          {
            time: 0,
            virtualMemoryUsage: PAGE_NUMBER_MAX / 5,
            physicalMemoryUsage: 0,
          },
          {
            time: 10,
            virtualMemoryUsage: PAGE_NUMBER_MAX / 10,
            physicalMemoryUsage: PAGE_NUMBER_MAX / 10,
          },
          {
            time: 25,
            virtualMemoryUsage: (PAGE_NUMBER_MAX * 2) / 10,
            physicalMemoryUsage: PAGE_NUMBER_MAX / 10,
          },
          {
            time: 40,
            virtualMemoryUsage: PAGE_NUMBER_MAX / 2,
            physicalMemoryUsage: 0,
          },
          {
            time: 50,
            virtualMemoryUsage: PAGE_NUMBER_MAX / 3,
            physicalMemoryUsage: PAGE_NUMBER_MAX / 4,
          },
        ]}
        availablePhysicalMemory={PAGE_NUMBER_MAX / 4}
      />
    </div>
  );
}
