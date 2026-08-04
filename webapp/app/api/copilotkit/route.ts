import { CopilotRuntime, createCopilotRuntimeHandler } from "@copilotkit/runtime/v2";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url:  process.env.DEEP_RESERACH_AGENT_URL || "http://localhost:8000/copilotkit/agent/deep_researcher",
    }),
  }
});

const handler = createCopilotRuntimeHandler({ runtime, basePath: "/api/copilotkit", mode: "single-route" });

export const POST = handler