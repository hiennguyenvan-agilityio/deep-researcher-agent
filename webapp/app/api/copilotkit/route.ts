import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { LangGraphAgent } from "@copilotkit/runtime/langgraph";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphAgent({
      deploymentUrl: "http://localhost:2024",
      graphId: "Deep researcher",
    }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};