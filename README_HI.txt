TELEGRAM HISTORY BOT — READY-TO-DEPLOY ZIP

ZIP mein code aur Render configuration taiyar hai. Python code edit karne ki zaroorat nahi.

DEPLOY:
1. ZIP extract karke saari files GitHub repository ke root mein upload karein.
2. Render Dashboard > New > Blueprint select karein aur repository connect karein.
3. Render render.yaml padhega aur worker + 1 GB persistent disk configure karega.
4. Render Environment mein BOT_TOKEN add karein. Value BotFather se mila token ho.
5. Deploy karein. Logs mein "Telegram History Bot starting" check karein.
6. Telegram mein bot ko /start bhejein.

COMMANDS:
 /start
 /help
 /history 20
 /count
 /export

IMPORTANT:
- Token ZIP/GitHub code mein nahi hai; ise Render ke Environment Variables mein add karna hoga.
- Persistent disk configuration Render plan/availability ke hisaab se paid ho sakti hai.
- Persistent disk par SQLite history restart/deploy ke baad bani reh sakti hai. Backup phir bhi rakhein.
- History unlimited nahi hai; storage disk ki capacity aur Telegram/API limits par depend karti hai.
- Bot sirf un messages ko save kar sakta hai jo Telegram us tak pahunchata hai. Purani chats automatically import nahi hoti.
- Bot ko Telegram par /start bhejein. Bot ke DM mein bheje gaye text save honge; groups ke liye bot permissions/privacy mode sahi honi chahiye.
- Render ka Stop/Resume Dashboard se manually kar sakte hain. Free plan ya service availability par 24/7 guarantee nahi.
- Agar pehle token public chat ya code mein share kiya tha, BotFather se /revoke karke naya token banayein.
