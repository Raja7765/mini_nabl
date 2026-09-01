const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const chatMessages = document.getElementById("chatMessages");


// ==========================================
// SESSION ID
// ==========================================

const sessionId = "session1";


// ==========================================
// ADD MESSAGE
// ==========================================

function addMessage(sender, text = "") {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add(
        "message",
        sender
    );

    const labelDiv = document.createElement("div");

    labelDiv.classList.add("message-label");

    labelDiv.textContent =
        sender === "user"
            ? "You"
            : "Assistant";


    const contentDiv = document.createElement("div");

    contentDiv.classList.add(
        "message-content"
    );

    contentDiv.textContent = text;


    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);

    chatMessages.scrollTop =
        chatMessages.scrollHeight;


    return contentDiv;
}


// ==========================================
// SEND MESSAGE
// ==========================================

async function sendMessage() {

    const question =
        questionInput.value.trim();

    if (!question) {
        return;
    }


    // Disable button while processing
    sendBtn.disabled = true;

    questionInput.disabled = true;


    // Add user message
    addMessage(
        "user",
        question
    );


    // Clear input
    questionInput.value = "";


    // Create empty assistant message
    const assistantContent =
        addMessage(
            "assistant",
            ""
        );


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/chat/stream",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    session_id: sessionId,
                    question: question
                })
            }
        );


        if (!response.ok) {

            throw new Error(
                `HTTP error: ${response.status}`
            );

        }


        // ==========================================
        // READ STREAM
        // ==========================================

        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder();


        let buffer = "";


        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done) {
                break;
            }


            buffer +=
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            // SSE messages are separated by \n\n
            const messages =
                buffer.split("\n\n");


            // Keep incomplete message
            buffer =
                messages.pop();


            for (const message of messages) {

                if (!message.startsWith("data:")) {
                    continue;
                }


                const data =
                    message
                        .replace(/^data:\s?/, "")
                        .trim();


                // Stream completed
                if (data === "[DONE]") {
                    continue;
                }


                // Add streamed text
                assistantContent.textContent +=
                    data;


                chatMessages.scrollTop =
                    chatMessages.scrollHeight;
            }
        }


    } catch (error) {

        console.error(
            "Chat error:",
            error
        );


        assistantContent.textContent =
            "Sorry, something went wrong while connecting to the server.";

    }


    // Enable again
    sendBtn.disabled = false;

    questionInput.disabled = false;

    questionInput.focus();
}


// ==========================================
// SEND BUTTON
// ==========================================

sendBtn.addEventListener(
    "click",
    sendMessage
);


// ==========================================
// ENTER KEY
// ==========================================

questionInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            sendMessage();

        }

    }
);


// ==========================================
// CLEAR CHAT
// ==========================================

clearBtn.addEventListener(
    "click",
    function () {

        chatMessages.innerHTML = "";

        addMessage(
            "assistant",
            "Hello! Ask me anything about NABL documents."
        );

    }
);