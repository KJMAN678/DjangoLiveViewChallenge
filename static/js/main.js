import { connect, startEvents, sendData } from './websocket.js';

window.sendData = sendData;

const ws = connect();
startEvents(ws);
