function renderHTML(data) {
    const targetHTML = document.querySelector(data.selector);
    if (targetHTML) {
        if (data.append) {
            targetHTML.innerHTML += data.html;
        } else {
            targetHTML.innerHTML = data.html;
        }
    }

    if (data.url) {
        window.history.pushState({ url: data.url }, "", data.url);
    }

    if (data.title) {
        document.title = data.title;
    }
}

export function connect(url = `${'https:' === document.location.protocol ? 'wss' : 'ws'}://${document.body.dataset.host}/ws/liveview/main`) {
    console.log("Connecting to WebSockets server...");
    window.myWebSocket = new WebSocket(url);
    return window.myWebSocket;
}

export function sendData(message, webSocket = window.myWebSocket) {
    if (webSocket.readyState === WebSocket.OPEN) {
        const messageFull = message;
        messageFull.function = messageFull.function || messageFull.action;
        messageFull.data = messageFull.data || {};
        messageFull.data.lang = document.querySelector("html").getAttribute("lang") || "ja";
        webSocket.send(JSON.stringify(messageFull));
    } else {
        console.warn("WebSocket not connected. readyState:", webSocket.readyState);
    }
}

export function startEvents(webSocket = window.myWebSocket) {
    webSocket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        renderHTML(data);
    });

    function reconnect(webSocket = window.myWebSocket) {
        const statusConnection = webSocket.readyState === WebSocket.OPEN;
        if (!statusConnection) {
            webSocket.close();
            console.log("Reconnecting to WebSockets server...");
            setTimeout(() => {
                connect();
                startEvents();
            }, 1000);
        }
        return statusConnection;
    }

    webSocket.addEventListener("open", () => {
        console.log("Connected to WebSockets server");
    });

    webSocket.addEventListener("error", () => {
        console.log("Connection error with WebSockets server");
        reconnect();
    });

    webSocket.addEventListener("close", () => {
        console.log("Connection closed with WebSockets server");
        reconnect();
    });
}
