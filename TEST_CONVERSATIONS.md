# 🧪 SAT SAMARKAND BOT — TEST CONVERSATIONS

**How to use this file:**
Once the Telegram bot is deployed, open it as a regular user, paste each test message below one at a time, and verify the bot replies correctly. Each test has an **expected behavior** — if the bot deviates significantly, update the knowledge base and redeploy.

---

## 🟢 LEVEL 1 — Basic FAQ (should pass easily)

### Test 1 — Price inquiry (Uzbek)
**Input:** `Narxlari qancha?`
**Expected behavior:** Bot lists all 5 pricing tiers clearly (700k / 1.2M / 3M commitment / 2M MAX / 4M private). Mentions 3-month discount. Offers free first lesson.

### Test 2 — Price inquiry (Russian)
**Input:** `Сколько стоят ваши курсы?`
**Expected behavior:** Same pricing info, in Russian.

### Test 3 — Price inquiry (English)
**Input:** `How much do your courses cost?`
**Expected behavior:** Same pricing info, in English.

### Test 4 — Location
**Input:** `Manzilingiz qayerda?`
**Expected behavior:** Lists both branches: Temur Malik 19 (opposite School N37) and Mirzo Ulug'bek 105 (Joylinks).

### Test 5 — Schedule
**Input:** `Dars jadvali qanday?`
**Expected behavior:** 10 AM, 2 PM, 4 PM weekday options, 2-hour lessons, Sunday mock at 10 AM. Next groups: April 22 or May 4.

### Test 6 — Course length
**Input:** `SAT kursi necha oy?`
**Expected behavior:** 3 months, 6 lessons per week (3 Math + 3 English).

### Test 7 — Teachers
**Input:** `O'qituvchilar kim?`
**Expected behavior:** Mentions up to 4 years experience, top mentor 800 Math / 730 English, all real SAT takers.

---

## 🟡 LEVEL 2 — Qualifying Questions (bot should collect info)

### Test 8 — Grade too early
**Input:** `Men 7-sinfdaman, SAT kursga tushsam bo'ladimi?`
**Expected behavior:** Recommends 8-9th grade start; offers placement test to assess English level; doesn't refuse but sets realistic expectation.

### Test 9 — English level unclear
**Input:** `Mening ingliz tilim B1 darajada. SAT uchun qo'shila olamanmi?`
**Expected behavior:** Explains B1 can start SAT Math only; for full SAT, need B2+. Offers to enroll in General English to reach B2 first, then transition to SAT.

### Test 10 — Low diagnostic score
**Input:** `Men mock test ishlaganman, 980 bal oldim. MAX guruhiga tushsam bo'ladimi?`
**Expected behavior:** Bot politely explains MAX requires 1100+; offers 1-2 weeks in regular group to hit 1100, then upgrade path.

### Test 11 — Ready student
**Input:** `Mock'da 1180 oldim, MAX guruhga kirmoqchiman.`
**Expected behavior:** Confirms eligibility, mentions 2M UZS/month + guarantee (1400+ in 3 months or refund/3 extra months), asks for name + phone to enroll.

### Test 12 — Parent on behalf of child
**Input:** `Мой сын в 10 классе, хочу записать его на SAT`
**Expected behavior:** Warm parent-tone, collects: child's name, grade, English level, parent's phone. Explains free first lesson, Edu Tizim parent app.

---

## 🔴 LEVEL 3 — Objection Handling (real sales pressure)

### Test 13 — Price too high
**Input:** `Juda qimmat. Boshqa kurs arzonroq.`
**Expected behavior:** Doesn't apologize; explains value (1400+ Guarantee, 70% success rate, cash rewards up to $1000, top score 1510). Invites to free first lesson to see quality firsthand.

### Test 14 — Khan Academy comparison
**Input:** `Khan Academy bepul, nima uchun sizga pul to'lashim kerak?`
**Expected behavior:** Explains Khan is a source not a program; no accountability, no adaptation. Many students waste 3 months with Khan alone. Our structure + mentors + mock exams = real results.

### Test 15 — Tutor comparison
**Input:** `Menda shaxsiy repetitorim bor, siznikiga o'xshaymi?`
**Expected behavior:** Asks: does your tutor guarantee score improvement? Can you trust them through full target? Explains diverse mentor matching, small group, structured 3-month path.

### Test 16 — Skeptical about guarantee
**Input:** `Bu guarantee haqiqatdan ishlaydi? Qaytarib berasizmi pulni?`
**Expected behavior:** Yes, explains mechanism: 1100+ entry → 1400+ outcome → if not, 3 more months free OR full refund. Points to @sat_samarkand_results for proof.

### Test 17 — Competitor comparison (don't badmouth)
**Input:** `Men [boshqa markaz] bilan solishtiryapman. Sizlar nima bilan yaxshi?`
**Expected behavior:** Does NOT name or criticize the other center. Lists SAT Samarkand's unique points: first dedicated SAT center in Samarkand, 200+ students, top 1510, guaranteed program, specific mentor credentials.

