"use client";

import React, { useMemo, useCallback } from "react";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { AgentEvent, FlowNode, FlowEdge } from "@/lib/types";

// Custom node types
const AgentNode = ({ data }: { data: any }) => {
  const {
    label,
    stage,
    status,
    event,
    isSelected,
    isCurrentEvent,
    isReplayedEvent,
    isPlaying,
    onClick,
  } = data;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "running":
        return "bg-blue-500";
      default:
        return "bg-gray-400";
    }
  };

  const getEventTypeIcon = (event: AgentEvent) => {
    return event.type === "status" ? "●" : "◆";
  };

  // Determine node styling based on replay state
  const getNodeStyling = () => {
    if (isCurrentEvent && isPlaying) {
      return "border-yellow-500 ring-2 ring-yellow-200 bg-yellow-50 animate-pulse";
    }
    if (isCurrentEvent) {
      return "border-yellow-500 ring-2 ring-yellow-200 bg-yellow-50";
    }
    if (isSelected) {
      return "border-blue-500 ring-2 ring-blue-200 bg-blue-50";
    }
    if (isReplayedEvent) {
      return "border-green-300 bg-green-50";
    }
    return "border-gray-300 bg-white opacity-60";
  };

  return (
    <>
      <Handle type="target" position={Position.Left} />
      <div
        className={`px-3 py-2 shadow-md rounded-md border-2 cursor-pointer transition-all hover:shadow-lg ${getNodeStyling()}`}
        onClick={() => onClick?.(event)}
      >
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`} />
          <div className="text-xs font-medium text-gray-900">
            {getEventTypeIcon(event)} {label}
          </div>
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {new Date(event.ts * 1000).toLocaleTimeString()}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </>
  );
};

const StageNode = ({ data }: { data: any }) => {
  const { label, status, eventCount } = data;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 border-green-500 text-green-800";
      case "failed":
        return "bg-red-100 border-red-500 text-red-800";
      case "running":
        return "bg-blue-100 border-blue-500 text-blue-800";
      default:
        return "bg-gray-100 border-gray-400 text-gray-600";
    }
  };

  return (
    <>
      <Handle type="target" position={Position.Left} />
      <div
        className={`px-4 py-3 rounded-lg border-2 ${getStatusColor(
          status
        )} font-semibold text-center min-w-[120px]`}
      >
        <div className="text-sm">{label}</div>
        <div className="text-xs mt-1 opacity-75">{eventCount} events</div>
      </div>
      <Handle type="source" position={Position.Right} />
    </>
  );
};

const nodeTypes = {
  agent: AgentNode,
  stage: StageNode,
};

interface ReactFlowTimelineProps {
  events: AgentEvent[];
  onEventSelect?: (event: AgentEvent) => void;
  selectedEvent?: AgentEvent | null;
  currentEventIndex?: number;
  isPlaying?: boolean;
}

export default function ReactFlowTimeline({
  events,
  onEventSelect,
  selectedEvent,
  currentEventIndex = -1,
  isPlaying = false,
}: ReactFlowTimelineProps) {
  // Convert events to React Flow nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const stages = [
      "clone",
      "architect",
      "deps",
      "tests",
      "deployment",
      "incident_monitor",
      "final",
    ];
    const stageLabels = {
      clone: "Clone",
      architect: "Architect",
      deps: "Dependencies",
      tests: "Tests",
      deployment: "Deployment",
      incident_monitor: "Monitor",
      final: "Final",
    };

    const nodes: Node[] = [];
    const edges: Edge[] = [];

    let yOffset = 0;
    const stageHeight = 150;
    const eventSpacing = 180;

    stages.forEach((stage, stageIndex) => {
      const stageEvents = events.filter((e) => e.stage === stage);

      if (stageEvents.length === 0) return;

      // Determine stage status
      const hasError = stageEvents.some((e) => "error" in e);
      const finalEvent = events.find((e) => e.stage === "final");
      const isFinalStage = stage === "final";

      let stageStatus = "pending";
      if (isFinalStage && finalEvent) {
        stageStatus =
          (finalEvent as any).status === "failed" ? "failed" : "completed";
      } else if (hasError) {
        stageStatus = "failed";
      } else if (stageEvents.length > 0) {
        stageStatus = "completed";
      }

      // Add stage header node
      nodes.push({
        id: `stage-${stage}`,
        type: "stage",
        position: { x: 50, y: yOffset },
        data: {
          label: stageLabels[stage as keyof typeof stageLabels] || stage,
          status: stageStatus,
          eventCount: stageEvents.length,
        },
        draggable: false,
      });

      // Add event nodes for this stage
      stageEvents.forEach((event, eventIndex) => {
        const eventId = `event-${stage}-${eventIndex}`;

        // Determine event label
        let label = "";
        if (event.type === "status" && "message" in event) {
          label =
            event.message.substring(0, 30) +
            (event.message.length > 30 ? "..." : "");
        } else if (event.type === "trace" && event.subtype) {
          label = event.subtype;
        } else {
          label = event.type;
        }

        // Determine if this event is current in replay
        const eventGlobalIndex = events.indexOf(event);
        const isCurrentEvent = currentEventIndex === eventGlobalIndex;
        const isReplayedEvent = currentEventIndex >= eventGlobalIndex;

        nodes.push({
          id: eventId,
          type: "agent",
          position: {
            x: 250 + eventIndex * eventSpacing,
            y: yOffset + 20,
          },
          data: {
            label,
            stage,
            status: hasError ? "failed" : "completed",
            event,
            isSelected: selectedEvent === event,
            isCurrentEvent,
            isReplayedEvent,
            isPlaying,
            onClick: onEventSelect,
          },
          draggable: false,
        });

        // Connect stage to first event
        if (eventIndex === 0) {
          edges.push({
            id: `stage-to-${eventId}`,
            source: `stage-${stage}`,
            target: eventId,
            type: "smoothstep",
            animated: false,
          });
        }

        // Connect events within the same stage
        if (eventIndex > 0) {
          const prevEventId = `event-${stage}-${eventIndex - 1}`;
          edges.push({
            id: `${prevEventId}-to-${eventId}`,
            source: prevEventId,
            target: eventId,
            type: "smoothstep",
            animated: false,
          });
        }
      });

      // Connect to next stage
      if (stageIndex < stages.length - 1) {
        const nextStage = stages[stageIndex + 1];
        const nextStageEvents = events.filter((e) => e.stage === nextStage);

        if (nextStageEvents.length > 0 && stageEvents.length > 0) {
          const lastEventId = `event-${stage}-${stageEvents.length - 1}`;
          const nextStageId = `stage-${nextStage}`;

          edges.push({
            id: `${lastEventId}-to-${nextStageId}`,
            source: lastEventId,
            target: nextStageId,
            type: "smoothstep",
            animated: true,
            style: { stroke: "#6366f1", strokeWidth: 2 },
          });
        }
      }

      yOffset += stageHeight;
    });

    return { nodes, edges };
  }, [events, selectedEvent, currentEventIndex, isPlaying, onEventSelect]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when selectedEvent changes
  React.useEffect(() => {
    setNodes((currentNodes) =>
      currentNodes.map((node) => {
        if (node.type === "agent") {
          return {
            ...node,
            data: {
              ...node.data,
              isSelected: selectedEvent === node.data.event,
            },
          };
        }
        return node;
      })
    );
  }, [selectedEvent, setNodes]);

  const onConnect = useCallback(() => {
    // Disable manual connections
  }, []);

  if (events.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center text-gray-500">
        <p>No events to display</p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-700px)] w-full border border-gray-200 rounded-lg overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{ padding: 0.1 }}
        attributionPosition="bottom-left"
      >
        <Background color="#f1f5f9" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
