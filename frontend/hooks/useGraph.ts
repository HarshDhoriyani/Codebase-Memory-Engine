"use client";
import { useState, useEffect } from "react";
import { fetchMostCalled, fetchFunctionCalls, fetchFunctionCalledBy, FunctionNode } from "@/lib/api";

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: FunctionNode[];
  edges: GraphEdge[];
}

export function useGraph() {
  const [graphData,  setGraphData]  = useState<GraphData>({ nodes: [], edges: [] });
  const [selected,   setSelected]   = useState<FunctionNode | null>(null);
  const [loading,    setLoading]    = useState(false);

  useEffect(() => {
    loadTopFunctions();
  }, []);

  async function loadTopFunctions() {
    setLoading(true);
    try {
      const data  = await fetchMostCalled(40);
      const nodes = data.functions || [];
      setGraphData({ nodes, edges: [] });
    } catch {}
    setLoading(false);
  }

  async function expandNode(fn: FunctionNode) {
    setSelected(fn);
    try {
      const [callsRes, calledByRes] = await Promise.all([
        fetchFunctionCalls(fn.name),
        fetchFunctionCalledBy(fn.name),
      ]);

      const newEdges: GraphEdge[] = [
        ...(callsRes.calls    || []).map((c: FunctionNode) => ({
          source: fn.name, target: c.name,
        })),
        ...(calledByRes.called_by || []).map((c: FunctionNode) => ({
          source: c.name, target: fn.name,
        })),
      ];

      const newNodes = [
        ...(callsRes.calls    || []),
        ...(calledByRes.called_by || []),
      ];

      setGraphData((prev) => ({
        nodes: [...prev.nodes, ...newNodes.filter(
          (n) => !prev.nodes.find((p) => p.name === n.name)
        )],
        edges: [...prev.edges, ...newEdges],
      }));
    } catch {}
  }

  return { graphData, selected, loading, expandNode, loadTopFunctions };
}