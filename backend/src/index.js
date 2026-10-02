import 'dotenv/config';
import createApp from "./server.js";

const PORT = process.env.PORT || 3000;
const app = createApp();

app.listen(PORT, "0.0.0.0", () => {
    console.log(`✅ Server running on port ${PORT}`);
});
