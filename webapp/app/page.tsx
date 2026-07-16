"use client";

import { CopilotChat } from "@copilotkit/react-core/v2";
import { ApprovalPopup } from "@/app/components/ApprovalPopup"

export default function Home() {
  return (
    <>
      <ApprovalPopup />
      <CopilotChat
        labels={{
          modalHeaderTitle: "Deep research assistant",
          welcomeMessageText: "What should we work on?",
        }}
      />
    </>
  );
}
