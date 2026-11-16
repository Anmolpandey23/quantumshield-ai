import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Layers, MousePointerClick, Share2 } from "lucide-react";
import { useMemo, useState } from "react";
import { DemoBadge } from "@/components/hud/DemoBadge";
import { GlassPanel } from "@/components/hud/GlassPanel";
import { loadTone, Meter } from "@/components/hud/Meter";
import { nodeStatusTone, StatusBadge } from "@/components/hud/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { NetworkGraph, NetworkLegend, statusColor } from "@/components/network/NetworkGraph";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { topologyQuery } from "@/services/queries";
import type { NodeLayer } from "@/types/quantumshield";

export const Route = createFileRoute("/topology")({
  head: () => ({
    meta: [
      { title: "Network Topology — QuantumShield AI" },
      { name: "description", content: "Interactive map of monitored nodes, links and their health (demo data)." },
      { property: "og:title", content: "Network Topology — QuantumShield AI" },
      { property: "og:description", content: "Interactive network topology with node health." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(topologyQuery),
  component: TopologyPage,
});

const LAYERS: NodeLayer[] = ["edge", "core", "service", "endpoint"];

function TopologyPage() {
  const { data } = useSuspenseQuery(topologyQuery);
  const [layers, setLayers] = useState<NodeLayer[]>(LAYERS);
  const [selectedId, setSelectedId] = useState<string | null>(
    (data.nodes.find((n) => n.status === "compromised") ?? data.nodes.find((n) => n.status === "isolated"))?.id ?? null,
  );
  // Look the node up by id on every render so its status follows live updates.
  const selected = data.nodes.find((n) => n.id === selectedId) ?? null;

  const dimmed = useMemo(
    () => new Set(data.nodes.filter((n) => !layers.includes(n.layer)).map((n) => n.id)),
    [data.nodes, layers],
  );
  const links = selected ? data.edges.filter((e) => e.from === selected.id || e.to === selected.id) : [];
  const counts = data.nodes.reduce<Record<string, number>>((acc, n) => ({ ...acc, [n.status]: (acc[n.status] ?? 0) + 1 }), {});

  return (
    <>
      <PageHeader
        eyebrow="Module 05"
        title="Network Topology"
        description="Click any node to inspect it. Filter by layer to focus the map."
        actions={
          <ToggleGroup type="multiple" value={layers} onValueChange={(v) => setLayers(v as NodeLayer[])}>
            {LAYERS.map((l) => (
              <ToggleGroupItem key={l} value={l} size="sm" className="font-mono text-[10px] uppercase data-[state=on]:bg-primary/15 data-[state=on]:text-primary">
                {l}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <GlassPanel title="Topology Map" subtitle={`${data.nodes.length} nodes · ${data.edges.length} links`} icon={<Share2 />} actions={<DemoBadge />}>
          <div className="aspect-[5/3] rounded-lg border border-border bg-background/40">
            <NetworkGraph topology={data} selectedId={selected?.id} onSelect={(n) => setSelectedId(n.id)} dimmedIds={dimmed} />
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <NetworkLegend />
            <div className="flex flex-wrap gap-2">
              {Object.entries(counts).map(([s, c]) => (
                <StatusBadge key={s} tone={nodeStatusTone[s]}>{c} {s}</StatusBadge>
              ))}
            </div>
          </div>
        </GlassPanel>

        <div className="space-y-6">
          <GlassPanel title="Node Inspector" icon={<MousePointerClick />}>
            <AnimatePresence mode="wait">
              {selected ? (
                <motion.div key={selected.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{selected.type} · {selected.layer}</p>
                      <h3 className="mt-1 text-lg font-semibold text-foreground">{selected.label}</h3>
                    </div>
                    <StatusBadge tone={nodeStatusTone[selected.status]} pulse>{selected.status}</StatusBadge>
                  </div>
                  <dl className="mt-4 space-y-2 text-xs">
                    <Item k="Node ID" v={selected.id} />
                    <Item k="Address" v={selected.ip} />
                    <Item k="Links" v={String(links.length)} />
                  </dl>
                  <div className="mt-4">
                    <div className="mb-1.5 flex justify-between text-xs">
                      <span className="text-muted-foreground">Load</span>
                      <span className="font-mono text-foreground">{selected.load}%</span>
                    </div>
                    <Meter value={selected.load} tone={loadTone(selected.load)} />
                  </div>
                  <div className="mt-4 space-y-1.5">
                    {links.map((l) => {
                      const peer = l.from === selected.id ? l.to : l.from;
                      return (
                        <div key={`${l.from}-${l.to}`} className="flex items-center justify-between rounded border border-border bg-surface/50 px-2.5 py-1.5 font-mono text-[11px]">
                          <span className="text-foreground">↔ {peer}</span>
                          <span className="uppercase text-muted-foreground">{l.status ?? "normal"}</span>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              ) : (
                <p className="text-sm text-muted-foreground">Select a node on the map.</p>
              )}
            </AnimatePresence>
          </GlassPanel>

          <GlassPanel title="All Nodes" icon={<Layers />} bodyClassName="p-2 max-h-80 overflow-auto scrollbar-thin">
            {data.nodes.map((n) => (
              <button
                key={n.id}
                onClick={() => setSelectedId(n.id)}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-primary/5 data-[active=true]:bg-primary/10"
                data-active={selected?.id === n.id}
              >
                <span className="size-2 rounded-full" style={{ background: statusColor[n.status] }} />
                <span className="flex-1 truncate text-foreground">{n.label}</span>
                <span className="font-mono text-[11px] text-muted-foreground">{n.load}%</span>
              </button>
            ))}
          </GlassPanel>
        </div>
      </div>
    </>
  );
}

function Item({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between rounded border border-border bg-surface/50 px-2.5 py-1.5">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="font-mono text-foreground">{v}</dd>
    </div>
  );
}
