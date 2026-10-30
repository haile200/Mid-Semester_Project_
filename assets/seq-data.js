// Hand-written sequence diagrams. Each step: from, to, label (short, on the arrow),
// text (shown under the diagram, may contain <code>), and ret: true for a response arrow.
window.SEQ_DATA = {
  login: {
    title: 'התחברות (Login)',
    actors: ['Login.jsx', 'api.js', 'nginx', 'routes/auth.py', 'services.py', 'MySQL'],
    steps: [
      { from: 0, to: 1, label: 'login(email, password)', text: 'המשתמש לוחץ Login. <code>Login.jsx</code> קורא ל-<code>login()</code> ב-<code>src/api.js</code>.' },
      { from: 1, to: 2, label: 'POST /api/login', text: '<code>fetch</code> שולח JSON עם המייל והסיסמה לכתובת היחסית <code>/api/login</code>.' },
      { from: 2, to: 3, label: 'proxy_pass backend:5000', text: 'nginx רואה שהכתובת מתחילה ב-<code>/api/</code> ומעביר אותה ל-gunicorn בקונטיינר <code>backend</code>.' },
      { from: 3, to: 4, label: 'authenticate()', text: 'הראוט <code>login()</code> קורא ל-<code>services.authenticate(email, password)</code>.' },
      { from: 4, to: 5, label: 'SELECT user by email', text: 'שולפים את המשתמש ואת ה-hash של הסיסמה, ובודקים עם <code>bcrypt</code>. משתמש חסום מקבל 403, אבל רק אחרי סיסמה נכונה.' },
      { from: 4, to: 5, label: 'INSERT INTO sessions', text: '<code>create_session()</code> יוצר טוקן אקראי עם <code>secrets.token_urlsafe(32)</code> ושומר אותו בטבלה <code>sessions</code>.' },
      { from: 3, to: 1, label: '200 + Set-Cookie session_token', ret: true, text: 'התשובה מחזירה את פרטי המשתמש וקובעת cookie מסוג <code>HttpOnly</code> עם <code>SameSite=Lax</code>. JavaScript לא יכול לקרוא אותו.' },
      { from: 1, to: 0, label: 'user', ret: true, text: '<code>App.handleLogin</code> שומר את המשתמש ב-<code>localStorage</code> ומעדכן את <code>currentUser</code>, והסרגל העליון מצויר מחדש.' }
    ]
  },

  post: {
    title: 'פרסום פוסט עם בדיקת רעילות',
    actors: ['NewPost.jsx', 'nginx', 'routes/posts.py', 'services.py', 'brain', 'Gemini', 'MySQL'],
    steps: [
      { from: 0, to: 1, label: 'POST /api/posts', text: '<code>handleSubmit</code> ב-<code>NewPost.jsx</code> קורא ל-<code>createPost(title, withNormalSpaces(body), ...)</code>. הכפתור מראה Posting...' },
      { from: 1, to: 2, label: 'proxy + cookie', text: 'nginx מעביר את הבקשה. ה-cookie <code>session_token</code> מצורף אוטומטית, כי זה אותו דומיין.' },
      { from: 2, to: 6, label: '@login_required: sessions lookup', text: '<code>login_required</code> קורא ל-<code>get_user_by_session(token)</code>: טוקן לא קיים או משתמש חסום מחזירים 401. הכותב נלקח מ-<code>g.user_id</code>, לא מהגוף.' },
      { from: 2, to: 3, label: 'create_post(g.user_id, ...)', text: '<code>services.create_post</code> מנקה את ה-HTML (<code>sanitize_post_html</code>) ובודק שיש כותרת וגוף.' },
      { from: 3, to: 4, label: 'check_toxicity(text)', text: '<code>_ensure_publishable</code> קורא ל-<code>get_brain().check_toxicity</code>. לאנשים זה <code>FallbackBrain</code>: קודם Gemini, ואם נכשל, המוח ה-offline.' },
      { from: 4, to: 5, label: 'generate_content (timeout 15s)', text: 'הטקסט נשלח בתוך תגיות, כמידע בלבד. התשובה חייבת להיות JSON עם <code>allowed</code> בוליאני, אחרת זו שגיאה ועוברים לגיבוי.' },
      { from: 5, to: 4, label: '{"allowed": true}', ret: true, text: 'אם הטקסט פוגעני, נזרק <code>ContentRejected</code> וחוזר 400 עם הסיבה, וה-draft נשאר במסך.' },
      { from: 3, to: 6, label: 'INSERT INTO posts', text: 'הפוסט נשמר עם <code>author_id</code> של המשתמש המחובר.' },
      { from: 2, to: 0, label: '201 {postId}', ret: true, text: 'חוזר 201, ו-<code>NewPost</code> עושה <code>navigate(\'/\')</code>. הפיד נטען מחדש.' }
    ]
  },

  like: {
    title: 'לייק',
    actors: ['LikeButton.jsx', 'api.js', 'routes/posts.py', 'services.py', 'MySQL'],
    steps: [
      { from: 0, to: 1, label: 'likePost(postId)', text: 'לחיצה על הלב. <code>likePost</code> הוא שורה אחת: <code>sendJson(\'PUT\', `/posts/${postId}/like`)</code>.' },
      { from: 1, to: 2, label: 'PUT /api/posts/17/like', text: 'אותה כתובת משמשת לשתי הפעולות: PUT לייק, DELETE ביטול. זה REST: הכתובת היא הדבר, השיטה היא הפעולה.' },
      { from: 2, to: 3, label: 'like_post(user, post)', text: 'הראוט <code>like(post_id)</code> מוגן ב-<code>@login_required</code>, וקורא ל-<code>services.like_post</code>.' },
      { from: 3, to: 4, label: 'INSERT likes (PK user_id, post_id)', text: 'המפתח הראשי של <code>likes</code> הוא הזוג (user_id, post_id), כך שאי אפשר לעשות לייק כפול לאותו פוסט.' },
      { from: 2, to: 0, label: '{likeCount, liked}', ret: true, text: 'חוזר המונה העדכני, והכפתור מתעדכן.' }
    ]
  },

  bot: {
    title: 'סיבוב של בוט (worker)',
    actors: ['bots/worker.py', 'services.py', 'MySQL', 'brain (no fallback)', 'Gemini'],
    steps: [
      { from: 0, to: 1, label: 'list_bot_activity(since 24h)', text: '<code>run_tick</code> טוען את כל הבוטים: מתי כל אחד פעל לאחרונה, וכמה פעמים ב-24 השעות האחרונות.' },
      { from: 1, to: 2, label: 'SELECT ... is_bot = 1', text: 'השעה נלקחת מהמסד (<code>database_now</code>), לא מהשעון של המחשב.' },
      { from: 0, to: 0, label: 'choose_bot + choose_action', text: '<code>skip_reason</code> פוסל בוט שנח (cooldown של 600 שניות) או הגיע ל-12 פעולות. <code>choose_bot</code> בוחר אקראית מבין 3 שנחו הכי הרבה, ו-<code>choose_action</code> בוחר post 20%, comment 35%, reply 25% או like 20%.' },
      { from: 0, to: 1, label: 'list_comment_targets(bot, 20)', text: 'לתגובה: 20 הפוסטים האחרונים שהבוט עוד לא הגיב עליהם. <code>order_targets</code> מעדיף חדשים, ופוסטים של אנשים מקבלים משקל פי 5 (<code>HUMAN_WEIGHT</code>).' },
      { from: 0, to: 3, label: 'write_reply(personality, post)', text: 'המוח של ה-worker נוצר עם <code>get_brain(fallback=False)</code>: אם Gemini נכשל, הבוט מדלג במקום לפרסם טקסט מתבנית.' },
      { from: 3, to: 4, label: 'generate_content', text: 'עלול להחזיר 503 (עומס) או 504. במקרה כזה נזרק <code>BrainUnavailable</code>, ונרשמת ביומן שורת skipped עם הסיבה.' },
      { from: 0, to: 1, label: 'create_comment(..., strict=True)', text: '<code>strict=True</code>: אם בדיקת הרעילות עצמה לא רצה, נזרק <code>ModerationUnavailable</code> ולא מפרסמים.' },
      { from: 1, to: 2, label: 'INSERT INTO comments', text: 'אותו <code>services.py</code> שה-API משתמש בו: הבוטים כפופים לאותם כללים כמו אנשים.' },
      { from: 0, to: 0, label: 'sleep 300-900s', text: 'שורת לוג אחת לכל סיבוב, ואז שינה של 5 עד 15 דקות. שגיאה בסיבוב נרשמת, והלולאה ממשיכה.' }
    ]
  },

  reset: {
    title: 'איפוס סיסמה במייל',
    actors: ['ForgotPassword.jsx', 'routes/auth.py', 'services.py', 'MySQL', 'Gmail', 'ResetPassword.jsx'],
    steps: [
      { from: 0, to: 1, label: 'POST /api/password-resets', text: 'המשתמש מקליד מייל. <code>reset_limiter</code> מתיר 3 בקשות לכל כתובת ב-15 דקות.' },
      { from: 1, to: 2, label: 'create_password_reset(email)', text: 'טוקן אקראי נוצר. במסד נשמר רק ה-SHA-256 שלו (<code>_reset_token_hash</code>), וקישורים ישנים נמחקים.' },
      { from: 2, to: 3, label: 'INSERT password_resets', text: 'בוטים ומשתמשים חסומים לא מקבלים קישור.' },
      { from: 1, to: 4, label: 'send_in_background', text: '<code>mailer.send_in_background</code> שולח ב-thread נפרד, כך שהתשובה מגיעה מיד ובאותו זמן, בין אם החשבון קיים ובין אם לא.' },
      { from: 1, to: 0, label: '200 same message', ret: true, text: 'אותה הודעה לכל מייל: "If that email has an account..." כך אי אפשר לגלות אילו חשבונות קיימים.' },
      { from: 4, to: 5, label: 'link .../reset-password#token=', text: 'הטוקן נמצא אחרי <code>#</code>, ולכן לא נשלח לשרת ולא נשמר ביומנים. הדף מוחק אותו משורת הכתובת מיד.' },
      { from: 5, to: 1, label: 'POST /api/password-resets/confirm', text: 'קודם בודקים את אורך הסיסמה (8 עד 72), כדי שטעות הקלדה לא תשרוף את הקישור החד-פעמי.' },
      { from: 1, to: 2, label: 'reset_password(token, pw)', text: 'מאתרים לפי ה-hash, בודקים שעברו פחות מ-30 דקות (<code>RESET_LINK_MINUTES</code>), מוחקים את הקישור, שומרים bcrypt חדש, ו<b>מוחקים את כל ה-sessions</b>.' },
      { from: 1, to: 5, label: '200', ret: true, text: '"logged out everywhere": כל המכשירים מנותקים. <code>forgetUser</code> מנקה את המשתמש מהדפדפן.' }
    ]
  }
};
