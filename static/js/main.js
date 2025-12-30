import { connect, startEvents, sendData } from './websocket.js';

window.sendData = sendData;

connect();
startEvents();
