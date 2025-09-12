import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import getTwilioRouter from './routes/twilio.js';
import clioRoutes from './routes/clio.js';

const app = express();
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: 'http://localhost:5173' } });

app.use('/api/twilio', getTwilioRouter(io));
app.use('/api/clio', clioRoutes);

io.on('connection', socket => {
  console.log('socket connected');
});

const port = process.env.PORT || 3001;
server.listen(port, () => console.log(`Backend listening on ${port}`));
