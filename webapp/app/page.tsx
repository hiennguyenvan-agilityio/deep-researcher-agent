"use client";

import { AgentSubscriber, CopilotChat, useAgent } from "@copilotkit/react-core/v2";
import { useEffect } from "react";

export default function Home() {

  const { agent } = useAgent();
  
  useEffect(() => {
    const subscriber: AgentSubscriber = {
      onCustomEvent: ({ event }) => {
        console.log("Custom event:", event.name, event.value);
      },
      onRunStartedEvent: () => {
        console.log("Agent started running");
      },
      onRunFinalized: () => {
        console.log("Agent finished running");
      },
      onStateChanged: (state) => {
        console.log("State changed:", state);
      },
    };
    const { unsubscribe } = agent.subscribe(subscriber);
    return () => unsubscribe();
  }, [agent]);
  
  return (
    <CopilotChat
      labels={{
        modalHeaderTitle: "Deep research assistant",
        welcomeMessageText: "What should we work on?",
      }}
    />
  );
}
