import { queryOptions } from "@tanstack/react-query";
import { quantumShieldService as svc } from "./quantumshield.service";

export const overviewQuery = queryOptions({ queryKey: ["overview"], queryFn: svc.getOverview });
export const threatsQuery = queryOptions({ queryKey: ["threats"], queryFn: svc.getThreats });
export const cryptoQuery = queryOptions({ queryKey: ["crypto"], queryFn: svc.getCrypto });
export const healingQuery = queryOptions({ queryKey: ["healing"], queryFn: svc.getHealing });
export const topologyQuery = queryOptions({ queryKey: ["topology"], queryFn: svc.getTopology });
export const pipelineQuery = queryOptions({ queryKey: ["pipeline"], queryFn: svc.getPipeline });
export const logsQuery = queryOptions({ queryKey: ["logs"], queryFn: svc.getLogs });