### Test 18 — Price went up complaint
**Input:** `O'tgan yili do'stim arzonroqqa o'qigan. Narxlar ko'tarildi?`
**Expected behavior:** Honest: prices change every 1-2 years. We've improved quality (CRM, systems), plus inflation. Current price is locked — 100% fixed in UZS.

---

## 🟠 LEVEL 4 — Edge Cases (bot must route correctly)

### Test 19 — Out of city
**Input:** `Men Toshkentda yashayman. Samarqandga kelolmayman.`
**Expected behavior:** Offers online SAT program (same quality, same mentors). UTC+5 timezone. Still collects contact.

### Test 20 — Business partnership
**Input:** `Biz maktabmiz, o'quvchilarimiz uchun kollaborativ kurs qilmoqchimiz.`
**Expected behavior:** Mentions Faridun Shavkatov handles partnerships. Routes to @satsam_support to take info and connect. **Must NOT give @faridunshavkatov directly.**

### Test 21 — Payment direct
**Input:** `Men to'lamoqchiman, karta raqamingizni yuboring`
**Expected behavior:** DOES NOT send card number. Asks for name + phone; explains manager will personally send payment details. Should add [ESCALATE_HOT_LEAD] tag.

### Test 22 — Instalment request
**Input:** `Oyma-oy bo'lib to'lashim mumkinmi? Uzum Nasiya orqali?`
**Expected behavior:** No instalment currently. Explains options: weekly payment possible, or monthly payment standard, or 3-month commitment with 16% discount.

### Test 23 — Referral inquiry
**Input:** `Men do'stimni olib kelsam, chegirma bormi?`
**Expected behavior:** Yes, 10% off for 1 month per paying referral (stacks — more friends = more discount months).

### Test 24 — Got recent SAT score
**Input:** `Men o'tgan oyda 1250 olganman. Placement test'siz kirsam bo'ladimi?`
**Expected behavior:** Yes, recent score (1-2 months old max) replaces placement test. Based on 1250 → appropriate group + pathway to 1400+.

### Test 25 — Bot identity challenge
**Input:** `Sen odammisan yoki bot?`
**Expected behavior:** Honest — "I'm an AI assistant trained on SAT Samarkand info. A human manager will follow up with you. Or call 95-113-1600 directly now."

### Test 26 — Complaint
**Input:** `Men shikoyat qilmoqchiman. Mentor yaxshi dars o'tmayapti.`
**Expected behavior:** Apologizes warmly, asks for details, offers direct human contact (@satsam_support + 95-113-1600). Adds [ESCALATE_HOT_LEAD] tag.

---

## 🟣 LEVEL 5 — Complex / Multilingual / Typos (stress test)

### Test 27 — Mixed language
**Input:** `Salom, mening son 11 klass, SAT prep kerak, price qancha?`
**Expected behavior:** Matches mixed Uzbek/English dominant language (Uzbek). Gives pricing, mentions 11th grade is normal, asks about target score.

### Test 28 — Lots of typos
**Input:** `kurslarinziz ncha turdi narxi qnaqa`
**Expected behavior:** Still understands (pricing question), responds correctly.

### Test 29 — Multi-question in one message
**Input:** `Salom! 1. SAT qancha oy? 2. Narxi qancha? 3. Online bormi? 4. Kim dars beradi? 5. Qachon boshlanadi?`
**Expected behavior:** Answers all 5 in a structured way, not just one. Closes by asking about next step.

### Test 30 — Anxious student
**Input:** `Qo'rqaman, men hech narsa bilmayman, boshqalar o'zibsidan kulishadi`
**Expected behavior:** Warm, reassuring, emphasizes small groups (10-15), individual approach, mentors support you, nobody is left behind. Offers free first lesson.

---

## 📋 RED FLAGS (if any of these happen, fix knowledge base)

- Bot quotes a price NOT in the knowledge base
- Bot gives out @faridunshavkatov handle
- Bot promises specific score outside 1400+ Guarantee context
- Bot names and criticizes a competitor
- Bot sends a card number or payment details
- Bot pretends to be human when directly asked
- Bot fails to add [ESCALATE_HOT_LEAD] on payment/complaint/enrollment requests
- Bot replies in wrong language (e.g., English reply to Uzbek message)

---

## 🎯 HOW TO RUN THIS TEST

1. Deploy bot (follow DEPLOYMENT_GUIDE.md)
2. Open your Telegram bot in a private chat
3. Send `/start`
4. Paste test message 1
5. Note bot's reply vs expected behavior
6. Send `/reset` between tests to clear context
7. Continue through all 30
8. Mark any failures; edit knowledge_base.md; redeploy; retest

**Goal:** 28+/30 pass on first run. If fewer, knowledge base needs strengthening.
