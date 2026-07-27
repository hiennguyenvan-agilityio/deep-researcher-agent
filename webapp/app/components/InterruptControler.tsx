import { useInterrupt } from "@copilotkit/react-core/v2";
import { Feedback } from "./Feedback";
import { ApprovalPopup } from "./ApprovalPopup";

const InterruptControler = () => {
  useInterrupt({
    render: ({ event, resolve, cancel }) => {
      let interrupt_message = event.value
      let interrupt_type
      try {
        const interrupt_data = JSON.parse(event.value)

        interrupt_message = interrupt_data.message
        interrupt_type = interrupt_data.type
      } catch { }

      if (interrupt_type === 'feedback') {
        return (
          <Feedback
            message={interrupt_message}
            onSubmit={() => resolve(false)}
            onRevision={(feedback: string) => {
              resolve(feedback)
            }}
          />
        )
      }


      return (
        <ApprovalPopup
          message={interrupt_message}
          onSubmit={() => resolve({ action: "approve" })}
          onCancel={cancel}
        />
      )
    },
  });

  return null;
}

export { InterruptControler }